import os
import sqlite3
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from datasets import Dataset
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeywordClassifier:
    """
    KoELECTRA 기반 키워드(브랜드) 분류 모델
    
    기능:
    - 뉴스 기사를 키워드별로 자동 분류
    - KoELECTRA 모델을 사용한 고성능 한국어 텍스트 분류
    - 동적 라벨 생성 (데이터에서 키워드 자동 추출)
    - 모델 학습, 저장, 로드, 예측 기능 제공
    """
    
    # 모델 설정 상수
    MODEL_NAME = "monologg/koelectra-base-v3-discriminator"
    MAX_LENGTH = 512
    MIN_TRAINING_DATA = 50
    
    def __init__(self, db_path: str = None, model_path: str = "models/keyword_model"):
        """
        KeywordClassifier 초기화
        
        Args:
            db_path: 데이터베이스 경로 (None이면 환경변수에서 로드)
            model_path: 모델 저장 경로
        """
        self.db_path = db_path or os.getenv('DB_PATH')
        self.model_path = model_path
        self.tokenizer = None
        self.model = None
        self.label_map = None
        self.reverse_label_map = None
        
        # 모델 저장 디렉토리 생성
        os.makedirs(model_path, exist_ok=True)
        
        logger.info(f"KeywordClassifier 초기화 완료 - DB: {self.db_path}, 모델경로: {model_path}")
    
    def get_db_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def load_training_data(self) -> pd.DataFrame:
        """
        classification_logs에서 키워드 분류 학습 데이터 로드
        
        Returns:
            pd.DataFrame: 키워드별 분류 학습 데이터
        """
        try:
            logger.info(f"키워드 학습 데이터 로드 시작 - DB 경로: {self.db_path}")
            
            if not os.path.exists(self.db_path):
                logger.error(f"데이터베이스 파일이 존재하지 않습니다: {self.db_path}")
                return pd.DataFrame()
            
            conn = self.get_db_connection()
            
            # 키워드가 있는 분류 로그에서 학습 데이터 추출
            query = """
                SELECT title, content, keyword
                FROM classification_logs
                WHERE keyword IS NOT NULL AND keyword != ''
                ORDER BY created_at DESC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) == 0:
                logger.warning("키워드 학습 데이터가 없습니다.")
                return df
            
            # 동적 라벨 인코딩 (키워드별로 자동 생성)
            keywords = sorted(df['keyword'].unique())
            self.label_map = {k: i for i, k in enumerate(keywords)}
            self.reverse_label_map = {i: k for k, i in self.label_map.items()}
            df['label'] = df['keyword'].map(self.label_map)
            
            logger.info(f"로드된 키워드 학습 데이터: {len(df)}개")
            logger.info(f"키워드 종류: {len(keywords)}개 - {keywords}")
            
            return df
            
        except Exception as e:
            logger.error(f"키워드 데이터 로드 중 오류: {e}")
            return pd.DataFrame()
    
    def preprocess_text(self, title: str, content: str) -> str:
        """
        텍스트 전처리 - 제목과 본문을 결합하여 모델 입력용 텍스트 생성
        
        Args:
            title: 기사 제목
            content: 기사 본문
            
        Returns:
            str: 전처리된 텍스트
        """
        text = f"제목: {title} 내용: {content}"
        return text.strip()
    
    def create_dataset(self, texts: List[str], labels: List[int]) -> Dataset:
        """
        텍스트와 라벨로부터 HuggingFace Dataset 생성
        
        Args:
            texts: 전처리된 텍스트 리스트
            labels: 라벨 리스트
            
        Returns:
            Dataset: 토큰화된 데이터셋
        """
        # 토큰화
        encodings = self.tokenizer(
            texts, 
            truncation=True, 
            padding=True, 
            max_length=self.MAX_LENGTH,
            return_tensors="pt"
        )
        
        # Dataset 생성
        return Dataset.from_dict({
            'input_ids': encodings['input_ids'],
            'attention_mask': encodings['attention_mask'],
            'labels': labels
        })
    
    def train_koelectra_model(self, df: pd.DataFrame) -> Dict:
        """
        KoELECTRA 모델 학습
        
        Args:
            df: 학습 데이터 DataFrame
            
        Returns:
            Dict: 학습 결과 정보
        """
        logger.info("키워드 분류 KoELECTRA 모델 학습 시작")
        
        try:
            # 토크나이저와 모델 로드
            logger.info(f"모델 로드 중: {self.MODEL_NAME}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME,
                num_labels=len(self.label_map)
            )
            
            # 데이터 전처리
            logger.info("데이터 전처리 중...")
            texts = [self.preprocess_text(row['title'], row['content']) for _, row in df.iterrows()]
            labels = df['label'].tolist()
            
            # 데이터 분할 (훈련:테스트 = 8:2)
            train_texts, test_texts, train_labels, test_labels = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )
            
            logger.info(f"데이터 분할 완료 - 훈련: {len(train_texts)}개, 테스트: {len(test_texts)}개")
            
            # 데이터셋 생성
            train_dataset = self.create_dataset(train_texts, train_labels)
            test_dataset = self.create_dataset(test_texts, test_labels)
            
            # 학습 설정
            training_args = TrainingArguments(
                output_dir=f"{self.model_path}/checkpoints",
                num_train_epochs=3,
                per_device_train_batch_size=8,
                per_device_eval_batch_size=8,
                warmup_steps=500,
                weight_decay=0.01,
                logging_dir=f"{self.model_path}/logs",
                logging_steps=10,
                save_steps=1000,
                eval_steps=1000,
                evaluation_strategy="steps",
                load_best_model_at_end=True,
                metric_for_best_model="accuracy",
                save_total_limit=3  # 체크포인트 개수 제한
            )
            
            # 트레이너 생성 및 학습
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=test_dataset
            )
            
            logger.info("모델 학습 시작...")
            trainer.train()
            
            # 모델 평가
            eval_results = trainer.evaluate()
            logger.info(f"평가 결과: {eval_results}")
            
            # 모델 저장
            self.save_model()
            
            logger.info("키워드 분류 KoELECTRA 모델 학습 완료")
            return {
                'model_type': 'koelectra_keyword',
                'eval_loss': eval_results.get('eval_loss', 0),
                'eval_accuracy': eval_results.get('eval_accuracy', 0),
                'train_samples': len(train_texts),
                'test_samples': len(test_texts),
                'num_keywords': len(self.label_map),
                'model_path': f"{self.model_path}/koelectra_keyword_model"
            }
            
        except Exception as e:
            logger.error(f"키워드 KoELECTRA 모델 학습 중 오류: {e}")
            return {'error': str(e)}
    
    def predict(self, title: str, content: str) -> Dict:
        """
        키워드 분류 예측
        
        Args:
            title: 기사 제목
            content: 기사 본문
            
        Returns:
            Dict: 분류 결과 (키워드, 신뢰도, 확률 분포)
        """
        try:
            if not self.model or not self.tokenizer:
                raise ValueError("모델이 로드되지 않았습니다. 먼저 모델을 로드하세요.")
            
            # 텍스트 전처리
            text = self.preprocess_text(title, content)
            
            # 토큰화
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=self.MAX_LENGTH
            )
            
            # 예측
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=1)
                prediction_idx = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][prediction_idx].item()
            
            prediction = self.reverse_label_map[prediction_idx]
            
            # 모든 키워드에 대한 확률 계산
            probabilities_dict = {
                self.reverse_label_map[i]: float(probabilities[0][i].item()) 
                for i in range(len(self.reverse_label_map))
            }
            
            return {
                'keyword': prediction,
                'confidence': float(confidence),
                'model_type': 'koelectra_keyword',
                'probabilities': probabilities_dict
            }
            
        except Exception as e:
            logger.error(f"키워드 예측 중 오류: {e}")
            return {
                'keyword': None,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def save_model(self) -> bool:
        """
        키워드 분류 모델 저장
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            if not self.model or not self.tokenizer:
                logger.error("저장할 모델이 없습니다.")
                return False
            
            model_save_path = f"{self.model_path}/koelectra_keyword_model"
            
            # 모델과 토크나이저 저장
            self.model.save_pretrained(model_save_path)
            self.tokenizer.save_pretrained(model_save_path)
            
            # 라벨 매핑 저장
            label_mapping_path = f"{self.model_path}/label_mapping.json"
            with open(label_mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.label_map, f, ensure_ascii=False, indent=2)
            
            logger.info(f"키워드 분류 모델 저장 완료: {model_save_path}")
            return True
            
        except Exception as e:
            logger.error(f"키워드 분류 모델 저장 중 오류: {e}")
            return False
    
    def load_model(self) -> bool:
        """
        키워드 분류 모델 로드
        
        Returns:
            bool: 로드 성공 여부
        """
        try:
            model_path = f"{self.model_path}/koelectra_keyword_model"
            
            if not os.path.exists(model_path):
                logger.warning(f"모델 파일이 존재하지 않습니다: {model_path}")
                return False
            
            # 모델과 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            
            # 라벨 매핑 로드
            label_mapping_path = f"{self.model_path}/label_mapping.json"
            if os.path.exists(label_mapping_path):
                with open(label_mapping_path, 'r', encoding='utf-8') as f:
                    self.label_map = json.load(f)
                    self.reverse_label_map = {v: k for k, v in self.label_map.items()}
            
            logger.info("키워드 분류 모델 로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"키워드 분류 모델 로드 중 오류: {e}")
            return False
    
    def evaluate_model(self, test_data: pd.DataFrame) -> Dict:
        """
        모델 성능 평가
        
        Args:
            test_data: 테스트 데이터 DataFrame
            
        Returns:
            Dict: 평가 결과 (정확도, 분류 리포트, 예측 결과 등)
        """
        try:
            if not self.model:
                raise ValueError("평가할 모델이 로드되지 않았습니다.")
            
            logger.info(f"모델 평가 시작 - 테스트 데이터: {len(test_data)}개")
            
            predictions = []
            actuals = []
            confidences = []
            
            for _, row in test_data.iterrows():
                result = self.predict(row['title'], row['content'])
                predictions.append(result['keyword'])
                actuals.append(row['keyword'])
                confidences.append(result['confidence'])
            
            accuracy = accuracy_score(actuals, predictions)
            
            logger.info(f"모델 평가 완료 - 정확도: {accuracy:.4f}")
            
            return {
                'accuracy': accuracy,
                'classification_report': classification_report(actuals, predictions),
                'predictions': predictions,
                'actuals': actuals,
                'avg_confidence': np.mean(confidences),
                'test_samples': len(test_data)
            }
            
        except Exception as e:
            logger.error(f"키워드 분류 모델 평가 중 오류: {e}")
            return {'error': str(e)}
    
    def get_model_info(self) -> Dict:
        """
        모델 정보 조회
        
        Returns:
            Dict: 모델 정보 (존재 여부, 경로, 크기, 라벨 매핑 등)
        """
        try:
            model_path = f"{self.model_path}/koelectra_keyword_model"
            model_exists = os.path.exists(model_path)
            
            info = {
                'model_type': 'koelectra_keyword',
                'model_exists': model_exists,
                'model_path': model_path,
                'label_mapping': self.label_map,
                'model_loaded': self.model is not None,
                'num_keywords': len(self.label_map) if self.label_map else 0
            }
            
            if model_exists:
                # 모델 파일 크기 계산
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(model_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                
                info['model_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            return info
            
        except Exception as e:
            logger.error(f"키워드 분류 모델 정보 조회 중 오류: {e}")
            return {'error': str(e)}

def main():
    """
    메인 실행 함수 - 키워드 분류 모델 학습 및 테스트
    """
    logger.info("=== 키워드 분류기 실행 시작 ===")
    
    # 분류기 초기화
    classifier = KeywordClassifier()
    
    # 학습 데이터 로드
    df = classifier.load_training_data()
    
    if len(df) < classifier.MIN_TRAINING_DATA:
        logger.warning(f"키워드 학습 데이터가 부족합니다. 최소 {classifier.MIN_TRAINING_DATA}개 이상 필요합니다.")
        return
    
    # KoELECTRA 모델 학습
    results = classifier.train_koelectra_model(df)
    
    if 'error' in results:
        logger.error(f"모델 학습 실패: {results['error']}")
    else:
        logger.info(f"모델 학습 성공: {results}")
    
    logger.info("=== 키워드 분류기 실행 완료 ===")

if __name__ == "__main__":
    main() 