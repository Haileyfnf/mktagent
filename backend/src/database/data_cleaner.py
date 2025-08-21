import sqlite3
import re
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = 'c:/Users/haenee/mkt_ai_agent/backend/src/database/db.sqlite'

# 공통 정제 패턴들
NEWS_PATTERNS = [
    r'\(서울=뉴스1\)',
    r'\(무단전재\)',
    r'\(종합\)',
    r'\(기사\)',
    r'\(사진\)',
    r'\(영상\)',
    r'\(인터뷰\)',
    r'\(단독\)',
    r'\(속보\)',
    r'\(업데이트\)',
    r'\(수정\)',
    r'\(추가\)',
]

SPECIAL_CHARS = r'[★☆◆◇■□●○◎※→←↑↓↔⇒⇐⇑⇓⇔]'

def get_db_connection():
    """데이터베이스 연결 반환"""
    return sqlite3.connect(DB_PATH)

def clean_whitespace(text):
    """연속된 공백 정리"""
    if not text:
        return text
    return re.sub(r'\s+', ' ', text).strip()

def update_article_content(conn, article_id, content, cleaned_content, operation_name):
    """기사 내용 업데이트 공통 함수"""
    if cleaned_content != content:
        conn.cursor().execute("UPDATE articles SET content = ? WHERE id = ?", (cleaned_content, article_id))
        logger.info(f"{operation_name} 완료 (ID: {article_id})")
        return True
    return False

def clean_nbsp_content():
    """content 칼럼에서 NBSP 제거"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # NBSP가 포함된 기사 수 확인
    c.execute("SELECT COUNT(*) FROM articles WHERE content LIKE '%&nbsp;%' OR content LIKE '%\xa0%'")
    nbsp_count = c.fetchone()[0]
    logger.info(f"NBSP가 포함된 기사 수: {nbsp_count}개")
    
    if nbsp_count > 0:
        # NBSP 제거
        c.execute("""
            UPDATE articles 
            SET content = REPLACE(REPLACE(content, '&nbsp;', ' '), '\xa0', ' ')
            WHERE content LIKE '%&nbsp;%' OR content LIKE '%\xa0%'
        """)
        
        # 연속된 공백 정리
        c.execute("""
            UPDATE articles 
            SET content = TRIM(REPLACE(REPLACE(REPLACE(content, '  ', ' '), '  ', ' '), '  ', ' '))
            WHERE content LIKE '%  %'
        """)
        
        conn.commit()
        logger.info("NBSP 제거 완료")
    
    conn.close()

def clean_title_zwnbsp():
    """title 칼럼에서 ZWNBSP 제거"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # ZWNBSP가 포함된 제목 수 확인
    c.execute("SELECT COUNT(*) FROM articles WHERE title LIKE '%\uFEFF%'")
    zwnbsp_count = c.fetchone()[0]
    logger.info(f"ZWNBSP가 포함된 제목 수: {zwnbsp_count}개")
    
    if zwnbsp_count > 0:
        # ZWNBSP 제거
        c.execute("""
            UPDATE articles 
            SET title = REPLACE(title, '\uFEFF', '')
            WHERE title LIKE '%\uFEFF%'
        """)
        
        # 연속된 공백 정리
        c.execute("""
            UPDATE articles 
            SET title = TRIM(REPLACE(REPLACE(REPLACE(title, '  ', ' '), '  ', ' '), '  ', ' '))
            WHERE title LIKE '%  %'
        """)
        
        conn.commit()
        logger.info("title ZWNBSP 제거 완료")
    
    conn.close()

def clean_press_domain():
    """press 칼럼에서 도메인만 추출하여 정제"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 현재 press 데이터 확인
    c.execute("SELECT DISTINCT press FROM articles WHERE press IS NOT NULL AND press != ''")
    current_presses = [row[0] for row in c.fetchall()]
    logger.info(f"현재 언론사 목록: {current_presses}")
    
    # 도메인 정제 함수
    def extract_domain(url):
        if not url:
            return ""
        
        # www. 제거
        domain = url.replace('www.', '')
        
        # .co.kr, .com, .net 등 제거
        domain = re.sub(r'\.(co\.kr|com|net|org|kr)$', '', domain)
        
        # 추가 도메인 확장자 제거
        domain = re.sub(r'\.(info|biz|edu|gov|mil|int)$', '', domain)
        
        return domain.strip()
    
    # 각 기사별로 press 정제
    c.execute("SELECT id, press FROM articles WHERE press IS NOT NULL AND press != ''")
    articles = c.fetchall()
    
    updated_count = 0
    for article_id, press in articles:
        cleaned_press = extract_domain(press)
        if cleaned_press != press:
            c.execute("UPDATE articles SET press = ? WHERE id = ?", (cleaned_press, article_id))
            updated_count += 1
            logger.info(f"언론사 정제: {press} -> {cleaned_press}")
    
    conn.commit()
    logger.info(f"언론사 도메인 정제 완료: {updated_count}개 업데이트")
    
    # 정제 후 언론사 목록 확인
    c.execute("SELECT DISTINCT press FROM articles WHERE press IS NOT NULL AND press != '' ORDER BY press")
    cleaned_presses = [row[0] for row in c.fetchall()]
    logger.info(f"정제 후 언론사 목록: {cleaned_presses}")
    
    conn.close()

def convert_date_format():
    """pub_date와 created_at 칼럼을 yyyy-mm-dd HH:MM:SS 형식으로 변환"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # pub_date 변환
    c.execute("SELECT id, pub_date FROM articles WHERE pub_date IS NOT NULL AND pub_date != ''")
    pub_dates = c.fetchall()
    
    updated_pub_count = 0
    for article_id, pub_date in pub_dates:
        try:
            if pub_date and isinstance(pub_date, str):
                # 이미 올바른 형식인지 확인 (yyyy-mm-dd HH:MM:SS)
                if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', pub_date):
                    continue  # 이미 올바른 형식이면 건너뛰기
                
                # 다양한 날짜 형식 처리
                date_formats = [
                    "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
                    "%Y-%m-%d %H:%M:%S",         # ISO 형식
                    "%Y-%m-%d",                  # 날짜만
                    "%d %b %Y %H:%M:%S",         # 시간대 없음
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(pub_date, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("UPDATE articles SET pub_date = ? WHERE id = ?", (formatted_date, article_id))
                    updated_pub_count += 1
                    logger.info(f"pub_date 변환: {pub_date} -> {formatted_date}")
                else:
                    logger.warning(f"날짜 형식 파싱 실패: {pub_date}")
                    
        except Exception as e:
            logger.error(f"pub_date 변환 오류 (ID: {article_id}): {e}")
    
    # created_at 변환 (SQLite datetime을 표준 형식으로)
    c.execute("""
        UPDATE articles 
        SET created_at = strftime('%Y-%m-%d %H:%M:%S', created_at)
        WHERE created_at IS NOT NULL
    """)
    
    conn.commit()
    logger.info(f"날짜 형식 변환 완료: pub_date {updated_pub_count}개 업데이트")
    
    conn.close()

def clean_classification_logs_dates():
    """classification_logs 테이블의 created_at 칼럼을 yyyy-mm-dd HH:MM:SS 형식으로 정제"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # classification_logs 테이블 존재 확인
        c.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='classification_logs'
        """)
        
        if not c.fetchone():
            logger.warning("classification_logs 테이블이 존재하지 않습니다.")
            return
        
        # 현재 created_at 데이터 샘플 확인
        c.execute("""
            SELECT created_at, COUNT(*) as count 
            FROM classification_logs 
            WHERE created_at IS NOT NULL 
            GROUP BY created_at 
            ORDER BY count DESC 
            LIMIT 10
        """)
        
        current_formats = c.fetchall()
        logger.info("현재 created_at 형식 샘플:")
        for date_format, count in current_formats:
            logger.info(f"  {date_format}: {count}개")
        
        # 다양한 날짜 형식 처리
        date_formats = [
            "%Y-%m-%dT%H:%M:%S.%f",  # 2025-07-23T10:54:29.732630
            "%Y-%m-%d %H:%M:%S",     # 2025-07-21 15:25:53
            "%Y-%m-%dT%H:%M:%S",     # 2025-07-23T10:54:29
            "%Y-%m-%d",              # 날짜만
            "%d/%m/%Y %H:%M:%S",     # 다른 형식들
            "%m/%d/%Y %H:%M:%S",
        ]
        
        # 모든 created_at 데이터 가져오기
        c.execute("SELECT rowid, created_at FROM classification_logs WHERE created_at IS NOT NULL")
        all_dates = c.fetchall()
        
        updated_count = 0
        failed_count = 0
        
        for rowid, date_str in all_dates:
            try:
                if not date_str or date_str == '':
                    continue
                
                # 이미 올바른 형식인지 확인
                if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', date_str):
                    continue
                
                # 다양한 형식으로 파싱 시도
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    # 표준 형식으로 변환
                    formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 업데이트
                    c.execute("""
                        UPDATE classification_logs 
                        SET created_at = ? 
                        WHERE rowid = ?
                    """, (formatted_date, rowid))
                    
                    updated_count += 1
                    logger.info(f"날짜 변환: {date_str} -> {formatted_date}")
                else:
                    failed_count += 1
                    logger.warning(f"날짜 형식 파싱 실패: {date_str}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"날짜 변환 오류 (rowid: {rowid}): {e}")
        
        conn.commit()
        
        logger.info(f"classification_logs 날짜 정제 완료:")
        logger.info(f"  - 업데이트된 레코드: {updated_count}개")
        logger.info(f"  - 실패한 레코드: {failed_count}개")
        
        # 정제 후 결과 확인
        c.execute("""
            SELECT created_at, COUNT(*) as count 
            FROM classification_logs 
            WHERE created_at IS NOT NULL 
            GROUP BY created_at 
            ORDER BY count DESC 
            LIMIT 5
        """)
        
        cleaned_formats = c.fetchall()
        logger.info("정제 후 created_at 형식 샘플:")
        for date_format, count in cleaned_formats:
            logger.info(f"  {date_format}: {count}개")
        
    except Exception as e:
        logger.error(f"classification_logs 날짜 정제 중 오류: {e}")
        conn.rollback()
    finally:
        conn.close()

def clean_classification_logs_data():
    """classification_logs 테이블 전체 데이터 정제"""
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # 테이블 존재 확인
        c.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='classification_logs'
        """)
        
        if not c.fetchone():
            logger.warning("classification_logs 테이블이 존재하지 않습니다.")
            return
        
        # 테이블 현황 확인
        c.execute("SELECT COUNT(*) FROM classification_logs")
        total_count = c.fetchone()[0]
        logger.info(f"classification_logs 테이블 총 레코드: {total_count}개")
        
        # NULL 값 처리
        c.execute("""
            UPDATE classification_logs 
            SET confidence_score = 0 
            WHERE confidence_score IS NULL
        """)
        null_updated = c.rowcount
        logger.info(f"NULL confidence_score를 0으로 변경: {null_updated}개")
        
        # is_saved 칼럼 정제
        c.execute("""
            UPDATE classification_logs 
            SET is_saved = 1 
            WHERE is_saved IS NULL OR is_saved = 0
        """)
        saved_updated = c.rowcount
        logger.info(f"is_saved를 1로 설정: {saved_updated}개")
        
        # 중복 URL 제거 (가장 최근 것만 유지)
        c.execute("""
            DELETE FROM classification_logs 
            WHERE rowid NOT IN (
                SELECT MAX(rowid) 
                FROM classification_logs 
                GROUP BY url
            )
        """)
        duplicate_removed = c.rowcount
        logger.info(f"중복 URL 제거: {duplicate_removed}개")
        
        conn.commit()
        
        # 정제 후 현황
        c.execute("SELECT COUNT(*) FROM classification_logs")
        final_count = c.fetchone()[0]
        logger.info(f"정제 후 총 레코드: {final_count}개")
        
    except Exception as e:
        logger.error(f"classification_logs 데이터 정제 중 오류: {e}")
        conn.rollback()
    finally:
        conn.close()

def remove_duplicate_articles():
    """중복 기사 제거 (URL 기준)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 중복 URL 확인
    c.execute("""
        SELECT url, COUNT(*) as count 
        FROM articles 
        WHERE url IS NOT NULL AND url != ''
        GROUP BY url 
        HAVING COUNT(*) > 1
    """)
    duplicates = c.fetchall()
    
    if duplicates:
        logger.info(f"중복 URL 발견: {len(duplicates)}개")
        
        for url, count in duplicates:
            logger.info(f"중복 URL: {url} ({count}개)")
            
            # 가장 최근 기사만 남기고 나머지 삭제
            c.execute("""
                DELETE FROM articles 
                WHERE url = ? AND id NOT IN (
                    SELECT MAX(id) FROM articles WHERE url = ?
                )
            """, (url, url))
        
        conn.commit()
        logger.info("중복 기사 제거 완료")
    else:
        logger.info("중복 기사 없음")
    
    conn.close()

def clean_content_characters():
    """content 칼럼에서 한자와 불필요한 특수문자 제거"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 한자와 특수문자 제거 함수
    def remove_chinese_and_special_chars(text):
        if not text:
            return text
        
        # 한자 제거 (Unicode 범위: 4E00-9FFF)
        text = re.sub(r'[\u4e00-\u9fff]', '', text)
        
        # 불필요한 특수문자 제거
        text = re.sub(SPECIAL_CHARS, '', text)
        
        # 연속된 공백 정리
        return clean_whitespace(text)
    
    # content 정제
    c.execute("SELECT id, content FROM articles WHERE content IS NOT NULL AND content != ''")
    articles = c.fetchall()
    
    updated_count = 0
    for article_id, content in articles:
        cleaned_content = remove_chinese_and_special_chars(content)
        if update_article_content(conn, article_id, content, cleaned_content, "문자 정제"):
            updated_count += 1
    
    conn.commit()
    logger.info(f"한자/특수문자 제거 완료: {updated_count}개 업데이트")
    
    conn.close()

def clean_news_patterns():
    """뉴스 관련 패턴 제거"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 패턴 제거 함수
    def remove_news_patterns(text):
        if not text:
            return text
        
        for pattern in NEWS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 연속된 공백 정리
        return clean_whitespace(text)
    
    # content 정제
    c.execute("SELECT id, content FROM articles WHERE content IS NOT NULL AND content != ''")
    articles = c.fetchall()
    
    updated_count = 0
    for article_id, content in articles:
        cleaned_content = remove_news_patterns(content)
        if update_article_content(conn, article_id, content, cleaned_content, "뉴스 패턴 제거"):
            updated_count += 1
    
    conn.commit()
    logger.info(f"뉴스 관련 패턴 제거 완료: {updated_count}개 업데이트")
    
    conn.close()

def show_cleaning_summary():
    """정제 작업 후 통계 출력"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 전체 기사 수
    c.execute("SELECT COUNT(*) FROM articles")
    total_articles = c.fetchone()[0]
    
    # 키워드별 기사 수
    c.execute("SELECT keyword, COUNT(*) FROM articles GROUP BY keyword ORDER BY COUNT(*) DESC")
    keyword_stats = c.fetchall()
    
    # 언론사별 기사 수
    c.execute("SELECT press, COUNT(*) FROM articles WHERE press IS NOT NULL AND press != '' GROUP BY press ORDER BY COUNT(*) DESC LIMIT 10")
    press_stats = c.fetchall()
    
    logger.info("=== 데이터 정제 완료 통계 ===")
    logger.info(f"전체 기사 수: {total_articles}개")
    logger.info("키워드별 기사 수:")
    for keyword, count in keyword_stats:
        logger.info(f"  {keyword}: {count}개")
    logger.info("상위 10개 언론사:")
    for press, count in press_stats:
        logger.info(f"  {press}: {count}개")
    
    conn.close()

def remove_english_only_articles():
    """제목이 모두 영문인 기사 삭제 (한글이 하나도 없는 경우)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # articles 테이블에서 영문 제목 기사 확인 및 삭제
    logger.info("articles 테이블에서 영문 제목 기사 확인 중...")
    
    c.execute("SELECT id, title FROM articles WHERE title IS NOT NULL AND title != ''")
    articles = c.fetchall()
    
    english_articles = []
    for article_id, title in articles:
        # 한글이 하나도 없고, 영문이 포함된 경우
        if title and not re.search(r'[가-힣]', title) and re.search(r'[A-Za-z]', title):
            english_articles.append((article_id, title))
    
    logger.info(f"articles 테이블에서 영문 제목 기사 발견: {len(english_articles)}개")
    
    if english_articles:
        for article_id, title in english_articles:
            logger.info(f"영문 제목 기사 삭제 (ID: {article_id}): {title[:50]}...")
            c.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        
        conn.commit()
        logger.info(f"articles 테이블에서 영문 제목 기사 {len(english_articles)}개 삭제 완료")
    
    # classification_logs 테이블에서 영문 제목 기사 확인 및 삭제
    try:
        c.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='classification_logs'
        """)
        
        if c.fetchone():
            logger.info("classification_logs 테이블에서 영문 제목 기사 확인 중...")
            
            c.execute("SELECT id, title FROM classification_logs WHERE title IS NOT NULL AND title != ''")
            classification_logs = c.fetchall()
            
            english_classification_logs = []
            for log_id, title in classification_logs:
                # 한글이 하나도 없고, 영문이 포함된 경우
                if title and not re.search(r'[가-힣]', title) and re.search(r'[A-Za-z]', title):
                    english_classification_logs.append((log_id, title))
            
            logger.info(f"classification_logs 테이블에서 영문 제목 기사 발견: {len(english_classification_logs)}개")
            
            if english_classification_logs:
                for log_id, title in english_classification_logs:
                    logger.info(f"영문 제목 분류 로그 삭제 (ID: {log_id}): {title[:50]}...")
                    c.execute("DELETE FROM classification_logs WHERE id = ?", (log_id,))
                
                conn.commit()
                logger.info(f"classification_logs 테이블에서 영문 제목 기사 {len(english_classification_logs)}개 삭제 완료")
        else:
            logger.info("classification_logs 테이블이 존재하지 않습니다.")
    
    except Exception as e:
        logger.error(f"classification_logs 테이블 영문 기사 삭제 중 오류: {e}")
    
    conn.close()
    
    total_deleted = len(english_articles) + (len(english_classification_logs) if 'english_classification_logs' in locals() else 0)
    logger.info(f"총 영문 제목 기사 삭제 완료: {total_deleted}개")

def main():
    """데이터 정제 작업 실행"""
    logger.info("데이터 정제 작업 시작")
    
    print("\n🔧 정제 작업 선택:")
    print("1. articles 테이블 전체 정제")
    print("2. classification_logs 테이블 날짜 정제")
    print("3. classification_logs 테이블 전체 정제")
    print("4. 모든 테이블 정제")
    print("5. 영문 제목 기사 삭제")
    
    choice = input("\n🤔 선택하세요 (1-5): ").strip()
    
    try:
        if choice == "1":
            # articles 테이블만 정제
            logger.info("=== articles 테이블 정제 시작 ===")
            
            # 1. NBSP 제거
            logger.info("1. NBSP 제거 중...")
            clean_nbsp_content()
            
            # 2. title ZWNBSP 제거
            logger.info("2. title ZWNBSP 제거 중...")
            clean_title_zwnbsp()
            
            # 3. 언론사 도메인 정제
            logger.info("3. 언론사 도메인 정제 중...")
            clean_press_domain()
            
            # 4. 날짜 형식 변환
            logger.info("4. 날짜 형식 변환 중...")
            convert_date_format()
            
            # 5. 중복 기사 제거
            logger.info("5. 중복 기사 제거 중...")
            remove_duplicate_articles()
            
            # 6. 문자 정제
            logger.info("6. 문자 정제 중...")
            clean_content_characters()

            # 7. 뉴스 패턴 제거
            logger.info("7. 뉴스 패턴 제거 중...")
            clean_news_patterns()
            
            # 8. 영문 제목 기사 삭제
            logger.info("8. 영문 제목 기사 삭제 중...")
            remove_english_only_articles()
            
            # 9. 정제 결과 통계
            logger.info("9. 정제 결과 확인 중...")
            show_cleaning_summary()
            
        elif choice == "2":
            # classification_logs 날짜만 정제
            logger.info("=== classification_logs 날짜 정제 시작 ===")
            clean_classification_logs_dates()
            
        elif choice == "3":
            # classification_logs 전체 정제
            logger.info("=== classification_logs 전체 정제 시작 ===")
            clean_classification_logs_data()
            clean_classification_logs_dates()
            
        elif choice == "4":
            # 모든 테이블 정제
            logger.info("=== 모든 테이블 정제 시작 ===")
            
            # articles 테이블 정제
            logger.info("📰 articles 테이블 정제 중...")
            clean_nbsp_content()
            clean_title_zwnbsp()
            clean_press_domain()
            convert_date_format()
            remove_duplicate_articles()
            clean_content_characters()
            clean_news_patterns()
            remove_english_only_articles()
            show_cleaning_summary()
            
            # classification_logs 테이블 정제
            logger.info("📊 classification_logs 테이블 정제 중...")
            clean_classification_logs_data()
            clean_classification_logs_dates()
            
        elif choice == "5":
            # 영문 제목 기사만 삭제
            logger.info("=== 영문 제목 기사 삭제 시작 ===")
            remove_english_only_articles()
            
        else:
            logger.error("잘못된 선택입니다. 1-5 중에서 선택해주세요.")
            return
        
        logger.info("✅ 데이터 정제 작업 완료!")
        
    except Exception as e:
        logger.error(f"데이터 정제 작업 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    main() 