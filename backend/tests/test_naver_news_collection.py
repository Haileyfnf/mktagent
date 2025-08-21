import requests
import json
import sqlite3
import os
from datetime import datetime, timedelta
import time

# 환경 변수에서 API 키 가져오기
NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET')

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(__file__), '../src/database/db.sqlite')

def get_active_keywords_from_db():
    """데이터베이스에서 활성화된 키워드 목록 가져오기"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT keyword, group_name, type 
            FROM keywords 
            WHERE is_active = 1 
            ORDER BY keyword
        """)
        
        keywords = cursor.fetchall()
        conn.close()
        
        if keywords:
            print(f"📋 활성화된 키워드 {len(keywords)}개:")
            for keyword in keywords:
                print(f"  - {keyword['keyword']} ({keyword['type']}, 그룹: {keyword['group_name']})")
        
        return [keyword['keyword'] for keyword in keywords]
        
    except Exception as e:
        print(f"❌ 키워드 조회 오류: {e}")
        return []

def test_naver_news_search_with_date():
    """날짜를 지정한 네이버 뉴스 검색 테스트"""
    print("=== 날짜 지정 네이버 뉴스 검색 테스트 ===")
    
    # 데이터베이스에서 활성화된 키워드 가져오기
    test_keywords = get_active_keywords_from_db()
    
    if not test_keywords:
        print("❌ 활성화된 키워드가 없습니다.")
        print("먼저 키워드를 등록해주세요.")
        return
    
    # 날짜 범위 설정 (2025-06-01 ~ 2025-07-04)
    start_date = datetime(2025, 6, 1)
    end_date = datetime(2025, 7, 4)
    
    print(f"검색 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"테스트 키워드: {test_keywords}")
    print("-" * 60)
    
    total_articles = 0
    saved_articles = 0
    
    for keyword in test_keywords:
        print(f"\n🔍 키워드 '{keyword}' 검색 중...")
        
        try:
            # 네이버 뉴스 API 호출
            url = 'https://openapi.naver.com/v1/search/news.json'
            headers = {
                'X-Naver-Client-Id': NAVER_CLIENT_ID,
                'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
            }
            params = {
                'query': keyword,
                'display': 20,  # 한 번에 20개씩
                'start': 1,
                'sort': 'date'  # 날짜순 정렬
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('items', [])
                
                print(f"  📊 검색 결과: {len(articles)}개 기사")
                total_articles += len(articles)
                
                # 각 기사 처리
                keyword_saved = 0
                for i, article in enumerate(articles, 1):
                    # 발행일 파싱
                    pub_date_str = article.get('pubDate', '')
                    if pub_date_str:
                        try:
                            # 네이버 API 날짜 형식: "Mon, 18 Dec 2023 10:30:00 +0900"
                            pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                            pub_date_local = pub_date.replace(tzinfo=None)
                            
                            # 날짜 범위 체크
                            if start_date <= pub_date_local <= end_date:
                                print(f"    📅 기사 {i}: {pub_date_local.strftime('%Y-%m-%d %H:%M')} - {article.get('title', '')[:50]}...")
                                
                                # DB에 저장
                                if save_article_to_db(article, keyword):
                                    keyword_saved += 1
                                    saved_articles += 1
                            else:
                                print(f"    ⏰ 기사 {i}: 날짜 범위 외 ({pub_date_local.strftime('%Y-%m-%d')})")
                                
                        except ValueError as e:
                            print(f"    ❌ 기사 {i}: 날짜 파싱 오류 - {e}")
                    else:
                        print(f"    ❌ 기사 {i}: 발행일 정보 없음")
                
                print(f"  💾 저장된 기사: {keyword_saved}개")
                
            else:
                print(f"  ❌ API 호출 실패: {response.status_code}")
                print(f"  에러: {response.text}")
                
        except Exception as e:
            print(f"  ❌ 키워드 '{keyword}' 처리 중 오류: {e}")
        
        # API 호출 간격 조절 (네이버 API 제한 고려)
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("📈 테스트 결과 요약:")
    print(f"  총 검색된 기사: {total_articles}개")
    print(f"  총 저장된 기사: {saved_articles}개")
    print(f"  저장 성공률: {(saved_articles/total_articles*100):.1f}%" if total_articles > 0 else "  저장 성공률: 0%")

def save_article_to_db(article, keyword):
    """기사를 데이터베이스에 저장"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 중복 체크 (URL 기준)
        cursor.execute("SELECT id FROM articles WHERE url = ?", (article['link'],))
        if cursor.fetchone():
            conn.close()
            return False  # 이미 저장됨
        
        # 발행일 파싱
        pub_date_str = article.get('pubDate', '')
        if pub_date_str:
            try:
                pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                pub_date_formatted = pub_date.strftime('%Y-%m-%d')
            except ValueError:
                pub_date_formatted = datetime.now().strftime('%Y-%m-%d')
        else:
            pub_date_formatted = datetime.now().strftime('%Y-%m-%d')
        
        # 기사 저장
        cursor.execute("""
            INSERT INTO articles (keyword, title, press, pub_date, content, url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            keyword,
            article.get('title', ''),
            article.get('originallink', ''),
            pub_date_formatted,
            article.get('description', ''),
            article.get('link', '')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"    ❌ DB 저장 오류: {e}")
        return False

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("=== 데이터베이스 연결 테스트 ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 테이블 존재 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        if cursor.fetchone():
            print("✅ articles 테이블 존재")
        else:
            print("❌ articles 테이블 없음")
            return False
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keywords'")
        if cursor.fetchone():
            print("✅ keywords 테이블 존재")
        else:
            print("❌ keywords 테이블 없음")
            return False
        
        # 기존 기사 수 확인
        cursor.execute("SELECT COUNT(*) FROM articles")
        existing_articles = cursor.fetchone()[0]
        print(f"📊 기존 기사 수: {existing_articles}개")
        
        # 활성화된 키워드 수 확인
        cursor.execute("SELECT COUNT(*) FROM keywords WHERE is_active = 1")
        active_keywords = cursor.fetchone()[0]
        print(f"📋 활성화된 키워드 수: {active_keywords}개")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 오류: {e}")
        return False

def show_saved_articles():
    """저장된 기사 확인"""
    print("\n=== 저장된 기사 확인 ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 최근 저장된 기사 10개 조회
        cursor.execute("""
            SELECT keyword, title, pub_date, press, url 
            FROM articles 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        articles = cursor.fetchall()
        
        if articles:
            print(f"📰 최근 저장된 기사 {len(articles)}개:")
            for i, article in enumerate(articles, 1):
                print(f"\n{i}. {article['keyword']} - {article['pub_date']}")
                print(f"   제목: {article['title'][:60]}...")
                print(f"   언론사: {article['press']}")
                print(f"   URL: {article['url']}")
        else:
            print("📭 저장된 기사가 없습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 기사 조회 오류: {e}")

def show_keyword_collection_stats():
    """키워드별 수집 통계 확인"""
    print("\n=== 키워드별 수집 통계 ===")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 키워드별 기사 수 집계
        cursor.execute("""
            SELECT 
                keyword,
                COUNT(*) as article_count,
                MIN(pub_date) as first_article,
                MAX(pub_date) as last_article
            FROM articles 
            GROUP BY keyword 
            ORDER BY article_count DESC
        """)
        
        stats = cursor.fetchall()
        
        if stats:
            print(f"📊 키워드별 기사 수집 현황:")
            for stat in stats:
                print(f"\n  🔍 {stat['keyword']}:")
                print(f"     📰 총 기사 수: {stat['article_count']}개")
                print(f"     📅 첫 기사: {stat['first_article']}")
                print(f"     📅 최근 기사: {stat['last_article']}")
        else:
            print("📭 수집된 기사가 없습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 통계 조회 오류: {e}")

if __name__ == "__main__":
    print("🚀 네이버 뉴스 수집 테스트 시작")
    print(f"📅 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # API 키 확인
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키가 설정되지 않았습니다.")
        print("환경 변수 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요.")
        exit(1)
    
    # 데이터베이스 연결 테스트
    if not test_database_connection():
        print("❌ 데이터베이스 연결 실패. 테스트를 중단합니다.")
        exit(1)
    
    # 네이버 뉴스 수집 테스트
    test_naver_news_search_with_date()
    
    # 저장된 기사 확인
    show_saved_articles()
    
    # 키워드별 수집 통계
    show_keyword_collection_stats()
    
    print("\n✅ 테스트 완료!") 