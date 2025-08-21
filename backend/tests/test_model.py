import os
import sqlite3
import pandas as pd
import logging
import json
from news_classifier import NewsClassifier
from dotenv import load_dotenv
from datetime import datetime

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_unclassified_data():
    """미분류 데이터 현황 확인"""
    try:
        db_path = os.getenv('DB_PATH')
        conn = sqlite3.connect(db_path)
        
        # 전체 데이터 현황 (올바른 방법)
        query = """
        SELECT 
            COUNT(*) as total_articles,
            COUNT(CASE WHEN cl.url IS NOT NULL THEN 1 END) as classified,
            COUNT(CASE WHEN cl.url IS NULL THEN 1 END) as unclassified
        FROM articles a
        LEFT JOIN classification_logs cl ON a.url = cl.url
        """
        
        df = pd.read_sql_query(query, conn)
        logger.info(f"📊 데이터 현황:")
        logger.info(f"   전체 기사: {df['total_articles'].iloc[0]:,}개")
        logger.info(f"   분류 완료: {df['classified'].iloc[0]:,}개")
        logger.info(f"   미분류: {df['unclassified'].iloc[0]:,}개")
        
        # 미분류 데이터 샘플 확인 (올바른 방법)
        sample_query = """
        SELECT a.title, a.content, a.keyword, a.created_at, a.url
        FROM articles a
        LEFT JOIN classification_logs cl ON a.url = cl.url
        WHERE cl.url IS NULL
        LIMIT 10
        """
        
        sample_df = pd.read_sql_query(sample_query, conn)
        logger.info(f"\n📝 미분류 데이터 샘플 (상위 5개):")
        for idx, row in sample_df.iterrows():
            logger.info(f"   {idx+1}. 제목: {row['title'][:50]}...")
            logger.info(f"      키워드: {row['keyword']}")
            logger.info(f"      URL: {row['url'][:50]}...")
            logger.info(f"      날짜: {row['created_at']}")
            logger.info("")
        
        conn.close()
        return df['unclassified'].iloc[0]
        
    except Exception as e:
        logger.error(f"데이터 확인 중 오류: {e}")
        return 0

def test_model_on_unclassified():
    """미분류 데이터로 모델 테스트 (그룹별 균등)"""
    try:
        logger.info("🤖 모델 로드 중...")
        # 올바른 모델 경로 지정
        classifier = NewsClassifier(model_path="../src/ml/models")
        
        if not classifier.load_koelectra_model():
            logger.error("모델 로드 실패!")
            return
        
        logger.info("✅ 모델 로드 완료")
        
        # 그룹별 미분류 데이터 가져오기
        db_path = os.getenv('DB_PATH')
        conn = sqlite3.connect(db_path)
        
        # 먼저 미분류된 그룹들과 각각의 개수 확인
        group_query = """
        SELECT a.group_name, COUNT(*) as count
        FROM articles a
        LEFT JOIN classification_logs cl ON a.url = cl.url
        WHERE cl.url IS NULL
        GROUP BY a.group_name
        ORDER BY count DESC
        """
        
        group_df = pd.read_sql_query(group_query, conn)
        logger.info(f"📊 그룹별 미분류 데이터 현황:")
        for idx, row in group_df.iterrows():
            logger.info(f"   {row['group_name']}: {row['count']}개")
        
        # 그룹별로 5개씩 테스트 데이터 가져오기
        all_test_data = []
        
        for group_name in group_df['group_name']:
            query = """
            SELECT a.id, a.title, a.content, a.keyword, a.group_name, a.created_at, a.url
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE cl.url IS NULL AND a.group_name = ?
            ORDER BY a.created_at DESC
            LIMIT 10
            """
            
            group_data = pd.read_sql_query(query, conn, params=[group_name])
            all_test_data.append(group_data)
        
        conn.close()
        
        # 모든 테스트 데이터 합치기
        test_df = pd.concat(all_test_data, ignore_index=True)
        
        if len(test_df) == 0:
            logger.warning("테스트할 미분류 데이터가 없습니다.")
            return
        
        logger.info(f"🧪 {len(test_df)}개 미분류 데이터로 테스트 시작... (그룹별 10개씩)")
        
        # 예측 실행
        results = []
        for idx, row in test_df.iterrows():
            try:
                result = classifier.predict(row['title'], row['content'], row['keyword'])
                
                results.append({
                    'id': row['id'],
                    'title': row['title'][:50] + "..." if len(row['title']) > 50 else row['title'],
                    'keyword': row['keyword'],
                    'group_name': row['group_name'],
                    'predicted_class': result['classification'],
                    'confidence': result['confidence'],
                    'probabilities': result['probabilities']
                })
                
                logger.info(f"📰 {idx+1:2d}. [{row['group_name']}] {result['classification']} ({result['confidence']:.3f}) - {row['title'][:40]}...")
                
            except Exception as e:
                logger.error(f"예측 중 오류 (ID: {row['id']}): {e}")
        
        # 결과 요약
        logger.info(f"\n📊 테스트 결과 요약:")
        logger.info(f"   테스트 데이터: {len(results)}개")
        
        # 그룹별 통계
        group_stats = {}
        for result in results:
            group_name = result['group_name']
            if group_name not in group_stats:
                group_stats[group_name] = {'total': 0, 'high_conf': 0, 'classes': {}}
            
            group_stats[group_name]['total'] += 1
            if result['confidence'] > 0.8:
                group_stats[group_name]['high_conf'] += 1
            
            pred_class = result['predicted_class']
            group_stats[group_name]['classes'][pred_class] = group_stats[group_name]['classes'].get(pred_class, 0) + 1
        
        logger.info(f"   그룹별 결과:")
        for group_name, stats in group_stats.items():
            high_conf_rate = stats['high_conf'] / stats['total'] * 100
            logger.info(f"     {group_name}: {stats['total']}개 (신뢰도>0.8: {stats['high_conf']}개, {high_conf_rate:.1f}%)")
            for class_name, count in stats['classes'].items():
                logger.info(f"       - {class_name}: {count}개")
        
        # 전체 분류별 통계
        class_counts = {}
        high_confidence = 0
        
        for result in results:
            pred_class = result['predicted_class']
            confidence = result['confidence']
            
            class_counts[pred_class] = class_counts.get(pred_class, 0) + 1
            if confidence > 0.8:
                high_confidence += 1
        
        logger.info(f"\n   전체 분류 결과:")
        for class_name, count in class_counts.items():
            logger.info(f"     {class_name}: {count}개")
        
        logger.info(f"   높은 신뢰도 (>0.8): {high_confidence}개 ({high_confidence/len(results)*100:.1f}%)")
        
        # 상위 신뢰도 예측들
        high_conf_results = sorted(results, key=lambda x: x['confidence'], reverse=True)[:5]
        logger.info(f"\n🏆 상위 신뢰도 예측 (상위 5개):")
        for idx, result in enumerate(high_conf_results, 1):
            logger.info(f"   {idx}. [{result['group_name']}] {result['predicted_class']} ({result['confidence']:.3f})")
            logger.info(f"      제목: {result['title']}")
            logger.info("")
        
        return results
        
    except Exception as e:
        logger.error(f"모델 테스트 중 오류: {e}")
        return []

def load_verification_results():
    """검증 결과 파일들 로드"""
    model_dir = "../src/ml/models"
    verification_files = [f for f in os.listdir(model_dir) if f.startswith('verification_results_')]
    
    if not verification_files:
        logger.warning("검증 결과 파일을 찾을 수 없습니다.")
        return []
    
    print("사용 가능한 검증 결과 파일:")
    for i, fname in enumerate(sorted(verification_files), 1):
        print(f"{i}. {fname}")
    
    choice = input("사용할 파일 번호를 입력하세요 (여러 개는 콤마로 구분): ")
    selected_indices = [int(x.strip())-1 for x in choice.split(',') if x.strip().isdigit()]
    
    all_results = []
    for idx in selected_indices:
        if 0 <= idx < len(verification_files):
            filepath = os.path.join(model_dir, sorted(verification_files)[idx])
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                all_results.extend(results)
                logger.info(f"📂 {os.path.basename(filepath)} 로드: {len(results)}개")
            except Exception as e:
                logger.error(f"파일 로드 실패 {filepath}: {e}")
    
    return all_results

def update_model_with_verification():
    """검증 결과로 모델 업데이트"""
    try:
        logger.info("🔄 모델 업데이트 시작...")
        
        # 1. 검증 결과 로드
        verification_results = load_verification_results()
        if not verification_results:
            logger.error("검증 결과를 로드할 수 없습니다.")
            return False
        
        # 2. 유효한 데이터 필터링
        valid_data = []
        for item in verification_results:
            if 'correct_label' in item and 'correct_reason' in item:
                valid_data.append({
                    'title': item['title'],
                    'content': item['content'],
                    'keyword': item['keyword'],
                    'classification': item['correct_label'],
                    'reason': item['correct_reason'],
                    'confidence': item['confidence']
                })
        
        if len(valid_data) < 10:
            logger.warning(f"파인튜닝 데이터가 부족합니다 (최소 10개 필요, 현재: {len(valid_data)}개)")
            return False
        
        logger.info(f"📊 파인튜닝 데이터 준비: {len(valid_data)}개")
        
        # 3. 모델 로드
        classifier = NewsClassifier(model_path="../src/ml/models")
        if not classifier.load_koelectra_model():
            logger.error("모델 로드 실패!")
            return False
        
        # 4. 파인튜닝 실행
        logger.info("🚀 파인튜닝 시작...")
        success = classifier.train_koelectra_model(
            training_data=valid_data,
            epochs=3,  # 빠른 파인튜닝
            is_finetuning=True
        )
        
        if success:
            logger.info("✅ 모델 업데이트 완료!")
            
            # 5. 업데이트 후 성능 테스트
            logger.info("🧪 업데이트 후 성능 테스트...")
            test_results = test_model_on_unclassified()
            
            if test_results:
                logger.info("✅ 성능 테스트 완료!")
                logger.info("💡 업데이트 전후 성능을 비교해보세요.")
            
            return True
        else:
            logger.error("❌ 모델 업데이트 실패!")
            return False
            
    except Exception as e:
        logger.error(f"모델 업데이트 중 오류: {e}")
        return False

def compare_model_performance():
    """모델 성능 비교 (업데이트 전후)"""
    logger.info("📊 모델 성능 비교 시작...")
    
    # 1. 현재 모델 성능 테스트
    logger.info("🔍 현재 모델 성능 테스트...")
    current_results = test_model_on_unclassified()
    
    if not current_results:
        logger.error("현재 모델 테스트 실패!")
        return
    
    # 2. 업데이트 실행
    logger.info("🔄 모델 업데이트 실행...")
    update_success = update_model_with_verification()
    
    if not update_success:
        logger.error("모델 업데이트 실패!")
        return
    
    # 3. 업데이트 후 성능 테스트
    logger.info("🔍 업데이트 후 모델 성능 테스트...")
    updated_results = test_model_on_unclassified()
    
    if not updated_results:
        logger.error("업데이트 후 모델 테스트 실패!")
        return
    
    # 4. 성능 비교
    logger.info("📈 성능 비교 결과:")
    
    # 신뢰도 비교
    current_high_conf = sum(1 for r in current_results if r['confidence'] > 0.8)
    updated_high_conf = sum(1 for r in updated_results if r['confidence'] > 0.8)
    
    current_rate = current_high_conf / len(current_results) * 100
    updated_rate = updated_high_conf / len(updated_results) * 100
    
    logger.info(f"   높은 신뢰도 (>0.8) 비율:")
    logger.info(f"     업데이트 전: {current_high_conf}/{len(current_results)} ({current_rate:.1f}%)")
    logger.info(f"     업데이트 후: {updated_high_conf}/{len(updated_results)} ({updated_rate:.1f}%)")
    logger.info(f"     개선: {updated_rate - current_rate:+.1f}%")
    
    # 분류별 분포 비교
    current_classes = {}
    updated_classes = {}
    
    for r in current_results:
        current_classes[r['predicted_class']] = current_classes.get(r['predicted_class'], 0) + 1
    
    for r in updated_results:
        updated_classes[r['predicted_class']] = updated_classes.get(r['predicted_class'], 0) + 1
    
    logger.info(f"\n   분류별 분포 변화:")
    all_classes = set(current_classes.keys()) | set(updated_classes.keys())
    for class_name in all_classes:
        current_count = current_classes.get(class_name, 0)
        updated_count = updated_classes.get(class_name, 0)
        change = updated_count - current_count
        logger.info(f"     {class_name}: {current_count} → {updated_count} ({change:+.0f})")

def main():
    """메인 실행 함수"""
    logger.info("=== 모델 테스트 및 업데이트 시스템 ===")
    
    print("\n🔧 사용 가능한 기능:")
    print("1. 미분류 데이터 현황 확인")
    print("2. 현재 모델 성능 테스트")
    print("3. 검증 결과로 모델 업데이트")
    print("4. 모델 성능 비교 (업데이트 전후)")
    print("5. 종료")
    
    while True:
        choice = input("\n🤔 선택하세요 (1-5): ").strip()
        
        if choice == '1':
            check_unclassified_data()
        elif choice == '2':
            test_model_on_unclassified()
        elif choice == '3':
            update_model_with_verification()
        elif choice == '4':
            compare_model_performance()
        elif choice == '5':
            logger.info("프로그램을 종료합니다.")
            break
        else:
            print("1-5 중에서 선택해주세요.")

if __name__ == "__main__":
    main() 