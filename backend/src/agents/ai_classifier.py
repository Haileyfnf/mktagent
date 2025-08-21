import openai
import json
import logging
import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI API 키 설정 (.env에서 가져오기)
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    logger.warning("AI 분류 기능이 제한될 수 있습니다.")

def classify_article_with_ai(title: str, content: str, keywords: List[str]) -> Tuple[str, str, float]:
    """
    OpenAI API를 사용하여 기사를 가장 적합한 키워드로 분류해서 기사를 저장해주세요.
    
    Args:
        title: 기사 제목
        content: 기사 본문
        keywords: 분류할 키워드 리스트
    
    Returns:
        (best_keyword, reasoning, confidence_score)
    """
    
    try:
        # 프롬프트 구성
        prompt = f"""
다음 뉴스 기사를 분석하여 가장 적합한 키워드로 분류해주세요.

**기사 제목**: {title}

**기사 본문**: {content[:2000]}...

**분류할 키워드**: {', '.join(keywords)}

**분류 기준**:
- F&F: 패션 회사 F&F와 관련된 내용 (브랜드 소유, 경영, 투자, 엔터테인먼트, 유니스(UNIS), 아홉(AHOF) 등)
- MLB: MLB 브랜드와 관련된 패션/의류 내용 (야구 관련 내용 제외)
- 디스커버리 익스페디션: 디스커버리 익스페디션 브랜드와 관련된 내용 (자동차 관련 내용 제외)
- 엠엘비: 엠엘비 브랜드와 관련된 패션/의류 내용 (야구 관련 내용 제외)

**응답 형식**:
{{
    "best_keyword": "가장 적합한 키워드",
    "reasoning": "분류 이유 (한국어로 설명)",
    "confidence": 0.95
}}

만약 여러 키워드가 동시에 언급되면, 기사의 주요 주제나 핵심 내용을 기준으로 가장 적합한 하나를 선택해주세요.
"""

        # OpenAI API 호출
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 F&F 회사와 사내 소속된 브랜드들의 뉴스 기사 분류 전문가입니다. 주어진 키워드 중에서 기사와 가장 관련성이 높은 키워드를 정확하게 분류해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # 응답 파싱
        result_text = response.choices[0].message.content.strip()
        
        # JSON 파싱 시도
        try:
            result = json.loads(result_text)
            best_keyword = result.get("best_keyword", keywords[0])
            reasoning = result.get("reasoning", "AI 분류 실패")
            confidence = result.get("confidence", 0.5)
            
            logger.info(f"AI 분류 결과: {best_keyword} (신뢰도: {confidence:.2f})")
            logger.info(f"분류 이유: {reasoning}")
            
            return best_keyword, reasoning, confidence
            
        except json.JSONDecodeError:
            logger.error(f"JSON 파싱 실패: {result_text}")
            return keywords[0], "AI 분류 실패", 0.5
            
    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {e}")
        return keywords[0], f"API 오류: {str(e)}", 0.5

def classify_article_content(title: str, content: str, keywords: List[str]) -> Dict:
    """
    기사 내용을 분석하여 분류 결과 반환
    
    Args:
        title: 기사 제목
        content: 기사 본문
        keywords: 분류할 키워드 리스트
    
    Returns:
        분류 결과 딕셔너리
    """
    
    # AI 분류 시도
    try:
        best_keyword, reasoning, confidence = classify_article_with_ai(title, content, keywords)
        
        return {
            "classification_method": "AI",
            "best_keyword": best_keyword,
            "reasoning": reasoning,
            "confidence": confidence,
            "all_keywords_found": [kw for kw in keywords if kw.lower() in content.lower()]
        }
        
    except Exception as e:
        logger.error(f"AI 분류 실패, 기본 분류로 대체: {e}")
        
        # AI 분류 실패 시 기본 키워드 매칭으로 대체
        return fallback_classification(title, content, keywords)

def fallback_classification(title: str, content: str, keywords: List[str]) -> Dict:
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

# 테스트 함수
def test_classification():
    """분류 시스템 테스트"""
    test_title = "Girl group UNIS's new EP 'Swicy' brings the sweetness and the spice"
    test_content = """
    UNIS, the rookie girl group under F&F Entertainment, hopes to ride the global tide with its new album...
    The group made its official debut on March 27 last year with its first EP "We Unis" under F&F Entertainment, 
    an agency owned by fashion company F&F that owns major brands such as MLB and Discovery Expedition.
    """
    
    keywords = ["F&F", "MLB", "디스커버리 익스페디션", "엠엘비"]
    
    result = classify_article_content(test_title, test_content, keywords)
    print("분류 결과:", json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_classification() 