import os
import sqlite3
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class HardcodeMLBClassifier:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 환경변수에서 DB 경로 가져오기
            db_path = os.getenv('DATABASE_PATH')
            if not db_path:
                # 환경변수가 없으면 기본 경로 사용
                script_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(script_dir, "..", "src", "database", "db.sqlite")
        
        self.db_path = db_path
        print(f"DB 경로: {self.db_path}")

    def classify_mlb_articles(self) -> List[Dict]:
        """MLB 그룹의 모든 기사를 '해당없음'으로 분류하여 저장합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # MLB 그룹의 모든 기사 조회
            cursor.execute("""
                SELECT id, title, url, keyword, group_name, content, created_at, pub_date
                FROM articles 
                WHERE group_name = 'MLB'
                ORDER BY created_at DESC 
            """)
            articles = cursor.fetchall()
            
            print(f"MLB 그룹에서 {len(articles)}개의 기사를 찾았습니다.")
            
            classification_results = []
            processed_count = 0
            skipped_count = 0
            
            for article in articles:
                article_id, title, url, keyword, group_name, content, created_at, pub_date = article
                
                # url + 키워드 중복 체크
                cursor.execute("SELECT COUNT(*) FROM classification_logs WHERE url = ? AND keyword = ?", (url, keyword))
                if cursor.fetchone()[0] > 0:
                    print(f"⚠️ 이미 저장된 url({url}) + 키워드({keyword})이므로 건너뜁니다.")
                    skipped_count += 1
                    continue
                
                # 하드코딩된 분류 결과
                result = {
                    'classification': '해당없음',
                    'confidence': 1.0,
                    'reason': 'MLB 패션 브랜드 관련 기사가 아닌 야구 스포츠 관련 기사이기 때문에 해당없음으로 분류'
                }
                
                # classification_logs에 저장
                cursor.execute("""
                    INSERT INTO classification_logs 
                    (keyword, group_name, title, content, url, classification_result, confidence_score, reason, processing_time, created_at, is_saved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    keyword, 
                    group_name,
                    title,
                    content,
                    url,
                    result['classification'], 
                    result['confidence'],
                    result['reason'],
                    0.0,  # 처리시간 0초 (하드코딩이므로)
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    0  # is_saved 기본값
                ))
                
                print(f"  제목: {title[:50]}...")
                print(f"  분류: {result['classification']}")
                print(f"  신뢰도: {result['confidence']:.2f}")
                print(f"  근거: {result['reason']}")
                print()
                
                classification_results.append({
                    'group_name': group_name,
                    'title': title,
                    'content': content,
                    'url': url,
                    'classification_result': result['classification'],
                    'is_saved': 0,
                    'confidence_score': result['confidence'],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'processing_time': 0.0,
                    'reason': result['reason']
                })
                
                processed_count += 1
            
            conn.commit()
            conn.close()
            
            print(f"\n=== MLB 그룹 분류 완료 ===")
            print(f"처리된 기사: {processed_count}개")
            print(f"건너뛴 기사: {skipped_count}개 (이미 분류됨)")
            print(f"총 기사: {len(articles)}개")
            
            return classification_results
            
        except Exception as e:
            print(f"MLB 기사 분류 중 오류: {e}")
            return []

    def get_mlb_classification_stats(self) -> Dict:
        """MLB 그룹의 분류 통계를 조회합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # MLB 그룹의 분류 통계
            cursor.execute("""
                SELECT classification_result, COUNT(*) as count, AVG(confidence_score) as avg_confidence
                FROM classification_logs 
                WHERE group_name = 'MLB'
                GROUP BY classification_result
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            stats = {}
            for classification, count, avg_confidence in results:
                stats[classification] = {
                    'count': count,
                    'avg_confidence': round(avg_confidence, 2) if avg_confidence else 0
                }
            
            return stats
            
        except Exception as e:
            print(f"MLB 통계 조회 중 오류: {e}")
            return {}

def main():
    """메인 실행 함수 - MLB 그룹 기사 하드코딩 분류"""
    classifier = HardcodeMLBClassifier()
    
    print("MLB 그룹 기사 하드코딩 분류를 시작합니다...")
    print("=" * 50)
    
    # MLB 그룹 기사 분류
    results = classifier.classify_mlb_articles()
    
    if results:
        print(f"\nMLB 그룹 분류 완료: {len(results)}개 기사 처리")
        
        # 분류 통계 출력
        stats = classifier.get_mlb_classification_stats()
        print(f"\nMLB 그룹 분류 통계:")
        for classification, data in stats.items():
            print(f"  {classification}: {data['count']}개 (평균 신뢰도: {data['avg_confidence']})")
    else:
        print("\nMLB 그룹에 대한 분류할 기사가 없습니다.")

if __name__ == "__main__":
    main() 