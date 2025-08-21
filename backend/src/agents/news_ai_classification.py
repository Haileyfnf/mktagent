import os
import sqlite3
import json
import re
from datetime import datetime, timedelta
from openai import OpenAI
from typing import Dict, List, Tuple, Optional
import time

class NewsAIClassifier:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 현재 스크립트 위치 기준으로 상대 경로 설정
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, "..", "database", "db.sqlite")
        
        self.db_path = db_path
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API 키가 설정되지 않았습니다. 분류 작업을 중단합니다.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"❌ OpenAI API 클라이언트 생성 실패: {e}")
                self.client = None
        
        # 프롬프트 템플릿 로드
        self.prompts = self._load_prompts()
        
    def _load_prompts(self) -> Dict[str, str]:
        """프롬프트 파일에서 기본 템플릿을 로드합니다."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file = os.path.join(script_dir, "prompts", "classification_prompts.md")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 기본 프롬프트 추출
            default_match = re.search(r'## 기본 분류 프롬프트\s*\n\s*```(.*?)```', content, re.DOTALL)
            if default_match:
                return {'default': default_match.group(1).strip()}
            else:
                print("기본 프롬프트를 찾을 수 없습니다.")
                return {}
            
        except FileNotFoundError:
            print(f"프롬프트 파일을 찾을 수 없습니다: {prompt_file}")
            return {}
        except Exception as e:
            print(f"프롬프트 로드 중 오류: {e}")
            return {}

    def _get_prompt_template(self, keyword: str) -> str:
        """키워드에 맞는 프롬프트 템플릿을 반환합니다."""
        # 모든 키워드가 동일한 기본 템플릿 사용
        return self.prompts.get('default', '').replace('{keyword}', keyword)

    def _parse_ai_response(self, response: str) -> Tuple[str, float, str]:
        """AI 응답을 파싱하여 분류 결과를 추출합니다."""
        try:
            # 코드블록 제거
            response = re.sub(r"^```json|^```|```$", "", response, flags=re.MULTILINE).strip()
            
            # JSON 파싱 시도
            try:
                result = json.loads(response)
                classification = result.get('classification', '해당없음')
                confidence = float(result.get('confidence', 0.5))
                reason = result.get('reason', '근거 없음')
                return classification, confidence, reason
            except json.JSONDecodeError:
                print(f"JSON 파싱 실패, 원본 응답: {response}")
                
                # JSON 파싱 실패 시 정규식으로 파싱 시도 (이전 방식)
                classification_match = re.search(r'"classification":\s*"(보도자료|오가닉|해당없음)"', response)
                classification = classification_match.group(1) if classification_match else "해당없음"
                
                confidence_match = re.search(r'"confidence":\s*([0-9]*\.?[0-9]+)', response)
                confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                
                reason_match = re.search(r'"reason":\s*"([^"]+)"', response)
                reason = reason_match.group(1) if reason_match else "근거 없음"
                
                return classification, confidence, reason
            
        except Exception as e:
            print(f"AI 응답 파싱 오류: {e}")
            return "해당없음", 0.5, "파싱 오류"

    def classify_article(self, title: str, content: str, keyword: str) -> Dict:
        if self.client is None:
            print("❌ OpenAI API 미연동 상태입니다. 분류를 건너뜁니다.")
            return {
                'classification': '해당없음',
                'confidence': 0.0,
                'reason': 'OpenAI API 미연동'
            }
        """단일 기사를 분류합니다."""
        try:
            # 프롬프트 템플릿 가져오기
            prompt_template = self._get_prompt_template(keyword)
            
            if not prompt_template:
                print(f"키워드 '{keyword}'에 대한 프롬프트 템플릿을 찾을 수 없습니다.")
                return {
                    'classification': '해당없음',
                    'confidence': 0.0,
                    'reason': '프롬프트 템플릿 없음'
                }
            
            # 프롬프트 생성
            prompt = prompt_template.format(title=title, content=content)
            
            # OpenAI API 최신 방식 호출
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 뉴스 기사 분류 전문가입니다. 정확하고 일관된 분류를 제공해 주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # 응답 파싱
            classification, confidence, reason = self._parse_ai_response(ai_response)
            
            return {
                'classification': classification,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            print(f"기사 분류 중 오류: {e}")
            return {
                'classification': '해당없음',
                'confidence': 0.0,
                'reason': f'분류 오류: {str(e)}'
            }

    def classify_articles_by_keyword(self, keyword: str, start_date: str = None, end_date: str = None) -> List[Dict]:
        # 프롬프트 템플릿이 없으면 분류 자체를 수행하지 않음
        if not self.prompts or not self.prompts.get('default'):
            print("❌ 프롬프트 템플릿이 없어 분류 작업을 중단합니다.")
            return []
        if self.client is None:
            print("❌ OpenAI API 미연동 상태입니다. 전체 분류 작업을 중단합니다.")
            return []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 날짜 조건이 있으면 적용, 없으면 모든 기사 조회
            if start_date and end_date:
                cursor.execute("""
                    SELECT id, title, url, keyword, group_name, content, created_at, pub_date
                    FROM articles 
                    WHERE keyword = ? AND DATE(pub_date) BETWEEN ? AND ?
                    ORDER BY created_at DESC 
                """, (keyword, start_date, end_date))
            else:
                cursor.execute("""
                    SELECT id, title, url, keyword, group_name, content, created_at, pub_date
                    FROM articles 
                    WHERE keyword = ?
                    ORDER BY created_at DESC 
                """, (keyword,))
            articles = cursor.fetchall()
            print(f"키워드 '{keyword}'에 대해 {len(articles)}개의 기사를 분류합니다.")
            classification_results = []
            for article in articles:
                article_id, title, url, keyword, group_name, content, created_at, pub_date = article
                print(f"기사 ID {article_id} 분류 중...")
                # url + 키워드 중복 체크
                cursor.execute("SELECT COUNT(*) FROM classification_logs WHERE url = ? AND keyword = ?", (url, keyword))
                if cursor.fetchone()[0] > 0:
                    print(f"⚠️ 이미 저장된 url({url}) + 키워드({keyword})이므로 건너뜁니다.")
                    continue
                start_time = time.time()
                result = self.classify_article(title, content, keyword)
                processing_time = round(time.time() - start_time, 1)
                cursor.execute("""
                    INSERT INTO classification_logs 
                    (keyword, group_name, title, content, url, classification_result, confidence_score, reason, processing_time, created_at, is_saved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    keyword, 
                    group_name,
                    title,
                    content,  # articles의 content 값만 그대로 저장
                    url,  # 실제 URL 저장
                    result['classification'], 
                    result['confidence'],
                    result['reason'],
                    processing_time,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    0  # is_saved 기본값
                ))
                print(f"  제목: {title[:50]}...")
                print(f"  분류: {result['classification']}")
                print(f"  신뢰도: {result['confidence']:.2f}")
                print(f"  근거: {result['reason']}")
                print(f"  처리시간: {processing_time:.1f}초")
                print()
                classification_results.append({
                    'group_name': group_name,
                    'title': title,
                    'content': content,  # articles의 content 값만 그대로 저장
                    'url': url,
                    'classification_result': result['classification'],
                    'is_saved': 0,  # 또는 False
                    'confidence_score': result['confidence'],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'processing_time': processing_time,
                    'reason': result['reason']
                })
            conn.commit()
            conn.close()
            self._print_classification_summary(classification_results, keyword)
            return classification_results
        except Exception as e:
            print(f"기사 분류 중 오류: {e}")
            return []

    def _print_classification_summary(self, results: List[Dict], keyword: str):
        """분류 결과 요약을 출력합니다."""
        if not results:
            return
            
        print(f"\n=== '{keyword}' 키워드 분류 결과 요약 ===")
        
        # 분류별 통계
        classification_counts = {}
        for result in results:
            classification = result['classification_result']
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
        
        for classification, count in classification_counts.items():
            percentage = (count / len(results)) * 100
            print(f"{classification}: {count}개 ({percentage:.1f}%)")
        
        # 평균 신뢰도
        avg_confidence = sum(r['confidence_score'] for r in results) / len(results)
        print(f"평균 신뢰도: {avg_confidence:.2f}")
        print(f"총 처리된 기사: {len(results)}개")

    def get_classification_statistics(self, keyword: str = None) -> Dict:
        """분류 통계를 조회합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if keyword:
                cursor.execute("""
                    SELECT classification_result, COUNT(*) as count, AVG(confidence_score) as avg_confidence
                    FROM classification_logs 
                    WHERE keyword = ?
                    GROUP BY classification_result
                """, (keyword,))
            else:
                cursor.execute("""
                    SELECT classification_result, COUNT(*) as count, AVG(confidence_score) as avg_confidence
                    FROM classification_logs 
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
            print(f"통계 조회 중 오류: {e}")
            return {}

    def get_classification_progress(self) -> Dict:
        """분류 진행 상황을 조회합니다."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 전체 기사 수
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # 분류된 기사 수 (URL + 키워드 조합 기준)
            cursor.execute("""
                SELECT COUNT(DISTINCT url || '|' || keyword) 
                FROM classification_logs
            """)
            classified_articles = cursor.fetchone()[0]
            
            # 키워드별 분류 현황
            cursor.execute("""
                SELECT keyword, COUNT(*) as count
                FROM classification_logs
                GROUP BY keyword
                ORDER BY count DESC
            """)
            keyword_stats = cursor.fetchall()
            
            # 날짜별 분류 현황
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM classification_logs
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 10
            """)
            date_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_articles': total_articles,
                'classified_articles': classified_articles,
                'progress_percentage': round((classified_articles / total_articles * 100), 2) if total_articles > 0 else 0,
                'keyword_stats': {keyword: count for keyword, count in keyword_stats},
                'date_stats': {date: count for date, count in date_stats}
            }
            
        except Exception as e:
            print(f"진행 상황 조회 중 오류: {e}")
            return {}

def main():
    """메인 실행 함수 - 모든 기사 분류"""
    classifier = NewsAIClassifier()

    # 모든 키워드 조회 (날짜 제한 없음)
    conn = sqlite3.connect(classifier.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT keyword FROM articles")
    keywords = [row[0] for row in cursor.fetchall()]
    conn.close()

    print(f"총 {len(keywords)}개 키워드의 모든 기사를 분류합니다.")

    for keyword in keywords:
        print(f"\n{'='*50}")
        print(f"키워드 '{keyword}' 분류 시작")
        print(f"{('='*50)}")
        
        # 해당 키워드의 모든 기사 분류
        results = classifier.classify_articles_by_keyword(keyword)
        if results:
            print(f"\n키워드 '{keyword}' 분류 완료: {len(results)}개 기사 처리")
        else:
            print(f"\n키워드 '{keyword}'에 대한 분류할 기사가 없습니다.")

    # 전체 통계 출력
    print(f"\n{'='*50}")
    print("전체 분류 통계")
    print(f"{'='*50}")
    for keyword in keywords:
        stats = classifier.get_classification_statistics(keyword)
        print(f"\n{keyword}:")
        for classification, data in stats.items():
            print(f"  {classification}: {data['count']}개 (평균 신뢰도: {data['avg_confidence']})")

if __name__ == "__main__":
    main()
