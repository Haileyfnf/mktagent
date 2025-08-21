import sqlite3
import os
from flask import Blueprint, request, jsonify
from backend.src.agents.news_ai_classification import NewsAIClassifier
from datetime import datetime

articles_bp = Blueprint('articles', __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '../database/news.db')

@articles_bp.route('/articles/classify/<int:article_id>', methods=['POST'])
def classify_article(article_id):
    """단일 기사를 AI로 분류합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 기사 조회
        cursor.execute("SELECT * FROM articles WHERE id=?", (article_id,))
        article = cursor.fetchone()
        
        if not article:
            conn.close()
            return jsonify({'error': '기사를 찾을 수 없습니다'}), 404
        
        # AI 분류 수행
        classifier = NewsAIClassifier(DB_PATH)
        result = classifier.classify_article(
            article['title'], 
            article['content'], 
            article['keyword']
        )
        
        # 분류 결과 저장
        cursor.execute("""
            INSERT INTO classification_logs 
            (article_id, keyword, classification, confidence, reason, title, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            article['keyword'],
            result['classification'],
            result['confidence'],
            result['reason'],
            article['title'],
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': '분류 완료',
            'result': result,
            'article_id': article_id
        })
        
    except Exception as e:
        return jsonify({'error': f'분류 중 오류 발생: {str(e)}'}), 500

@articles_bp.route('/articles/filtered', methods=['GET'])
def get_filtered_articles():
    """분류된 기사들을 필터링하여 조회합니다."""
    try:
        # 쿼리 파라미터
        classification = request.args.get('classification', '')  # 보도자료, 오가닉, 해당없음
        keyword = request.args.get('keyword', '')
        limit = int(request.args.get('limit', 100))
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 기본 쿼리
        query = """
            SELECT a.*, c.classification, c.confidence, c.reason, c.created_at as classified_at
            FROM articles a
            LEFT JOIN classification_logs c ON a.id = c.article_id
            WHERE 1=1
        """
        params = []
        
        # 필터 조건 추가
        if classification:
            query += " AND c.classification = ?"
            params.append(classification)
        
        if keyword:
            query += " AND a.keyword = ?"
            params.append(keyword)
        
        # 정렬 및 제한
        query += " ORDER BY c.created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'articles': articles,
            'count': len(articles),
            'filters': {
                'classification': classification,
                'keyword': keyword,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'기사 조회 중 오류 발생: {str(e)}'}), 500

@articles_bp.route('/articles/stats', methods=['GET'])
def get_articles_stats():
    """기사 및 분류 통계를 조회합니다."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 모니터링 키워드 수
        cursor.execute("SELECT COUNT(*) FROM keywords WHERE is_active=1")
        keyword_count = cursor.fetchone()[0]
        
        # 오늘 수집된 기사 수
        cursor.execute("SELECT COUNT(*) FROM articles WHERE date(created_at) = ?", (today,))
        today_articles = cursor.fetchone()[0]
        
        # 분류 통계 (오늘)
        cursor.execute("""
            SELECT classification, COUNT(*) as count 
            FROM classification_logs 
            WHERE date(created_at) = ?
            GROUP BY classification
        """, (today,))
        
        classification_stats = {}
        for row in cursor.fetchall():
            classification_stats[row[0]] = row[1]
        
        # 전체 분류 통계
        cursor.execute("""
            SELECT classification, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM classification_logs 
            GROUP BY classification
        """)
        
        total_stats = {}
        for row in cursor.fetchall():
            total_stats[row[0]] = {
                'count': row[1],
                'avg_confidence': round(row[2], 2) if row[2] else 0
            }
        
        conn.close()
        
        return jsonify({
            'keyword_count': keyword_count,
            'today_articles': today_articles,
            'today_classification': classification_stats,
            'total_classification': total_stats
        })
        
    except Exception as e:
        return jsonify({'error': f'통계 조회 중 오류 발생: {str(e)}'}), 500

@articles_bp.route('/articles/classify-batch', methods=['POST'])
def classify_articles_batch():
    """특정 키워드의 기사들을 일괄 분류합니다."""
    try:
        data = request.get_json()
        keyword = data.get('keyword')
        limit = data.get('limit', 50)
        
        if not keyword:
            return jsonify({'error': '키워드가 필요합니다'}), 400
        
        # AI 분류 수행
        classifier = NewsAIClassifier(DB_PATH)
        results = classifier.classify_articles_by_keyword(keyword, limit)
        
        return jsonify({
            'message': '일괄 분류 완료',
            'keyword': keyword,
            'processed_count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'일괄 분류 중 오류 발생: {str(e)}'}), 500 