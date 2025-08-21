import os
import re
import html
import sqlite3
import time
from urllib.parse import urlparse, quote
from flask import Blueprint, request, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# ============================================================================
# 환경 설정
# ============================================================================

# 네이버 API 설정
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

# 데이터베이스 설정
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'db.sqlite'))

# Flask Blueprint 설정
naver_news_bp = Blueprint('naver_news', __name__)

# 디버깅을 위한 DB 경로 출력
print(f"🔍 DB 경로: {DB_PATH}")
print(f"🔍 DB 파일 존재 여부: {os.path.exists(DB_PATH)}")

DOMAIN_PRESS_MAP = {
    "joins.com": "중앙일보",
    "chosun.com": "조선일보",
    "hani.co.kr": "한겨레",
    "donga.com": "동아일보",
    "khan.co.kr": "경향신문",
    # ... 필요시 추가
}

# ============================================================================
# 데이터 정제 함수들
# ============================================================================

def clean_text(text):
    """텍스트 정제 (HTML 태그 제거, NBSP 제거, 공백 정리, psp 제거, ZWNBSP 제거)"""
    if not text:
        return ''
    # HTML 태그 제거
    text = re.sub(r'<.*?>', '', text)
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    # NBSP 및 특수 공백 문자 제거
    text = text.replace('&nbsp;', ' ').replace('\xa0', ' ')
    text = re.sub(r'[\u00A0\u200B\u200C\u200D\uFEFF]', ' ', text)
    # ZWNBSP(Zero Width No-Break Space) 제거
    text = text.replace('\uFEFF', '')
    # ZWNBSP(Zero Width No-Break Space) 추가 제거
    text = text.replace('\u2060', '')  # WORD JOINER
    text = text.replace('\u200B', '')  # ZERO WIDTH SPACE
    text = text.replace('\u200C', '')  # ZERO WIDTH NON-JOINER
    text = text.replace('\u200D', '')  # ZERO WIDTH JOINER
    # psp(대소문자 구분 없이) 모두 제거
    text = re.sub(r'psp', '', text, flags=re.IGNORECASE)
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_press_domain(press):
    """언론사 도메인에서 확장자 제거"""
    if not press:
        return press
    
    # www. 제거
    press = press.replace('www.', '')
    
    # .co.kr, .com, .net 등 제거
    press = re.sub(r'\.(co\.kr|com|net|org|kr)$', '', press)
    press = re.sub(r'\.(info|biz|edu|gov|mil|int)$', '', press)
    
    return press.strip()

def format_date(date_str):
    """날짜 형식을 yyyy-mm-dd HH:MM:SS로 변환"""
    if not date_str:
        return date_str
    
    try:
        # RFC 2822 형식 파싱 (예: "Mon, 08 Jul 2025 13:34:51 +0900")
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
            "%Y-%m-%d %H:%M:%S",         # ISO 형식
            "%Y-%m-%d",                  # 날짜만
            "%d %b %Y %H:%M:%S",         # 시간대 없음
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
        
        # 파싱 실패 시 원본 반환
        return date_str
        
    except Exception as e:
        print(f"날짜 형식 변환 실패: {date_str}, 오류: {e}")
        return date_str

# ============================================================================
# 데이터베이스 관련 함수들
# ============================================================================

def get_active_keywords_from_db():
    """데이터베이스에서 활성화된 키워드들을 가져오는 함수"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT keyword, group_name FROM keywords WHERE is_active = 1")
    keywords_data = cursor.fetchall()
    
    conn.close()
    return keywords_data

# ============================================================================
# 기사 추출 및 처리 함수들
# ============================================================================

def extract_press_from_url(originallink):
    """URL에서 언론사 도메인 추출"""
    if not originallink:
        return ""
    domain = urlparse(originallink).netloc
    return domain

def extract_article_content(url):
    """기사 본문 추출"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if 'news.naver.com' in url:
            content_selectors = [
                '#articleBody',
                '#articleBodyContents',
                '.article_body',
                '#content',
                '.news_end',
            ]
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    for unwanted in content_element.select('script, style, .reporter_area, .copyright, .link_news'):
                        unwanted.decompose()
                    content = content_element.get_text(strip=True)
                    if content and len(content) > 100:
                        return clean_text(content)
        
        general_selectors = [
            'article',
            '.article-content',
            '.news-content',
            '.content',
            '.post-content',
            '.entry-content',
            'main',
            '.main-content'
        ]
        for selector in general_selectors:
            content_elements = soup.select(selector)
            for element in content_elements:
                for unwanted in element.select('script, style, nav, header, footer, .advertisement, .sidebar'):
                    unwanted.decompose()
                content = element.get_text(strip=True)
                if content and len(content) > 200:
                    return clean_text(content)
        
        body = soup.find('body')
        if body:
            for unwanted in body.select('script, style, nav, header, footer, .advertisement, .sidebar, .comment'):
                unwanted.decompose()
            content = body.get_text(strip=True)
            if content and len(content) > 300:
                return clean_text(content)
        
        return ""
    except Exception:
        return ""

def save_article_to_db(article, keyword):
    """기사를 데이터베이스에 저장 (정제 포함)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 그룹명 조회
    cursor.execute("SELECT group_name FROM keywords WHERE keyword=? AND is_active=1", (keyword,))
    row = cursor.fetchone()
    group_name = row[0] if row else None
    
    # 중복 URL 검사
    cursor.execute("SELECT id FROM articles WHERE url = ?", (article['link'],))
    if cursor.fetchone():
        conn.close()
        return False
    
    # 원본 데이터 추출
    title = clean_text(article.get('title', ''))
    content = extract_article_content(article.get('link', ''))
    press = extract_press_from_url(article.get('originallink', ''))
    pub_date = article.get('pubDate', '')
    
    # 데이터 정제
    content = clean_text(content)
    press = clean_press_domain(press)
    pub_date = format_date(pub_date)
    
    # 제목이 모두 영문인지 확인 (한글이 하나도 없으면 제외)
    if title and not re.search(r'[가-힣]', title):
        # 영문, 숫자, 특수문자만 있는지 확인
        if re.search(r'[A-Za-z]', title):
            print(f"🔤 [필터] 영문 제목 기사 제외: {title[:40]} ...")
            conn.close()
            return False
    
    # 야구 관련 키워드 리스트
    baseball_terms = [
        '이정후', '김하성', '이닝', '실점', '투수', '타자', '홈런', '야구', 'KBO', '삼진', '타율', '도루',
        '포수', '마운드', '경기', '선발', '불펜', '타점', '득점', '안타', '볼넷', '스트라이크',
        '포스트시즌', '월드시리즈', '메이저리그', 'MLB', '구단', '감독', '코치', '선수', '타순',
        '타격', '수비', '연봉', '이적', '트레이드', '시범경기', '플레이오프', '클린업', '사구', '홈플레이트',
        '외야수', '내야수', '주루', '슬라이딩', '사이드암', '언더핸드', '좌완', '우완', '완투', '완봉', '노히트', '노런'
    ]

    # MLB/엠엘비 + 야구 기사 필터링
    if keyword in ['MLB', '엠엘비']:
        if any(term in title for term in baseball_terms) or any(term in content for term in baseball_terms):
            print(f"⚾️ [필터] MLB/엠엘비 키워드 야구 기사 제외: {title[:40]} ...")
            conn.close()
            return False
    
    # F&F 키워드 특별 필터링
    if keyword == 'F&F':
        # 1. 제목이나 본문에 실제로 F&F가 없는 기사 필터링 (네이버 API 오탐지 방지)
        if 'F&F' not in title and 'F&F' not in content and 'f&f' not in title.lower() and 'f&f' not in content.lower():
            print(f"🔍 [필터] F&F 키워드 오탐지 기사 제외: {title[:40]} ... (제목/본문에 F&F 없음)")
            conn.close()
            return False
        
        # 2. 지주사 관련주 나열 기사 필터링
        if '(지주사 관련주)' in content or '지주사 관련주' in content:
            # 홀딩스/지주 관련 기업명 리스트
            holding_companies = [
                '홀딩스', '지주', '대상홀딩스', '한화', '하나금융지주', 'GRT', '한진중공업홀딩스', 
                '로스웰', '성창기업지주', '평화홀딩스', 'BNK금융지주', '우리산업홀딩스', '휴맥스홀딩스',
                '비츠로테크', '네오위즈홀딩스', '부방', '한국콜마홀딩스', '디와이', '한미사이언스',
                'LS전선아시아', '컴투스홀딩스', 'JB금융지주', '솔본', '글로벌에스엠', '엘브이엠씨홀딩스',
                'KB금융', 'DGB금융지주', '슈프리마에이치큐', 'KC그린홀딩스', 'CNH', 'BGF', '풀무원',
                '일동홀딩스', '신송홀딩스', '오가닉티코스메틱', '녹십자홀딩스', '신한지주', '우리금융지주',
                'APS', '휴온스글로벌', '덕산하이메탈', '이지홀딩스', '일진홀딩스', '윙입푸드', '오리온홀딩스',
                'CR홀딩스', 'SK디스커버리', '코아시아', 'DRB동일', '골든센츄리', '웅진', '롯데지주',
                '코오롱', '동국홀딩스', '메리츠금융지주', '해성산업', '제일파마홀딩스', 'LG', 'AJ네트웍스',
                'HDC', '에코프로', '경동인베스트', 'GS', 'SJM홀딩스', '유수홀딩스', '서연',
                '유비쿼스홀딩스', '샘표', '삼성물산', '이건홀딩스', '이녹스', '금호건설', '동아쏘시오홀딩스',
                '대덕', '아세아', 'LX홀딩스', '대웅', '솔브레인홀딩스', '동성케미컬', '효성', 'HD현대',
                '풍산홀딩스', 'NICE', '삼양홀딩스', 'SK스퀘어', '한세예스24홀딩스', 'KPX홀딩스',
                '한솔홀딩스', '그래디언트', '심텍홀딩스', 'CS홀딩스', 'F&F홀딩스', '영원무역홀딩스',
                '골프존뉴딘홀딩스', '하이트진로홀딩스', '노루홀딩스', 'KISCO홀딩스', 'AK홀딩스', 'DB',
                '예스코홀딩스', '코스맥스비티아이', '아이디스홀딩스', '농심홀딩스', '진양홀딩스', '두산밥캣', '헝셍그룹'
            ]
            
            # 본문에서 홀딩스/지주 관련 기업명이 5개 이상 언급되면 필터링
            holding_count = sum(1 for company in holding_companies if company in content)
            if holding_count >= 5:
                print(f"🏢 [필터] F&F 키워드 지주사 관련주 나열 기사 제외: {title[:40]} ... (홀딩스 관련 기업 {holding_count}개 언급)")
                conn.close()
                return False
    
    # 데이터베이스에 저장
    cursor.execute("""
        INSERT INTO articles (keyword, group_name, title, content, press, pub_date, url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        keyword,
        group_name,
        title,
        content,
        press,
        pub_date,
        article.get('link', '')
    ))
    conn.commit()
    conn.close()
    return True

# ============================================================================
# 네이버 뉴스 API 관련 함수들
# ============================================================================

def search_naver_news(keyword, display=10, start=1, sort='date', start_date=None, end_date=None):
    """네이버 뉴스 API 검색"""
    url = 'https://openapi.naver.com/v1/search/news.json'
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
    }
    
    search_query_encoded = quote(keyword, safe='')
    
    params = {
        'query': search_query_encoded,
        'display': display,
        'start': start,
        'sort': sort
    }
    
    print(f"[DEBUG] 네이버 뉴스 API 요청 쿼리: {keyword} → {search_query_encoded}")
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    
    # 날짜 필터링 (필요시)
    if start_date and end_date and 'items' in result:
        filtered_items = []
        for article in result['items']:
            pub_date_str = article.get('pubDate', '')
            if pub_date_str:
                try:
                    pub_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                    pub_date_local = pub_date.replace(tzinfo=None)
                    if start_date <= pub_date_local <= end_date:
                        filtered_items.append(article)
                except ValueError:
                    continue
        result['items'] = filtered_items
        result['total'] = len(filtered_items)
    
    return result

def search_naver_news_all_pages(keyword, start_date=None, end_date=None):
    """페이지 끝까지 최대 100개 기사만 검색하는 함수"""
    all_articles = []
    page = 1
    display = 100  # 한 번에 100개씩 가져오기

    print(f"    🔍 키워드 '{keyword}' 크롤링 시작")
    print(f"    📄 페이지별 검색 시작...")

    while len(all_articles) < 100:
        start_index = (page - 1) * display + 1
        try:
            result = search_naver_news(keyword, display=display, start=start_index, sort='date', 
                                     start_date=start_date, end_date=end_date)
            articles = result.get('items', [])
            if not articles:
                print(f"    📄 페이지 {page}: 더 이상 기사가 없습니다. (총 {len(all_articles)}개 기사 수집 완료)")
                break
            # 남은 수만큼만 추가
            remain = 100 - len(all_articles)
            all_articles.extend(articles[:remain])
            print(f"    📄 페이지 {page}: {len(articles[:remain])}개 기사 검색 (start={start_index})")
            time.sleep(0.1)
            page += 1
            if len(all_articles) >= 100:
                print(f"    ⚠️ 최대 수집 한도(100개)에 도달했습니다.")
                break
        except Exception as e:
            print(f"    ❌ 페이지 {page} 검색 중 오류: {e}")
            break
    print(f"    📊 키워드 '{keyword}' 크롤링 완료. 총 {len(all_articles)}개 기사 검색")
    return all_articles

def filter_and_save_articles(articles, keyword):
    """기사들을 필터링하고 저장하는 함수"""
    filtered_articles = []
    saved_count = 0
    skipped_count = 0
    duplicate_count = 0
    
    for article in articles:
        title = clean_text(article.get('title', ''))
        url = article.get('link', '')
        
        # URL 기반 중복 체크
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
        is_duplicate = cursor.fetchone() is not None
        conn.close()
        
        if is_duplicate:
            duplicate_count += 1
            filtered_articles.append({
                'title': title,
                'url': url,
                'status': 'duplicate',
                'reason': 'URL 중복'
            })
            continue
        
        # 본문 추출 및 DB 저장
        if save_article_to_db(article, keyword):
            saved_count += 1
            filtered_articles.append({
                'title': title,
                'url': url,
                'status': 'saved'
            })
        else:
            skipped_count += 1
    
    return {
        'saved_count': saved_count,
        'skipped_count': skipped_count,
        'duplicate_count': duplicate_count,
        'filtered_articles': filtered_articles
    }

# ============================================================================
# Flask API 엔드포인트들
# ============================================================================

@naver_news_bp.route('/news/search', methods=['GET'])
def news_search():
    """뉴스 검색 API"""
    keyword = request.args.get('keyword')
    display = int(request.args.get('display', 10))
    start = int(request.args.get('start', 1))
    sort = request.args.get('sort', 'date')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not keyword:
        return jsonify({'error': '키워드 필요'}), 400
    
    parsed_start_date = None
    parsed_end_date = None
    if start_date and end_date:
        try:
            parsed_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            parsed_end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': '날짜 형식 오류 (YYYY-MM-DD)'}), 400
    
    result = search_naver_news(keyword, display=display, start=start, sort=sort, 
                              start_date=parsed_start_date, end_date=parsed_end_date)
    return jsonify(result)

@naver_news_bp.route('/news/search_all_pages', methods=['POST'])
def search_all_pages():
    """페이지 끝까지 모든 기사 검색 및 저장"""
    data = request.get_json()
    keyword = data.get('keyword')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not keyword:
        return jsonify({'error': '키워드 필요'}), 400
    
    parsed_start_date = None
    parsed_end_date = None
    if start_date and end_date:
        try:
            parsed_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            parsed_end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': '날짜 형식 오류 (YYYY-MM-DD)'}), 400
    
    # 페이지 끝까지 모든 기사 검색
    articles = search_naver_news_all_pages(keyword, start_date=parsed_start_date, end_date=parsed_end_date)
    
    # 필터링 및 저장
    filter_result = filter_and_save_articles(articles, keyword)
    return jsonify({
        'message': f'{filter_result["saved_count"]}건 저장 완료', 
        'total': len(articles), 
        'saved': filter_result["saved_count"],
        'skipped': filter_result["skipped_count"],
        'duplicate': filter_result["duplicate_count"],
        'filtered_articles': filter_result["filtered_articles"],
        'date_range': f"{start_date} ~ {end_date}" if start_date and end_date else "전체 기간"
    })

# ============================================================================
# 정식 업무 수행 함수들
# ============================================================================

def run_news_collection():
    """뉴스 수집 업무 실행 (스케줄러에서 호출)"""
    print(f"🚀 뉴스 수집 업무 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키가 설정되지 않았습니다.")
        return {
            'success': False,
            'error': '네이버 API 키 미설정',
            'total_articles': 0,
            'saved_articles': 0
        }
    try:
        active_keywords_data = get_active_keywords_from_db()
        if not active_keywords_data:
            print("❌ 활성화된 키워드가 없습니다.")
            return {
                'success': False,
                'error': '활성화된 키워드 없음',
                'total_articles': 0,
                'saved_articles': 0
            }
        active_keywords = [row[0] for row in active_keywords_data]
        print(f"📋 처리할 키워드: {active_keywords}")
    except Exception as e:
        print(f"❌ 키워드 조회 중 오류: {e}")
        return {
            'success': False,
            'error': f'키워드 조회 오류: {str(e)}',
            'total_articles': 0,
            'saved_articles': 0
        }
    total_articles = 0
    saved_articles = 0
    failed_keywords = []
    for keyword in active_keywords:
        print(f"\n🔍 키워드 '{keyword}' 처리 중...")
        try:
            articles = search_naver_news_all_pages(keyword)
            print(f"  📊 검색 결과: {len(articles)}개 기사")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            for article in articles:
                url = article.get('link', '')
                cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
                if cursor.fetchone() is not None:
                    print(f"  ⚠️ 중복 URL 발견: {url} → 다음 키워드로 건너뜁니다.")
                    break
                # 중복이 아니면 저장
                if save_article_to_db(article, keyword):
                    saved_articles += 1
            conn.close()
            total_articles += len(articles)
        except Exception as e:
            print(f"  ❌ 키워드 '{keyword}' 처리 중 오류: {e}")
            failed_keywords.append(keyword)
    print(f"\n📈 뉴스 수집 완료 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  총 검색된 기사: {total_articles}개")
    print(f"  총 저장된 기사: {saved_articles}개")
    print(f"  저장 성공률: {(saved_articles/total_articles*100):.1f}%" if total_articles > 0 else "  저장 성공률: 0%")
    if failed_keywords:
        print(f"  실패한 키워드: {failed_keywords}")
    return {
        'success': True,
        'total_articles': total_articles,
        'saved_articles': saved_articles,
        'failed_keywords': failed_keywords,
        'success_rate': (saved_articles/total_articles*100) if total_articles > 0 else 0
    }

def run_news_collection_for_keyword(keyword, start_date=None, end_date=None):
    """특정 키워드에 대한 뉴스 수집 실행"""
    print(f"🔍 키워드 '{keyword}' 뉴스 수집 시작")
    
    try:
        # 페이지 끝까지 모든 기사 검색
        articles = search_naver_news_all_pages(keyword, start_date=start_date, end_date=end_date)
        
        if not articles:
            print(f"키워드 '{keyword}'로 검색된 기사가 없습니다.")
            return {
                'success': True,
                'keyword': keyword,
                'total_articles': 0,
                'saved_articles': 0
            }
        
        # 필터링 및 저장
        filter_result = filter_and_save_articles(articles, keyword)
        
        print(f"✅ 키워드 '{keyword}' 처리 완료")
        print(f"  검색된 기사: {len(articles)}개")
        print(f"  저장된 기사: {filter_result['saved_count']}개")
        
        return {
            'success': True,
            'keyword': keyword,
            'total_articles': len(articles),
            'saved_articles': filter_result['saved_count'],
            'skipped_count': filter_result['skipped_count'],
            'duplicate_count': filter_result['duplicate_count']
        }
        
    except Exception as e:
        print(f"❌ 키워드 '{keyword}' 처리 중 오류: {e}")
        return {
            'success': False,
            'keyword': keyword,
            'error': str(e),
            'total_articles': 0,
            'saved_articles': 0
        }

# ============================================================================
# 실행 코드 (테스트 및 직접 실행용)
# ============================================================================

if __name__ == "__main__":
    # 정식 업무 실행
    result = run_news_collection()
    
    if result['success']:
        print(f"\n🎉 뉴스 수집 업무가 성공적으로 완료되었습니다!")
        print(f"   저장 성공률: {result['success_rate']:.1f}%")
    else:
        print(f"\n⚠️ 뉴스 수집 업무 중 오류가 발생했습니다: {result['error']}")
    
    print("✅ 프로그램 종료") 