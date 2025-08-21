import os
import sqlite3
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from backend.src.ml.news_classifier import NewsClassifier

ml_classification_bp = Blueprint('ml_classification', __name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "db.sqlite")

@ml_classification_bp.route('/ml/train', methods=['POST'])
def train_model():
    """KoELECTRA 모델 학습"""
    try:
        classifier = NewsClassifier(DB_PATH)
        
        # 학습 데이터 로드
        df = classifier.load_training_data()
        
        if len(df) < 50:
            return jsonify({
                'success': False,
                'message': '학습 데이터가 부족합니다. 최소 50개 이상의 데이터가 필요합니다.',
                'data_count': len(df)
            }), 400
        
        # KoELECTRA 모델 학습
        results = classifier.train_koelectra_model(df)
        
        if 'error' in results:
            return jsonify({
                'success': False,
                'message': f'모델 학습 중 오류가 발생했습니다: {results["error"]}'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'KoELECTRA 모델 학습이 완료되었습니다.',
            'results': results,
            'data_count': len(df)
        })
        
    except Exception as e:
        logger.error(f"모델 학습 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'모델 학습 중 오류가 발생했습니다: {str(e)}'
        }), 500

@ml_classification_bp.route('/ml/predict', methods=['POST'])
def predict_article():
    """기사 분류 예측"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        keyword = data.get('keyword', '')
        
        if not all([title, content, keyword]):
            return jsonify({
                'success': False,
                'message': 'title, content, keyword가 모두 필요합니다.'
            }), 400
        
        classifier = NewsClassifier(DB_PATH)
        
        # 모델 로드
        if not classifier.load_koelectra_model():
            return jsonify({
                'success': False,
                'message': 'KoELECTRA 모델이 로드되지 않았습니다. 먼저 모델을 학습하세요.'
            }), 400
        
        # 예측 수행
        result = classifier.predict(title, content, keyword)
        
        return jsonify({
            'success': True,
            'prediction': result
        })
        
    except Exception as e:
        logger.error(f"예측 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'예측 중 오류가 발생했습니다: {str(e)}'
        }), 500

@ml_classification_bp.route('/ml/evaluate', methods=['POST'])
def evaluate_model():
    """모델 성능 평가"""
    try:
        classifier = NewsClassifier(DB_PATH)
        
        # 테스트 데이터 로드 (최근 데이터 사용)
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT 
                title, 
                content, 
                keyword, 
                classification_result,
                confidence_score
            FROM classification_logs 
            WHERE classification_result IN ('보도자료', '오가닉', '해당없음')
            AND confidence_score > 0.7
            ORDER BY created_at DESC
            LIMIT 100
        """
        
        import pandas as pd
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 10:
            return jsonify({
                'success': False,
                'message': '평가할 데이터가 부족합니다.'
            }), 400
        
        # 모델 로드
        if not classifier.load_koelectra_model():
            return jsonify({
                'success': False,
                'message': 'KoELECTRA 모델이 로드되지 않았습니다.'
            }), 400
        
        # 모델 평가
        evaluation_results = classifier.evaluate_model(df)
        
        return jsonify({
            'success': True,
            'evaluation': evaluation_results,
            'test_data_count': len(df)
        })
        
    except Exception as e:
        logger.error(f"모델 평가 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'모델 평가 중 오류가 발생했습니다: {str(e)}'
        }), 500

@ml_classification_bp.route('/ml/status', methods=['GET'])
def get_model_status():
    """모델 상태 확인"""
    try:
        classifier = NewsClassifier(DB_PATH)
        
        # 데이터베이스에서 학습 데이터 수 확인
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN classification_result = '보도자료' THEN 1 ELSE 0 END) as press_releases,
                   SUM(CASE WHEN classification_result = '오가닉' THEN 1 ELSE 0 END) as organic,
                   SUM(CASE WHEN classification_result = '해당없음' THEN 1 ELSE 0 END) as irrelevant
            FROM classification_logs 
            WHERE classification_result IN ('보도자료', '오가닉', '해당없음')
            AND confidence_score > 0.7
        """)
        
        data_stats = cursor.fetchone()
        conn.close()
        
        # 모델 정보 조회
        model_info = classifier.get_model_info()
        
        return jsonify({
            'success': True,
            'data_stats': {
                'total': data_stats[0] if data_stats[0] else 0,
                'press_releases': data_stats[1] if data_stats[1] else 0,
                'organic': data_stats[2] if data_stats[2] else 0,
                'irrelevant': data_stats[3] if data_stats[3] else 0
            },
            'model_info': model_info
        })
        
    except Exception as e:
        logger.error(f"모델 상태 확인 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'모델 상태 확인 중 오류가 발생했습니다: {str(e)}'
        }), 500

@ml_classification_bp.route('/ml/classify_batch', methods=['POST'])
def classify_batch():
    """배치 분류 (기존 GPT-4 대신 KoELECTRA 모델 사용)"""
    try:
        classifier = NewsClassifier(DB_PATH)
        
        # 모델 로드
        if not classifier.load_koelectra_model():
            return jsonify({
                'success': False,
                'message': 'KoELECTRA 모델이 로드되지 않았습니다.'
            }), 400
        
        # 분류되지 않은 기사 조회
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.title, a.content, a.keyword, a.group_name, a.url
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE cl.url IS NULL
            ORDER BY a.created_at DESC
            LIMIT 50
        """)
        
        articles = cursor.fetchall()
        conn.close()
        
        if not articles:
            return jsonify({
                'success': True,
                'message': '분류할 기사가 없습니다.',
                'processed_count': 0
            })
        
        # 배치 분류 수행
        processed_count = 0
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for article in articles:
            article_id, title, content, keyword, group_name, url = article
            
            # KoELECTRA 모델로 분류
            result = classifier.predict(title, content, keyword)
            
            # 결과 저장
            cursor.execute("""
                INSERT INTO classification_logs 
                (keyword, group_name, title, content, url, 
                 classification_result, confidence_score, reason, 
                 processing_time, created_at, is_saved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                keyword, group_name, title, content, url,
                result['classification'], result['confidence'],
                f'KoELECTRA 모델 분류', 0.0,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0
            ))
            
            processed_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{processed_count}개 기사 분류 완료',
            'processed_count': processed_count,
            'model_type': 'koelectra'
        })
        
    except Exception as e:
        logger.error(f"배치 분류 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'배치 분류 중 오류가 발생했습니다: {str(e)}'
        }), 500

@ml_classification_bp.route('/ml/compare', methods=['POST'])
def compare_with_gpt():
    """KoELECTRA와 GPT-4 분류 결과 비교"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        keyword = data.get('keyword', '')
        
        if not all([title, content, keyword]):
            return jsonify({
                'success': False,
                'message': 'title, content, keyword가 모두 필요합니다.'
            }), 400
        
        classifier = NewsClassifier(DB_PATH)
        
        # KoELECTRA 모델 로드
        if not classifier.load_koelectra_model():
            return jsonify({
                'success': False,
                'message': 'KoELECTRA 모델이 로드되지 않았습니다.'
            }), 400
        
        # KoELECTRA 예측
        koelectra_result = classifier.predict(title, content, keyword)
        
        # GPT-4 예측 (기존 시스템 사용)
        from backend.src.agents.news_ai_classification import NewsAIClassifier
        gpt_classifier = NewsAIClassifier(DB_PATH)
        gpt_result = gpt_classifier.classify_article(title, content, keyword)
        
        return jsonify({
            'success': True,
            'comparison': {
                'koelectra': koelectra_result,
                'gpt4': gpt_result,
                'agreement': koelectra_result['classification'] == gpt_result['classification']
            }
        })
        
    except Exception as e:
        logger.error(f"비교 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'비교 중 오류가 발생했습니다: {str(e)}'
        }), 500 