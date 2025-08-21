from flask import Flask, request, jsonify, render_template
import sqlite3
from flask_cors import CORS
import os

# Flask 앱 생성 시 템플릿 폴더 경로 지정
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)
CORS(app)  # CORS 허용 (React 등 프론트엔드 연동 시 필요)

# 데이터베이스 경로 설정
DB_PATH = "db.sqlite" if os.path.exists("db.sqlite") else "backend/db.sqlite"

def auto_group_keyword(keyword):
    BRAND_GROUP_MAP = {
        "스노우피크 어패럴": "스노우피크",
        "스노우피크": "스노우피크",
        "Snow Peak Apparel": "스노우피크",
        "Snow Peak": "스노우피크",
        # 필요시 추가
    }
    if keyword in BRAND_GROUP_MAP:
        return BRAND_GROUP_MAP[keyword]
    for suffix in [" 어패럴", " 코리아", " 주식회사", " (주)", "㈜"]:
        if keyword.endswith(suffix):
            base = keyword.replace(suffix, "")
            if base in BRAND_GROUP_MAP:
                return BRAND_GROUP_MAP[base]
    norm = keyword.lower().replace(" ", "")
    for k, v in BRAND_GROUP_MAP.items():
        if norm == k.lower().replace(" ", ""):
            return v
    return keyword

# 메인 페이지 렌더링
@app.route("/")
def home():
    return render_template('index.html')

# IP 주소 가져오기 (프록시 환경 고려)
def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

# 1. 키워드 조회 API (GET)
@app.route("/api/keywords", methods=["GET"])
def get_keywords():
    try:
        ip = get_client_ip()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, keyword, type FROM keywords WHERE ip = ? ORDER BY id", (ip,))
        keywords = [{"id": row[0], "keyword": row[1], "type": row[2] or '자사'} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": keywords,
            "ip": ip
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 2. 키워드 추가 API (POST)
@app.route("/api/keywords", methods=["POST"])
def add_keyword():
    try:
        ip = get_client_ip()
        data = request.get_json()
        keyword = data.get("keyword", "").strip()
        type_ = data.get("type", "자사").strip()
        if not keyword:
            return jsonify({
                "success": False,
                "error": "키워드를 입력해주세요."
            }), 400
        # 자동 그룹핑 적용
        keyword_group = auto_group_keyword(keyword)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # 중복 키워드 확인
        cursor.execute("SELECT id FROM keywords WHERE ip = ? AND keyword = ?", (ip, keyword))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "error": "이미 등록된 키워드입니다."
            }), 400
        # 키워드 추가 (keyword_group도 함께 저장)
        cursor.execute("INSERT INTO keywords (ip, keyword, type, keyword_group) VALUES (?, ?, ?, ?)", (ip, keyword, type_, keyword_group))
        keyword_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "message": "키워드가 추가되었습니다.",
            "data": {"id": keyword_id, "keyword": keyword, "type": type_, "keyword_group": keyword_group}
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 3. 키워드 수정 API (PUT)
@app.route("/api/keywords/<int:keyword_id>", methods=["PUT"])
def update_keyword(keyword_id):
    try:
        ip = get_client_ip()
        data = request.get_json()
        new_keyword = data.get("keyword", "").strip()
        new_type = data.get("type", "자사").strip()
        if not new_keyword:
            return jsonify({
                "success": False,
                "error": "키워드를 입력해주세요."
            }), 400
        # 자동 그룹핑 적용
        new_keyword_group = auto_group_keyword(new_keyword)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # 해당 IP의 키워드인지 확인
        cursor.execute("SELECT keyword FROM keywords WHERE id = ? AND ip = ?", (keyword_id, ip))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return jsonify({
                "success": False,
                "error": "수정할 수 있는 키워드가 없습니다."
            }), 404
        # 중복 키워드 확인 (자신 제외)
        cursor.execute("SELECT id FROM keywords WHERE ip = ? AND keyword = ? AND id != ?", 
                      (ip, new_keyword, keyword_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "error": "이미 등록된 키워드입니다."
            }), 400
        # 키워드 및 그룹 수정
        cursor.execute("UPDATE keywords SET keyword = ?, type = ?, keyword_group = ? WHERE id = ? AND ip = ?", 
                      (new_keyword, new_type, new_keyword_group, keyword_id, ip))
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "message": "키워드가 수정되었습니다.",
            "data": {"id": keyword_id, "keyword": new_keyword, "type": new_type, "keyword_group": new_keyword_group}
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 4. 키워드 삭제 API (DELETE)
@app.route("/api/keywords/<int:keyword_id>", methods=["DELETE"])
def delete_keyword(keyword_id):
    try:
        ip = get_client_ip()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 해당 IP의 키워드인지 확인 후 삭제
        cursor.execute("DELETE FROM keywords WHERE id = ? AND ip = ?", (keyword_id, ip))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "삭제할 수 있는 키워드가 없습니다."
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "키워드가 삭제되었습니다."
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 5. 키워드 일괄 저장 API (기존 코드 개선)
@app.route("/api/keywords/batch", methods=["POST"])
def save_keywords_batch():
    try:
        ip = get_client_ip()
        data = request.get_json()
        keywords = data.get("keywords", [])
        
        if not isinstance(keywords, list):
            return jsonify({
                "success": False,
                "error": "키워드는 배열 형태로 전송해주세요."
            }), 400
        
        # 빈 키워드 필터링
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 기존 키워드 삭제
        cursor.execute("DELETE FROM keywords WHERE ip = ?", (ip,))
        
        # 새 키워드 추가
        for keyword in keywords:
            cursor.execute("INSERT INTO keywords (ip, keyword) VALUES (?, ?)", (ip, keyword))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"{len(keywords)}개의 키워드가 저장되었습니다.",
            "data": {"count": len(keywords)}
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 6. IP별 키워드 통계 API
@app.route("/api/keywords/stats", methods=["GET"])
def get_keywords_stats():
    try:
        ip = get_client_ip()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 키워드 개수 조회
        cursor.execute("SELECT COUNT(*) FROM keywords WHERE ip = ?", (ip,))
        total_count = cursor.fetchone()[0]
        
        # 최근 추가된 키워드
        cursor.execute("SELECT keyword FROM keywords WHERE ip = ? ORDER BY id DESC LIMIT 5", (ip,))
        recent_keywords = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "total_count": total_count,
                "recent_keywords": recent_keywords,
                "ip": ip
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# 7. 키워드 저장 API (POST)
@app.route("/save_keywords", methods=["POST"])
def save_keywords():
    ip = get_client_ip()
    data = request.get_json()
    keywords = data.get("keywords", [])
    type_ = data.get("type", "자사")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 기존 키워드 삭제
    c.execute("DELETE FROM keywords WHERE ip = ?", (ip,))
    for kw in keywords:
        c.execute("INSERT INTO keywords (ip, keyword, type) VALUES (?, ?, ?)", (ip, kw, type_))

    conn.commit()
    conn.close()

    return jsonify({"message": "브랜드 키워드가 저장되었습니다."})

# 8. 키워드 조회 API (GET)
@app.route("/get_keywords", methods=["GET"])
def get_keywords_legacy():
    ip = get_client_ip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, keyword, type FROM keywords WHERE ip = ? ORDER BY id", (ip,))
    keywords = [
        {"id": row[0], "keyword": row[1], "type": row[2] or '자사'} for row in c.fetchall()
    ]
    conn.close()
    return jsonify({"keywords": keywords, "ip": ip})

# 테스트용 서버 시작
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
