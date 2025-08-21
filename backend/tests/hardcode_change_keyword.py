import os
import sqlite3
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class HardcodeMLBToFF:
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

    def update_mlb_to_ff(self) -> Dict:
        """제목에 F&F가 포함된 기사들의 키워드와 그룹명을 F&F로 수정합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 제목에 'F&F'가 포함된 기사들 조회
            cursor.execute("""
                SELECT id, title, url, keyword, group_name, content, created_at, pub_date
                FROM articles 
                WHERE title LIKE '%F&F%'
            """)
            
            articles = cursor.fetchall()
            
            if not articles:
                print("❌ 제목에 'F&F'가 포함된 기사를 찾을 수 없습니다.")
                return {}
            
            print(f"제목에 'F&F'가 포함된 기사 {len(articles)}개를 찾았습니다.")
            print()
            
            updated_count = 0
            updated_articles = []
            
            for article in articles:
                article_id, title, url, keyword, group_name, content, created_at, pub_date = article
                
                # 이미 F&F로 설정되어 있는지 확인
                if keyword == "F&F" and group_name == "F&F":
                    print(f"⏭️  이미 F&F로 설정됨: {title[:50]}...")
                    continue
                
                print(f"기사 정보:")
                print(f"  ID: {article_id}")
                print(f"  제목: {title}")
                print(f"  URL: {url}")
                print(f"  현재 키워드: {keyword}")
                print(f"  현재 그룹: {group_name}")
                print()
                
                # 키워드와 그룹명 수정
                new_keyword = "F&F"
                new_group_name = "F&F"
                
                # articles 테이블 업데이트
                cursor.execute("""
                    UPDATE articles 
                    SET keyword = ?, group_name = ?
                    WHERE id = ?
                """, (new_keyword, new_group_name, article_id))
                
                # classification_logs에서도 해당 기사 삭제 (새로운 키워드로 재분류 필요)
                cursor.execute("""
                    DELETE FROM classification_logs 
                    WHERE url = ?
                """, (url,))
                
                updated_count += 1
                updated_articles.append({
                    'article_id': article_id,
                    'title': title,
                    'url': url,
                    'old_keyword': keyword,
                    'new_keyword': new_keyword,
                    'old_group': group_name,
                    'new_group': new_group_name
                })
                
                print(f"✅ 업데이트 완료!")
                print(f"  키워드: {keyword} → {new_keyword}")
                print(f"  그룹명: {group_name} → {new_group_name}")
                print(f"  분류 로그 삭제: 기존 분류 결과 삭제됨")
                print("-" * 50)
            
            conn.commit()
            conn.close()
            
            print(f"\n📊 전체 업데이트 결과:")
            print(f"  총 기사 수: {len(articles)}개")
            print(f"  업데이트된 기사 수: {updated_count}개")
            print(f"  이미 F&F로 설정된 기사 수: {len(articles) - updated_count}개")
            
            return {
                'total_articles': len(articles),
                'updated_count': updated_count,
                'updated_articles': updated_articles,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ 업데이트 중 오류: {e}")
            return {}

    def classify_as_organic(self, keyword: str, title: str, content: str, url: str, group_name: str) -> Dict:
        """기사를 오가닉으로 하드코딩 분류합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 하드코딩된 분류 결과
            result = {
                'classification': '오가닉',
                'confidence': 1.0,
                'reason': "'MLB'키워드가 본문에 포함되고 있지만 결국엔 해당 브랜드를 소유하고 있는 F&F 기업의 실적 전망에 대한 기사라서 MLB 키워드가 아니라 F&F로 분류되어야함."
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
            
            conn.commit()
            conn.close()
            
            print(f"✅ 분류 완료!")
            print(f"  분류: {result['classification']}")
            print(f"  신뢰도: {result['confidence']:.2f}")
            print(f"  근거: {result['reason']}")
            
            return result
            
        except Exception as e:
            print(f"❌ 분류 중 오류: {e}")
            return {}

    def verify_update(self) -> bool:
        """업데이트가 성공적으로 되었는지 확인합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 제목에 'F&F'가 포함된 기사들 조회
            cursor.execute("""
                SELECT id, title, url, keyword, group_name
                FROM articles 
                WHERE title LIKE '%F&F%'
            """)
            
            articles = cursor.fetchall()
            
            if not articles:
                print("❌ articles에서 기사를 찾을 수 없습니다.")
                conn.close()
                return False
                
            print(f"\n🔍 articles 테이블 확인:")
            print(f"  총 기사 수: {len(articles)}개")
            
            # 모든 기사가 F&F로 업데이트되었는지 확인
            all_updated = True
            for article in articles:
                article_id, title, url, keyword, group_name = article
                print(f"\n🔍 기사 확인:")
                print(f"  제목: {title}")
                print(f"  현재 키워드: {keyword}")
                print(f"  현재 그룹: {group_name}")
                
                if keyword != "F&F" or group_name != "F&F":
                    print("❌ 아직 F&F로 업데이트되지 않았습니다.")
                    all_updated = False
                else:
                    print("✅ F&F로 정상 업데이트됨")
                
                print("-" * 50)
            
            if all_updated:
                print("✅ 모든 기사가 F&F로 성공적으로 업데이트되었습니다!")
                conn.close()
                return True
            else:
                print("❌ 일부 기사가 아직 F&F로 업데이트되지 않았습니다.")
                conn.close()
                return False
                
        except Exception as e:
            print(f"❌ 확인 중 오류: {e}")
            return False

def main():
    """메인 실행 함수 - 제목에 F&F가 포함된 기사들의 키워드/그룹명을 F&F로 수정"""
    updater = HardcodeMLBToFF()
    
    print("제목에 'F&F'가 포함된 기사들의 키워드/그룹명을 F&F로 수정합니다...")
    print("=" * 70)
    
    # 업데이트 실행
    result = updater.update_mlb_to_ff()
    
    if result:
        print(f"\n📋 수정 사유:")
        print("제목에 'F&F'가 포함된 기사들은 해당 브랜드와 관련된 기사이므로")
        print("키워드와 그룹명을 'F&F'로 통일하여 분류의 일관성을 확보합니다.")
        
        # 업데이트 확인
        print(f"\n{'='*70}")
        updater.verify_update()
    else:
        print("\n❌ 업데이트에 실패했습니다.")

if __name__ == "__main__":
    main() 