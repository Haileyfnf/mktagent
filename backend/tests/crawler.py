import requests
import urllib.parse
import sqlite3
import time
import re
import logging
import os
import json
import openai
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 네이버 API 키 설정 (.env에서 가져오기)
CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError('네이버 API 키 또는 시크릿이 .env 파일에 설정되어 있지 않습니다.')

# OpenAI API 키 설정 (.env에서 가져오기)
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    logger.warning("AI 분류 기능이 제한될 수 있습니다.")
else:
    logger.info("OpenAI API 키가 정상적으로 설정되었습니다.")

DB_PATH = 'c:/Users/haenee/mkt_ai_agent/backend/src/database/db.sqlite'

def get_keywords():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT keyword FROM keywords")
    keywords = [row[0] for row in c.fetchall()]
    conn.close()
    logger.info(f"크롤링할 키워드: {keywords}")
    return keywords

def get_group_name(keyword):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT group_name FROM keywords WHERE keyword = ?", (keyword,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def extract_press_from_url(originallink):
    if not originallink:
        return ""
    from urllib.parse import urlparse
    domain = urlparse(originallink).netloc
    return domain

def save_article(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 중복 URL 검사
    c.execute("SELECT id FROM articles WHERE url = ?", (data['url'],))
    if c.fetchone():
        logger.info(f"중복 URL로 저장하지 않음: {data['url']}")
        conn.close()
        return
    c.execute("""
        INSERT INTO articles (keyword, group_name, title, content, press, pub_date, url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
    """, (
        data['keyword'],
        data['group_name'],
        data['title'],
        data['content'],
        data['press'],
        data['pub_date'],
        data['url']
    ))
    conn.commit()
    conn.close()
    logger.info(f"기사 저장 완료: {data['title'][:30]}...")

def classify_article_with_ai(title: str, content: str, keywords: list) -> tuple:
    """
    OpenAI API를 사용하여 기사를 가장 적합한 키워드로 분류하고 보도자료/오가닉 판단
    """
    try:
        # 프롬프트 구성
        prompt = f"""
다음 뉴스 기사를 분석하여 가장 적합한 키워드로 분류하고, 보도자료인지 오가닉 기사인지 판단해주세요.

**기사 제목**: {title}

**기사 본문**: {content[:2000]}...

**분류할 키워드**: {', '.join(keywords)}

**분류 기준**:
- F&F: 패션 회사 F&F와 관련된 내용 (브랜드 소유, 경영, 투자, 엔터테인먼트, 유니스(UNIS), 아홉(AHOF) 등)
- MLB: MLB 브랜드와 관련된 패션/의류 내용 (야구 관련 내용 제외)
- 디스커버리 익스페디션: 디스커버리 익스페디션 브랜드와 관련된 내용 (자동차 관련 내용 제외)
- 엠엘비: 엠엘비 브랜드와 관련된 패션/의류 내용 (야구 관련 내용 제외)

**보도자료 판단 기준**:
- "F&F 관계자에 따르면", "MLB 측", "디스커버리 관계자" 등 패턴
- "보도자료 제공" 문구
- 브랜드에서 직접 발표한 내용

**응답 형식**:
{{
    "best_keyword": "가장 적합한 키워드",
    "article_type": "보도자료" 또는 "오가닉",
    "reasoning": "분류 이유 (한국어로 설명)",
    "confidence": 0.95
}}

만약 여러 키워드가 동시에 언급되면, 기사의 주요 주제나 핵심 내용을 기준으로 가장 적합한 하나를 선택해주세요.
"""

        # OpenAI API 호출 (이전 버전)
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": "당신은 F&F 회사와 사내 소속된 브랜드들의 뉴스 기사 분류 전문가입니다. 주어진 키워드 중에서 기사와 가장 관련성이 높은 키워드를 정확하게 분류해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # 더 일관된 결과를 위해 낮춤
            max_tokens=150    # JSON 응답이므로 충분함
        )
        
        # 응답 파싱
        result_text = response.choices[0].message.content.strip()
        
        try:
            result = json.loads(result_text)
            best_keyword = result.get("best_keyword", keywords[0])
            article_type = result.get("article_type", "오가닉")
            reasoning = result.get("reasoning", "AI 분류 실패")
            confidence = result.get("confidence", 0.5)
            
            logger.info(f"AI 분류 결과: {best_keyword} ({article_type}) (신뢰도: {confidence:.2f})")
            logger.info(f"분류 이유: {reasoning}")
            
            return best_keyword, article_type, reasoning, confidence
            
        except json.JSONDecodeError:
            logger.error(f"JSON 파싱 실패: {result_text}")
            return keywords[0], "오가닉", "AI 분류 실패", 0.5
            
    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {e}")
        return keywords[0], "오가닉", f"API 오류: {str(e)}", 0.5

def classify_article_content(title: str, content: str, keywords: list) -> dict:
    """
    기사 내용을 분석하여 분류 결과 반환 (AI 호출 없이 fallback만 사용)
    """
    try:
        # best_keyword, article_type, reasoning, confidence = classify_article_with_ai(title, content, keywords)
        # return {
        #     "classification_method": "AI",
        #     "best_keyword": best_keyword,
        #     "article_type": article_type,
        #     "reasoning": reasoning,
        #     "confidence": confidence,
        #     "all_keywords_found": [kw for kw in keywords if kw.lower() in content.lower()]
        # }
        # === AI 호출 없이 fallback만 사용 ===
        return fallback_classification(title, content, keywords)
    except Exception as e:
        logger.error(f"AI 분류 실패, 기본 분류로 대체: {e}")
        return fallback_classification(title, content, keywords)

def fallback_classification(title: str, content: str, keywords: list) -> dict:
    """
    AI 분류 실패 시 사용하는 기본 분류 방법
    """
    text = (title + " " + content).lower()
    
    # 각 키워드별 점수 계산
    keyword_scores = {}
    for keyword in keywords:
        score = 0
        # 제목에 있으면 높은 점수
        if keyword.lower() in title.lower():
            score += 3
        # 본문에 있으면 점수 추가
        if keyword.lower() in text:
            score += 1
        keyword_scores[keyword] = score
    
    # 가장 높은 점수의 키워드 선택
    best_keyword = max(keyword_scores, key=keyword_scores.get)
    
    return {
        "classification_method": "fallback",
        "best_keyword": best_keyword,
        "reasoning": f"기본 키워드 매칭 (점수: {keyword_scores[best_keyword]})",
        "confidence": min(keyword_scores[best_keyword] / 4, 0.8),
        "all_keywords_found": [kw for kw in keywords if kw.lower() in text]
    }

def extract_article_content(url):
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
                        logger.info(f"네이버 뉴스 본문 추출 성공 (길이: {len(content)}자)")
                        return content
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
                    logger.info(f"일반 뉴스 본문 추출 성공 (길이: {len(content)}자)")
                    return content
        body = soup.find('body')
        if body:
            for unwanted in body.select('script, style, nav, header, footer, .advertisement, .sidebar, .comment'):
                unwanted.decompose()
            content = body.get_text(strip=True)
            if content and len(content) > 300:
                logger.info(f"body 전체에서 본문 추출 (길이: {len(content)}자)")
                return content
        logger.warning(f"본문을 찾을 수 없습니다: {url}")
        return ""
    except requests.RequestException as e:
        logger.error(f"기사 페이지 요청 실패: {url}, 오류: {e}")
        return ""
    except Exception as e:
        logger.error(f"본문 추출 중 오류: {url}, 오류: {e}")
        return ""

def keyword_variants(keyword):
    variants = [keyword]
    if '&' in keyword:
        variants.append(keyword.replace('&', 'and'))
        variants.append(keyword.replace('&', ''))
    variants.append(keyword.lower())
    variants.append(keyword.upper())
    return list(set(variants))

def crawl_news_for_keyword(keyword, start_date=None, end_date=None):
    logger.info(f"키워드 '{keyword}' 크롤링 시작")
    search_query = keyword
    logger.info(f"검색 쿼리: {search_query}")
    query = urllib.parse.quote(search_query)
    
    total_articles = 0
    page = 1
    display = 100  # 한 번에 100개씩 가져오기
    
    while True:
        start_index = (page - 1) * display + 1
        url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display={display}&start={start_index}&sort=date"
        headers = {
            "X-Naver-Client-Id": CLIENT_ID,
            "X-Naver-Client-Secret": CLIENT_SECRET
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if not data['items']:
                logger.info(f"페이지 {page}: 더 이상 기사가 없습니다. (총 {total_articles}개 기사 수집 완료)")
                break
                
            logger.info(f"페이지 {page}: {len(data['items'])}개 기사 검색 (start={start_index})")
            group_name = get_group_name(keyword)
            
            page_articles = 0
            for i, item in enumerate(data['items'], 1):
                title = BeautifulSoup(item['title'], "html.parser").get_text()
                press = extract_press_from_url(item.get('originallink', ''))
                pub_date = item['pubDate']
                link = item['link']
                

                
                # 데이터 정제
                # 1. content에서 NBSP 제거
                if article_content:
                    article_content = article_content.replace('&nbsp;', ' ').replace('\xa0', ' ')
                    import re
                    article_content = re.sub(r'\s+', ' ', article_content).strip()
                
                # 2. press 도메인 정제
                if press:
                    press = press.replace('www.', '')
                    import re
                    press = re.sub(r'\.(co\.kr|com|net|org|kr)$', '', press)
                    press = re.sub(r'\.(info|biz|edu|gov|mil|int)$', '', press)
                    press = press.strip()
                
                # 3. 날짜 형식 변환
                if pub_date:
                    try:
                        from datetime import datetime
                        date_formats = [
                            "%a, %d %b %Y %H:%M:%S %z",  # RFC 2822
                            "%Y-%m-%d %H:%M:%S",         # ISO 형식
                            "%Y-%m-%d",                  # 날짜만
                            "%d %b %Y %H:%M:%S",         # 시간대 없음
                        ]
                        
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(pub_date, fmt)
                                pub_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                                break
                            except ValueError:
                                continue
                    except Exception as e:
                        logger.warning(f"날짜 형식 변환 실패: {pub_date}, 오류: {e}")
                
                logger.info(f"  {i}. 제목: {title}")
                logger.info(f"     언론사: {press}")
                logger.info(f"     업로드 일자/시간: {pub_date}")
                logger.info(f"     기사 링크: {link}")
                article_content = extract_article_content(link)
                logger.info(f"     기사 본문 크롤링 시작...")
                
                # 정제된 데이터로 저장
                save_article({
                    "keyword": keyword,
                    "group_name": group_name,
                    "title": title,
                    "content": article_content,
                    "press": press,
                    "pub_date": pub_date,
                    "url": link
                })
                total_articles += 1
                page_articles += 1
            
            logger.info(f"페이지 {page}: {page_articles}개 기사 저장")
            
            # API 호출 간격 조절
            time.sleep(0.1)
            page += 1
        else:
            logger.error(f"Error Code: {response.status_code}")
            break
    
    logger.info(f"키워드 '{keyword}' 크롤링 완료. 총 {total_articles}개 기사 DB 저장")
    return total_articles

def main():
    logger.info("크롤링 시작")
    keywords = ["디스커버리 익스페디션"]
    start_date = None
    end_date = None
    logger.info("날짜 필터링 제거 - 최신 기사 수집")
    keyword_article_count = {}
    for kw in keywords:
        count = crawl_news_for_keyword(kw, start_date, end_date)
        keyword_article_count[kw] = count
    logger.info("=== 키워드별 크롤링 기사 수 ===")
    for kw, count in keyword_article_count.items():
        logger.info(f"{kw}: {count}개")
    logger.info("모든 크롤링 완료")

def is_fashion_article(title, content):
    """패션 관련 기사인지 판단"""
    text = (title + ' ' + content).lower()
    
    # 야구 관련 키워드가 2개 이상 있으면 제외
    baseball_terms = ['야구', 'baseball', '투수', '타자', '홈런', '구단', 'pitcher', 'batter', 'hitter', 'home run']
    baseball_count = sum(1 for term in baseball_terms if term in text)
    if baseball_count >= 2:
        logger.info(f"야구 관련 키워드 {baseball_count}개 감지: 기사 제외")
        return False
    
    # 패션 관련 키워드가 있으면 포함
    fashion_keywords = ['패션', '의류', '브랜드', '디자인', '스타일', 'fashion', 'clothing', 'brand', 'design']
    if any(keyword in text for keyword in fashion_keywords):
        logger.info(f"패션 관련 키워드 감지: 기사 포함")
        return True
    
    return True

if __name__ == "__main__":
    main()
