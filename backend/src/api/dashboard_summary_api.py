import os
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, jsonify

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "database", "db.sqlite")
)
dashboard_bp = Blueprint("dashboard", __name__)


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


@dashboard_bp.route('/dashboard/summary', methods=['GET'])
def dashboard_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 이번 달 날짜 범위 계산
    start_date, end_date = get_this_month_dates()

    # 이번 달 pub_date 기준 자사 보도자료 수 ('해당없음' 제외)
    cursor.execute('''
        SELECT COUNT(a.id)
        FROM articles a
        LEFT JOIN classification_logs cl ON a.url = cl.url
        JOIN keywords k ON a.keyword = k.keyword
        WHERE DATE(a.pub_date) BETWEEN ? AND ?
        AND cl.classification_result = '보도자료' AND k.type = '자사'
    ''', (start_date, end_date))
    month_press_releases = cursor.fetchone()[0]

    # 이번 달 pub_date 기준 자사 오가닉 기사 수 ('해당없음' 제외)
    cursor.execute('''
        SELECT COUNT(a.id)
        FROM articles a
        LEFT JOIN classification_logs cl ON a.url = cl.url
        JOIN keywords k ON a.keyword = k.keyword
        WHERE DATE(a.pub_date) BETWEEN ? AND ?
        AND cl.classification_result = '오가닉' AND k.type = '자사'
    ''', (start_date, end_date))
    month_organic_articles = cursor.fetchone()[0]

    # 이번 달 pub_date 기준 자사 기사 수 (보도자료+오가닉, '해당없음' 제외)
    month_articles = month_press_releases + month_organic_articles

    # 보도자료 커버리지율 계산: (보도자료 수 / 전체 기사 수) × 100
    coverage_rate = round((month_press_releases / month_articles) * 100) if month_articles > 0 else 0

    conn.close()
    return jsonify({
        'success': True,
        'data': {
            'month_articles': month_articles,
            'month_press_releases': month_press_releases,
            'month_organic_articles': month_organic_articles,
            'coverage_rate': coverage_rate
        }
    })


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 이번 달 날짜 범위 계산
    start_date, end_date = get_this_month_dates()

    # 이번 달 pub_date 기준 자사 보도자료 수 ('해당없음' 제외)
    cursor.execute('''
        SELECT COUNT(a.id)
        FROM articles a
        LEFT JOIN classification_logs cl ON a.url = cl.url
        JOIN keywords k ON a.keyword = k.keyword
        WHERE DATE(a.pub_date) BETWEEN ? AND ?
        AND cl.classification_result = '보도자료' AND k.type = '자사'
    ''', (start_date, end_date))
    month_press_releases = cursor.fetchone()[0]
    print("월간 자사 보도자료 수:", month_press_releases)

    # 이번 달 pub_date 기준 자사 오가닉 기사 수 ('해당없음' 제외)
    cursor.execute('''
        SELECT COUNT(a.id)
        FROM articles a
        LEFT JOIN classification_logs cl ON a.url = cl.url
        JOIN keywords k ON a.keyword = k.keyword
        WHERE DATE(a.pub_date) BETWEEN ? AND ?
        AND cl.classification_result = '오가닉' AND k.type = '자사'
    ''', (start_date, end_date))
    month_organic_articles = cursor.fetchone()[0]
    print("월간 자사 오가닉 기사 수:", month_organic_articles)

    # 이번 달 pub_date 기준 자사 기사 수 (보도자료+오가닉, '해당없음' 제외)
    month_articles = month_press_releases + month_organic_articles
    print("월간 자사 기사 수:", month_articles)

    # 보도자료 커버리지율 계산: (보도자료 수 / 전체 기사 수) × 100
    coverage_rate = round((month_press_releases / month_articles) * 100) if month_articles > 0 else 0
    print("보도자료 커버리지율:", coverage_rate, "%")

    conn.close() 