import os
import sqlite3
import pandas as pd
import logging
import json
from datetime import datetime
from news_classifier import NewsClassifier
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VerificationResultProcessor:
    """
    수동 검증 결과를 모델 파인튜닝에 적용하는 클래스
    """
    
    def __init__(self, db_path=None, model_path="models"):
        self.db_path = db_path or os.getenv('DB_PATH')
        self.model_path = model_path
        self.classifier = NewsClassifier(db_path=db_path, model_path=model_path)
    
    def load_verification_results(self, verification_file):
        """검증 결과 파일 로드"""
        try:
            with open(verification_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            logger.info(f"📂 검증 결과 로드 완료: {len(results)}개")
            return results
            
        except Exception as e:
            logger.error(f"검증 결과 로드 중 오류: {e}")
            return None
    
    def extract_wrong_predictions(self, verification_results):
        """틀린 예측들만 추출"""
        wrong_predictions = []
        
        for item in verification_results:
            if not item['is_correct'] and 'correct_label' in item:
                wrong_predictions.append({
                    'title': item['title'],
                    'content': item['content'],
                    'keyword': item['keyword'],
                    'classification_result': item['correct_label'],
                    'original_prediction': item['predicted_class'],
                    'confidence': item['confidence'],
                    'group_name': item['group_name']
                })
        
        logger.info(f"📊 틀린 예측 {len(wrong_predictions)}개 추출")
        return wrong_predictions
    
    def load_existing_training_data(self):
        """기존 학습 데이터 로드"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT title, content, keyword, classification_result
            FROM articles 
            WHERE classification_result IS NOT NULL
            AND classification_result IN ('보도자료', '오가닉', '해당없음')
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"📂 기존 학습 데이터 로드 완료: {len(df)}개")
            return df
            
        except Exception as e:
            logger.error(f"기존 학습 데이터 로드 중 오류: {e}")
            return pd.DataFrame()
    
    def create_finetuning_dataset(self, wrong_predictions, existing_data):
        """파인튜닝용 데이터셋 생성"""
        # 틀린 예측들을 DataFrame으로 변환
        wrong_df = pd.DataFrame(wrong_predictions)
        
        # 기존 데이터와 합치기
        combined_df = pd.concat([existing_data, wrong_df], ignore_index=True)
        
        # 중복 제거 (URL 기준이 아니라면 제목+내용 기준)
        combined_df = combined_df.drop_duplicates(subset=['title', 'content'], keep='first')
        
        logger.info(f"📊 파인튜닝 데이터셋 생성 완료:")
        logger.info(f"  - 기존 데이터: {len(existing_data)}개")
        logger.info(f"  - 틀린 예측: {len(wrong_predictions)}개")
        logger.info(f"  - 최종 데이터셋: {len(combined_df)}개")
        
        return combined_df
    
    def save_finetuning_data(self, dataset, filename=None):
        """파인튜닝 데이터 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"finetuning_data_{timestamp}.json"
        
        filepath = os.path.join(self.model_path, filename)
        
        try:
            # DataFrame을 JSON으로 변환
            data_list = dataset.to_dict('records')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 파인튜닝 데이터 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"파인튜닝 데이터 저장 중 오류: {e}")
            return None
    
    def run_finetuning(self, finetuning_data_path, epochs=3):
        """모델 파인튜닝 실행"""
        try:
            logger.info("🚀 모델 파인튜닝 시작...")
            
            # 파인튜닝 데이터 로드
            with open(finetuning_data_path, 'r', encoding='utf-8') as f:
                finetuning_data = json.load(f)
            
            # NewsClassifier의 파인튜닝 메서드 호출
            # (기존 train_koelectra_model 메서드를 재사용)
            success = self.classifier.train_koelectra_model(
                training_data=finetuning_data,
                epochs=epochs,
                is_finetuning=True
            )
            
            if success:
                logger.info("✅ 모델 파인튜닝 완료!")
                return True
            else:
                logger.error("❌ 모델 파인튜닝 실패!")
                return False
                
        except Exception as e:
            logger.error(f"파인튜닝 중 오류: {e}")
            return False
    
    def analyze_improvements(self, verification_results):
        """개선 사항 분석"""
        print(f"\n{'='*80}")
        print(f"📈 개선 사항 분석")
        print(f"{'='*80}")
        
        # 그룹별 오류 분석
        group_errors = {}
        for item in verification_results:
            if not item['is_correct']:
                group = item['group_name']
                if group not in group_errors:
                    group_errors[group] = []
                group_errors[group].append({
                    'predicted': item['predicted_class'],
                    'correct': item['correct_label'],
                    'confidence': item['confidence']
                })
        
        print(f"\n🔍 그룹별 오류 패턴:")
        for group, errors in group_errors.items():
            print(f"\n  {group}:")
            for error in errors:
                print(f"    예측: {error['predicted']} → 실제: {error['correct']} (신뢰도: {error['confidence']:.3f})")
        
        # 분류별 오류 분석
        class_errors = {}
        for item in verification_results:
            if not item['is_correct']:
                pred_class = item['predicted_class']
                if pred_class not in class_errors:
                    class_errors[pred_class] = []
                class_errors[pred_class].append(item['correct_label'])
        
        print(f"\n📊 분류별 오류 패턴:")
        for pred_class, correct_labels in class_errors.items():
            print(f"  {pred_class}로 잘못 분류된 것들:")
            for correct_label in correct_labels:
                print(f"    → {correct_label}")

def main():
    """메인 실행 함수"""
    logger.info("=== 검증 결과 파인튜닝 적용 시작 ===")
    
    processor = VerificationResultProcessor()
    
    # 1. 검증 결과 파일 여러 개 선택
    model_dir = processor.model_path
    verification_files = [f for f in os.listdir(model_dir) if f.startswith('verification_results_')]
    
    if not verification_files:
        logger.error("❌ 검증 결과 파일을 찾을 수 없습니다!")
        logger.info("💡 먼저 enhanced_verification.py를 실행해서 검증을 완료하세요.")
        return
    
    print("사용 가능한 검증 결과 파일 목록:")
    for i, fname in enumerate(sorted(verification_files), 1):
        print(f"{i}. {fname}")
    idxs = input("사용할 파일 번호를 콤마(,)로 구분해서 입력하세요 (예: 1,3): ")
    idx_list = [int(x.strip())-1 for x in idxs.split(',') if x.strip().isdigit()]
    selected_files = [os.path.join(model_dir, sorted(verification_files)[i]) for i in idx_list if 0 <= i < len(verification_files)]
    if not selected_files:
        print("선택된 파일이 없습니다. 종료합니다.")
        return
    print("📂 사용할 검증 결과 파일:")
    for f in selected_files:
        print(" -", os.path.basename(f))
    # 여러 파일의 결과 합치기
    all_verification_results = []
    for f in selected_files:
        results = processor.load_verification_results(f)
        if results:
            all_verification_results.extend(results)
    verification_results = all_verification_results
    if not verification_results:
        print("선택한 파일에서 검증 결과를 불러오지 못했습니다. 종료합니다.")
        return
    
    # 3. 틀린 예측 추출
    wrong_predictions = processor.extract_wrong_predictions(verification_results)
    if not wrong_predictions:
        logger.warning("⚠️ 틀린 예측이 없습니다. 파인튜닝이 필요하지 않습니다.")
        return
    
    # 4. 개선 사항 분석
    processor.analyze_improvements(verification_results)
    
    # 5. 기존 학습 데이터 로드
    existing_data = processor.load_existing_training_data()
    
    # 6. 파인튜닝 데이터셋 생성
    finetuning_dataset = processor.create_finetuning_dataset(wrong_predictions, existing_data)

    # 파인튜닝 데이터 분포 확인 및 경고
    counts = finetuning_dataset['classification_result'].value_counts()
    print("\n[파인튜닝 데이터 클래스 분포]")
    print(counts)
    if (counts < 2).any():
        print("⚠️ 각 클래스별로 최소 2개 이상 데이터가 필요합니다. 수동 검증 데이터를 더 추가해 주세요.")
        return
    
    # 7. 파인튜닝 데이터 저장
    finetuning_data_path = processor.save_finetuning_data(finetuning_dataset)
    if not finetuning_data_path:
        return
    
    # 8. 사용자 확인
    print(f"\n{'='*80}")
    print(f"🚀 파인튜닝 준비 완료!")
    print(f"{'='*80}")
    print(f"  - 틀린 예측: {len(wrong_predictions)}개")
    print(f"  - 기존 데이터: {len(existing_data)}개")
    print(f"  - 최종 데이터셋: {len(finetuning_dataset)}개")
    print(f"  - 파인튜닝 데이터: {finetuning_data_path}")
    
    confirm = input(f"\n🤔 파인튜닝을 실행하시겠습니까? (y/n): ").lower().strip()
    
    if confirm == 'y':
        # 9. 파인튜닝 실행
        epochs = int(input("파인튜닝 에포크 수를 입력하세요 (기본값: 3): ") or "3")
        
        success = processor.run_finetuning(finetuning_data_path, epochs=epochs)
        
        if success:
            print(f"\n🎉 파인튜닝 완료!")
            print(f"💡 이제 새로운 모델로 테스트해보세요.")
        else:
            print(f"\n❌ 파인튜닝 실패!")
    else:
        print(f"\n💡 파인튜닝이 취소되었습니다.")
        print(f"   파인튜닝 데이터는 {finetuning_data_path}에 저장되어 있습니다.")
    
    logger.info("=== 검증 결과 파인튜닝 적용 완료 ===")

if __name__ == "__main__":
    main() 