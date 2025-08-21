from flask import Blueprint, request, jsonify
import sqlite3
import os
import openai
import difflib
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# --- 설정 및 상수 ---
keywords_bp = Blueprint('keywords', __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '../database/db.sqlite')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# OpenAI 클라이언트 초기화 (API 키 필수)
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 API 키를 설정해주세요.")

try:
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    # API 키 유효성 간단 테스트
    print("✅ OpenAI API 클라이언트가 정상적으로 초기화되었습니다.")
except Exception as e:
    raise ValueError(f"❌ OpenAI API 클라이언트 초기화 실패: {e}")
OWN_BRANDS = [
    "디스커버리 익스페디션", "MLB", "세르지오 타키니", "수프라", "듀베티카", "디스커버리 키즈", "MLB키즈",
    "바닐라코", "banilaco", "AHOF", "UNIS", "그룹 아홉", "그룹 유니스"
]

# --- DB 유틸 함수 ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- 유틸 함수 ---
def find_similar_group_name(keyword):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT keyword, group_name FROM keywords WHERE is_active=1")
    rows = cursor.fetchall()
    conn.close()
    def normalize(s):
        return s.replace(" ", "").lower()
    keywords = [row['keyword'] for row in rows]
    group_names = [row['group_name'] for row in rows]
    norm_keyword = normalize(keyword)
    for i, k in enumerate(keywords):
        if normalize(k) in norm_keyword or norm_keyword in normalize(k):
            return group_names[i]
    norm_keywords = [normalize(k) for k in keywords]
    matches = difflib.get_close_matches(norm_keyword, norm_keywords, n=1, cutoff=0.5)
    if matches:
        idx = norm_keywords.index(matches[0])
        return group_names[idx]
    return None

# --- OpenAI 분류 함수 ---
def recommend_group_and_type_with_openai(keyword, group_names):
    if not OPENAI_API_KEY:
        return keyword, '경쟁사'  # 기본값
    prompt = f"""
아래는 이미 등록된 브랜드 그룹명 목록입니다: {', '.join(group_names)}
신규 키워드: {keyword}
아래 조건에 따라 그룹명과 유형(자사/경쟁사)을 각각 한 단어로만 답변하세요.

조건:
- F&F, F&F홀딩스, F&F엔터테인먼트, F&Co, 에프앤에프 및 이 회사들에 속한 브랜드(디스커버리 익스페디션, MLB, 세르지오 타키니, 수프라, 듀베티카, 디스커버리 키즈, MLB키즈, 바닐라코, banilaco, AHOF, UNIS, 그룹 아홉, 그룹 유니스)는 모두 '자사'
- 영문 키워드가 한글로 소리나는 대로 읽었을 때 기존 그룹명과 유사하면 같은 그룹으로 묶으세요. (예: Discovery Expedition ↔ 디스커버리 익스페디션, MLB ↔ 엠엘비)
- 그 외 브랜드는 모두 '경쟁사'
- 그룹명과 유형을 쉼표(,)로 구분해서 한 줄로만 답변하세요. (예: MLB,자사)
- 설명이나 문장 없이 그룹명과 유형만 한 줄로 답변하세요.
"""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    result = response.choices[0].message.content.strip()
    if ',' in result:
        group_name, type_ = [x.strip() for x in result.split(',', 1)]
    else:
        group_name = result.strip()
        type_ = '경쟁사'
    if not group_name or group_name.lower() == keyword.lower() or len(group_name) < 2:
        group_name = keyword
    return group_name, type_

# --- API 라우트 ---
@keywords_bp.route('/keywords', methods=['GET'])
def get_keywords():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM keywords WHERE is_active=1")
    keywords = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'keywords': keywords})

@keywords_bp.route('/keywords', methods=['POST'])
def add_keyword():
    data = request.get_json()
    keyword = data.get('keyword')
    group_name = data.get('group_name')
    type_ = data.get('type')
    ip = request.remote_addr
    if not group_name or not type_:
        similar_group = find_similar_group_name(keyword)
        if similar_group:
            group_name = similar_group
        else:
            # 기존 그룹명 목록 추출
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT group_name FROM keywords WHERE is_active=1")
            group_name_list = [row['group_name'] for row in cursor.fetchall()]
            conn.close()
            
            # AI를 사용하여 그룹명과 유형 추천
            ai_group_name, ai_type = recommend_group_and_type_with_openai(keyword, group_name_list)
            
            if not group_name:
                group_name = ai_group_name
            if not type_:
                type_ = ai_type
    # 그룹 기준 type 일관성 강제
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT type FROM keywords WHERE group_name=? AND is_active=1", (group_name,))
    types = [row['type'] for row in cursor.fetchall()]
    if types:
        type_ = types[0]
    conn.close()
    # 자사 브랜드 강제 분류
    if keyword in OWN_BRANDS:
        type_ = '자사'
    if not group_name or not group_name.strip():
        group_name = keyword
    if not type_ or not type_.strip():
        type_ = '경쟁사'
    if not keyword or not group_name or not type_:
        return jsonify({'success': False, 'error': 'keyword, group_name, type 필수'}), 400
    conn = get_db()
    cursor = conn.cursor()
    try:
        existing = cursor.execute("SELECT id, is_active FROM keywords WHERE keyword=? LIMIT 1", (keyword,)).fetchone()
        if existing:
            if existing['is_active'] == 0:
                cursor.execute("UPDATE keywords SET is_active=1, deactivated_at=NULL, group_name=?, type=? WHERE id=", (group_name, type_, existing['id']))
            else:
                conn.close()
                return jsonify({'success': False, 'error': '이미 존재하는 키워드입니다.'}), 400
        else:
            cursor.execute(
                "INSERT INTO keywords (ip, keyword, group_name, type) VALUES (?, ?, ?, ?)",
                (ip, keyword, group_name, type_)
            )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': '이미 존재하는 키워드입니다.'}), 400
    conn.close()
    return jsonify({'success': True, 'message': '키워드가 추가되었습니다.', 'type': type_, 'group_name': group_name}), 201

@keywords_bp.route('/keywords/<int:keyword_id>', methods=['PUT', 'PATCH'])
def update_keyword(keyword_id):
    data = request.get_json()
    keyword = data.get('keyword')
    group_name = data.get('group_name')
    type_ = data.get('type')
    is_active = data.get('is_active')
    if not group_name:
        group_name = keyword
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE keywords SET keyword=?, group_name=?, type=?, is_active=? WHERE id=?",
            (keyword, group_name, type_, is_active, keyword_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': '이미 존재하는 키워드입니다.'}), 400
    conn.close()
    return jsonify({'success': True, 'message': '키워드 수정 완료', 'type': type_, 'group_name': group_name})

@keywords_bp.route('/keywords/<int:keyword_id>', methods=['DELETE'])
def delete_keyword(keyword_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE keywords SET is_active=0, deactivated_at=datetime('now', 'localtime') WHERE id=?", (keyword_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '키워드가 삭제되었습니다.'})

@keywords_bp.route('/keywords/stats', methods=['GET'])
def get_keywords_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM keywords WHERE is_active=1")
    total_count = cursor.fetchone()['total']
    today_articles = 0
    press_releases = 0
    organic_articles = 0
    conn.close()
    return jsonify({
        'success': True,
        'data': {
            'total_count': total_count,
            'today_articles': today_articles,
            'press_releases': press_releases,
            'organic_articles': organic_articles
        }
    })

@keywords_bp.route('/keywords/monthly_stats', methods=['GET'])
def get_keywords_monthly_stats():
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now()
    start_of_month = today.replace(day=1)
    start_str = start_of_month.strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT k.keyword, k.type, k.group_name,
            COUNT(CASE WHEN a.id IS NOT NULL 
                  AND (cl.classification_result IS NULL OR cl.classification_result != '해당없음') 
                  THEN 1 END) as total_articles,
            COUNT(CASE WHEN cl.classification_result='보도자료' THEN 1 END) as press_releases
        FROM keywords k
        LEFT JOIN articles a ON a.keyword=k.keyword AND DATE(a.pub_date) >= ?
        LEFT JOIN classification_logs cl ON cl.url=a.url
        WHERE k.is_active=1
        GROUP BY k.keyword, k.type, k.group_name
    ''', (start_str,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        total = row['total_articles'] or 0
        press = row['press_releases'] or 0
        coverage_rate = int((press / total) * 100) if total else 0
        result.append({
            "keyword": row['keyword'],
            "type": row['type'],
            "group_name": row['group_name'],
            "total_articles": total,
            "press_releases": press,
            "mention_rate": coverage_rate
        })
    conn.close()
    return jsonify({"success": True, "data": result})
