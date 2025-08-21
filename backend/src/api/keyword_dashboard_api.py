from flask import Blueprint, jsonify
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()  # .env 파일에서 환경변수 불러오기

keyword_dashboard_bp = Blueprint('keyword_dashboard', __name__)

DB_PATH = os.getenv('DB_PATH')  # 환경변수에서 DB 경로 불러오기


def get_this_month_dates():
    """이번 달 1일~말일 날짜 범위를 반환"""
    today = datetime.now().date()
    # 이번 달 1일
    first_day = today.replace(day=1)
    # 다음 달 1일에서 하루 빼면 이번 달 마지막 날
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    last_day = next_month - timedelta(days=1)
    
    return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')


@keyword_dashboard_bp.route(
    '/keywords/group/<group_name>/stats', methods=['GET']
)
def group_keyword_stats(group_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 이번 달 날짜 범위 계산
    start_date, end_date = get_this_month_dates()

    # 그룹에 속한 키워드 이번 달 기사/보도자료/오가닉 집계 ('해당없음' 제외)
    cursor.execute("""
        SELECT
            a.group_name,
            COUNT(*) as total_articles,
            SUM(CASE WHEN c.classification_result = '보도자료'
                THEN 1 ELSE 0 END) as press_releases,
            SUM(CASE WHEN c.classification_result = '오가닉'
                THEN 1 ELSE 0 END) as organic_articles
        FROM articles a
        LEFT JOIN classification_logs c ON a.url = c.url
        WHERE a.group_name = ? AND DATE(a.pub_date) BETWEEN ? AND ?
        AND (c.classification_result IS NULL OR c.classification_result != '해당없음')
        GROUP BY a.group_name
    """, (group_name, start_date, end_date))
    row = cursor.fetchone()

    # 이번 달 전체 기사 수 조회 (모든 그룹 합계, '해당없음' 제외)
    cursor.execute("""
        SELECT COUNT(*) as total_all_articles
        FROM articles a
        LEFT JOIN classification_logs c ON a.url = c.url
        WHERE DATE(a.pub_date) BETWEEN ? AND ?
        AND (c.classification_result IS NULL OR c.classification_result != '해당없음')
    """, (start_date, end_date))
    total_all_articles = cursor.fetchone()[0]

    conn.close()

    if not row:
        return jsonify({'success': True, 'data': {
            'group_name': group_name,
            'total_articles': 0,
            'press_releases': 0,
            'organic_articles': 0,
            'mention_rate': 0
        }})

    total, press, organic = row[1], row[2], row[3]
    # 보도자료 커버리지 = (보도자료 수 / 전체 기사 수) × 100
    coverage_rate = round(
        (press / total) * 100
    ) if total else 0

    return jsonify({'success': True, 'data': {
        'group_name': group_name,
        'total_articles': total,
        'press_releases': press,
        'organic_articles': organic,
        'mention_rate': coverage_rate
    }})


@keyword_dashboard_bp.route(
    '/keywords/group/<group_name>/articles', methods=['GET']
)
def group_keyword_articles(group_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id, a.title, a.press, a.pub_date, a.url,
               IFNULL(c.classification_result, 'unknown'),
               IFNULL(c.confidence_score, 0)
        FROM articles a
        LEFT JOIN classification_logs c ON a.url = c.url
        WHERE a.group_name = ?
        AND (c.classification_result IS NULL OR c.classification_result != '해당없음')
        ORDER BY a.pub_date DESC
    """, (group_name,))
    articles = [
        {
            'id': row[0],
            'title': row[1],
            'press': row[2],
            'pub_date': row[3],
            'url': row[4],
            'classification_result': row[5],
            'confidence_score': row[6],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify({'success': True, 'data': articles})


@keyword_dashboard_bp.route(
    '/keywords/article/<int:article_id>/classification-reason',
    methods=['GET']
)
def get_classification_reason(article_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT url, group_name FROM articles WHERE id = ?", (article_id,))
    article_row = cursor.fetchone()
    if not article_row:
        conn.close()
        return jsonify({
            'success': False,
            'message': '기사를 찾을 수 없습니다.'
        })
    article_url, article_group_name = article_row

    # url + group_name으로 JOIN
    cursor.execute("""
        SELECT a.title, a.url, c.classification_result,
               c.confidence_score, c.reason, c.created_at
        FROM articles a
        LEFT JOIN classification_logs c ON a.url = c.url AND a.group_name = c.group_name
        WHERE a.id = ?
    """, (article_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({
            'success': False,
            'message': '기사를 찾을 수 없습니다.'
        })

    title, url, classification_result, confidence_score, reason, created_at = (
        row
    )

    return jsonify({
        'success': True,
        'data': {
            'title': title,
            'url': url,
            'classification_result': classification_result or 'unknown',
            'confidence_score': confidence_score or 0,
            'reason': reason or '분류 이유가 없습니다.',
            'created_at': created_at
        }
    })


@keyword_dashboard_bp.route(
    '/keywords/article/<int:article_id>/classification',
    methods=['PUT', 'OPTIONS']
)
def update_classification(article_id):
    from flask import request

    # OPTIONS 요청 처리 (CORS preflight)
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200

    data = request.get_json()
    new_classification = data.get('classification')
    reason = data.get('reason', '사용자 수정')

    if new_classification not in ['보도자료', '오가닉', '해당없음']:
        return jsonify({
            'success': False,
            'message': '유효하지 않은 분류 값입니다.'
        })

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 기사 URL, group_name 조회
    cursor.execute("SELECT url, group_name FROM articles WHERE id = ?", (article_id,))
    article_row = cursor.fetchone()

    if not article_row:
        conn.close()
        return jsonify({
            'success': False,
            'message': '기사를 찾을 수 없습니다.'
        })

    article_url, article_group_name = article_row

    # 기존 분류 로그 확인
    cursor.execute(
        "SELECT id FROM classification_logs WHERE url = ? AND group_name = ?",
        (article_url, article_group_name)
    )
    existing_log = cursor.fetchone()

    if existing_log:
        cursor.execute("""
            UPDATE classification_logs
            SET classification_result = ?,
                reason = ?,
                confidence_score = 1.0,
                created_at = ?
            WHERE url = ? AND group_name = ?
        """, (
            new_classification,
            reason,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            article_url,
            article_group_name
        ))
        print('UPDATE rowcount:', cursor.rowcount)
        # 추가: UPDATE 후 실제 값 확인
        cursor.execute(
            "SELECT reason FROM classification_logs WHERE url = ? AND group_name = ?",
            (article_url, article_group_name)
        )
        print('DB에 저장된 reason:', cursor.fetchone())
    else:
        # 새 분류 로그 생성
        cursor.execute(
            "SELECT keyword, group_name, title, content FROM articles "
            "WHERE id = ?",
            (article_id,)
        )
        article_data = cursor.fetchone()

        if article_data:
            keyword, group_name, title, content = article_data
            cursor.execute("""
                INSERT INTO classification_logs
                (keyword, group_name, title, content, url,
                 classification_result, confidence_score, reason,
                 processing_time, created_at, is_saved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                keyword, group_name, title, content, article_url,
                new_classification, 1.0, reason, 0.0,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1
            ))

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': '분류가 업데이트되었습니다.',
        'data': {
            'article_id': article_id,
            'new_classification': new_classification
        }
    })
