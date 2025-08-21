import os
import sqlite3
import pandas as pd
import logging
from news_classifier import NewsClassifier
from dotenv import load_dotenv
import json
from datetime import datetime
import webbrowser
import time

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedVerification:
    """
    향상된 수동 검증 시스템
    - 분류 기준 가이드 제공
    - 빠른 검증 옵션
    - 진행률 표시
    - 일시 중단/재개 기능
    """
    
    def __init__(self, db_path=None, model_path="models"):
        self.db_path = db_path or os.getenv('DB_PATH')
        self.model_path = model_path
        self.classifier = NewsClassifier(db_path=db_path, model_path=model_path)
        
        # 브랜드 소유 관계 정의 (직접 소유 브랜드 + 자회사)
        self.brand_ownership = {
            "F&F": {
                "brands": ["MLB", "디스커버리", "디스커버리 익스페디션"],
                "subsidiaries": ["F&F엔터테인먼트", "F&F인터내셔널", "F&F홀딩스"]
            },
            "이랜드": {
                "brands": ["뉴발란스", "휠라"],
                "subsidiaries": ["이랜드월드", "이랜드리테일"]
            },
            "영원무역": {
                "brands": ["노스페이스"],
                "subsidiaries": []
            }
        }
        
        # 분류 기준 정의
        self.classification_guide = {
            "보도자료": [
                "기업이나 조직에서 공식적으로 발표한 내용",
                "언론사가 기업의 보도자료를 그대로 게재",
                "기업의 성과, 실적, 계획 등을 홍보하는 내용",
                "기업명이 제목에 포함되고 홍보성 내용",
                "본문에 '~관계자에 의하면', '브랜드 관계자 측은', 'OO사 관계자는' 등의 표현",
                "기업이 소유한 브랜드들의 활동을 홍보하는 내용",
                "사회공헌활동, 환경보호활동 등 기업의 긍정적 활동 홍보",
                "⚠️ 기자가 여러 브랜드의 보도자료를 합쳐서 편집한 기사도 보도자료",
                "⚠️ 제목에 여러 브랜드명이 나열되어 있어도 본문에 보도자료 특성이 있으면 보도자료",
                "⚠️ 브랜드 소유 관계: F&F(MLB, 디스커버리 + F&F엔터테인먼트 등 자회사), 이랜드(뉴발란스, 휠라), 노스페이스(독립)",
                "⚠️ 수집 키워드와 실제 보도자료 주체가 다를 수 있습니다 (예: 디스커버리 키워드로 수집했지만 F&F의 보도자료)",
                "예시: 'OO기업, 매출 20% 증가 발표', 'OO사 신제품 출시', 'F&F, MLB·디스커버리 매장에 의류수거함 설치', '이랜드 뉴발란스, 2025 멤버스위크 캠페인 개최'"
            ],
            "오가닉": [
                "언론사가 독립적으로 작성한 기사",
                "기업이나 조직과 무관한 객관적 분석",
                "시장 동향, 트렌드 분석 등",
                "기업명이 언급되지만 홍보성이 아닌 내용",
                "여러 브랜드 혹은 기업명이 같이 언급되는 내용",
                "⚠️ 중요: 키워드로 수집된 기사는 해당 기업 관련 내용이 본문에 포함되어 있을 가능성이 높음",
                "⚠️ 주식/금융 관련 제목이라도 본문에 키워드 기업 내용이 있으면 '오가닉'일 수 있음",
                "⚠️ 연예인/인플루언서가 브랜드 제품을 착용하는 라이프스타일/트렌드 기사",
                "예시: 'IT업계 동향 분석', '시장 변화에 따른 OO기업 영향', '상승률 상위 50선 - 코스피(본문에 F&F 언급)', '차은우 러닝 기사(노스페이스 제품 착용)'"
            ],
            "해당없음": [
                "키워드와 관련이 없는 내용",
                "단순히 키워드만 언급되고 실제 내용은 다른 주제",
                "스팸성이나 광고성 내용",
                "본문을 확인해도 키워드 기업과 전혀 관련 없는 내용",
                "⚠️ 다른 기업의 이벤트/할인행사에서 키워드 브랜드가 참여하는 경우",
                "⚠️ 키워드 브랜드가 언급되지만 실제 주체는 다른 기업인 경우",
                "⚠️ 제목은 일반적이지만 본문에 키워드 관련 내용이 포함된 경우 (재검토 필요)",
                "⚠️ 연예인/인플루언서가 브랜드 제품을 착용하는 경우는 '오가닉'으로 분류",
                "예시: 'OO기업 주식 투자 팁', 'OO사 관련 루머', '쿠팡 티셔츠 페어에 뉴발란스 참여', '[경제계 인사] 뉴발란스코리아 대표 (본문에 보도자료 특성)', '차은우 러닝 기사 (노스페이스 제품 착용)'"
            ]
        }
    
    def show_classification_guide(self):
        """분류 기준 가이드 표시"""
        print("\n" + "="*80)
        print("📋 분류 기준 가이드")
        print("="*80)
        
        for category, criteria in self.classification_guide.items():
            print(f"\n🔸 {category}:")
            for i, criterion in enumerate(criteria, 1):
                print(f"   {i}. {criterion}")
        
        print("\n" + "="*80)
        input("가이드를 확인했습니다. Enter를 눌러 계속하세요...")
    
    def predict_and_verify_enhanced(self, limit=20, auto_open_url=False):
        """
        향상된 예측 및 검증 시스템
        
        Args:
            limit: 검증할 데이터 개수
            auto_open_url: URL 자동 열기 여부
        """
        try:
            logger.info("🔍 향상된 예측 및 검증 시작...")
            
            # 분류 기준 가이드 표시
            self.show_classification_guide()
            
            # 모델 로드
            if not self.classifier.load_koelectra_model():
                logger.error("모델 로드 실패!")
                return
            
            # 미분류 데이터 가져오기 (group_name별 최신순)
            conn = sqlite3.connect(self.db_path)

            # 1단계: 사용 가능한 group_name들 조회
            group_query = """
            SELECT DISTINCT a.group_name, COUNT(*) as count
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE cl.url IS NULL
            GROUP BY a.group_name
            ORDER BY count DESC
            """
            group_df = pd.read_sql_query(group_query, conn)

            if len(group_df) == 0:
                logger.warning("검증할 미분류 데이터가 없습니다.")
                conn.close()
                return

            print(f"\n📊 사용 가능한 그룹 현황:")
            for _, row in group_df.iterrows():
                print(f"  {row['group_name']}: {row['count']}개")

            # 2단계: 각 group_name별로 최신순으로 균등하게 데이터 수집
            articles_per_group = max(1, limit // len(group_df))  # 그룹당 최소 1개
            remaining = limit % len(group_df)  # 남은 개수

            all_articles = []

            for idx, group_row in group_df.iterrows():
                group_name = group_row['group_name']
                current_limit = articles_per_group + (1 if idx < remaining else 0)

                # 모든 그룹에서 균형잡힌 선택 (F&F 특별 키워드는 검증 과정에서만 안내)
                article_query = """
                SELECT a.id, a.title, a.content, a.keyword, a.group_name, a.created_at, a.url
                FROM articles a
                LEFT JOIN classification_logs cl ON a.url = cl.url
                WHERE cl.url IS NULL AND a.group_name = ?
                ORDER BY RANDOM()
                LIMIT ?
                """

                group_articles = pd.read_sql_query(article_query, conn, params=[group_name, current_limit])
                all_articles.append(group_articles)

                print(f"  {group_name}: {len(group_articles)}개 선택")

            conn.close()

            # 모든 그룹의 데이터 합치기
            df = pd.concat(all_articles, ignore_index=True)

            print(f"\n✅ 총 {len(df)}개 기사를 {len(group_df)}개 그룹에서 최신순으로 균등하게 선택했습니다.")

            if len(df) == 0:
                logger.warning("검증할 미분류 데이터가 없습니다.")
                return
            
            # 검증 결과 저장용
            verification_results = []
            session_file = os.path.join(self.model_path, "verification_session.json")
            
            # 이전 세션 복구
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        verification_results = json.load(f)
                    print(f"📂 이전 세션에서 {len(verification_results)}개 검증 결과를 복구했습니다.")
                except:
                    verification_results = []
            
            # 이미 검증된 ID들
            verified_ids = {r['id'] for r in verification_results}
            
            # 검증 시작 (그룹별로 섞어서 진행)
            import random
            df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)  # 랜덤 섞기
            
            for idx, row in df_shuffled.iterrows():
                if row['id'] in verified_ids:
                    continue
                
                try:
                    result = self.classifier.predict(row['title'], row['content'], row['keyword'])
                    
                    print(f"\n{'='*80}")
                    print(f"📰 기사 {len(verification_results)+1}/{len(df)}")
                    print(f"ID: {row['id']}")
                    print(f"키워드: {row['keyword']}")
                    print(f"그룹: {row['group_name']} ({df_shuffled['group_name'].value_counts()[row['group_name']]}개 중)")
                    print(f"날짜: {row['created_at']}")
                    
                    # 기본 정보 표시
                    print(f"\n📋 제목: {row['title']}")
                    print(f"🔗 URL: {row['url']}")
                    print(f"📏 내용 길이: {len(row['content'])}자")
                    
                    # 제목 vs 본문 불일치 감지
                    title_content_mismatch = self.detect_title_content_mismatch(row)
                    if title_content_mismatch:
                        print(f"\n⚠️  제목-본문 불일치 감지: {title_content_mismatch}")
                    
                    # ML이 먼저 사유 생성
                    ml_reason = self.generate_ml_reason(row, result)
                    print(f"\n🤖 ML 사유: {ml_reason}")
                    
                    print(f"\n📊 모델 예측:")
                    print(f"  분류: {result['classification']}")
                    print(f"  신뢰도: {result['confidence']:.3f}")
                    
                    # 확률 분포 표시
                    probs = result['probabilities']
                    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                    print(f"  확률 분포:")
                    for class_name, prob in sorted_probs:
                        bar = "█" * int(prob * 20)
                        print(f"    {class_name}: {prob:.3f} {bar}")
                    
                    # 검증 옵션
                    print(f"\n🚀 검증 옵션:")
                    print(f"  y = 예측이 맞음 (원본 기사 확인 후)")
                    print(f"  n = 예측이 틀림 (원본 기사 확인 후 수정)")
                    print(f"  s = 건너뛰기")
                    print(f"  q = 종료 (현재까지 저장)")
                    print(f"  u = URL 열기")
                    print(f"  f = 전체 내용 보기")
                    
                    while True:
                        user_input = input(f"\n🤔 선택: ").lower().strip()
                        
                        if user_input == 'q':
                            # 세션 저장 후 종료
                            self.save_session(verification_results, session_file)
                            print("💾 세션을 저장하고 종료합니다.")
                            return
                        elif user_input == 'u' and row['url']:
                            try:
                                webbrowser.open(row['url'])
                                print("🌐 브라우저에서 URL을 열었습니다.")
                            except:
                                print("❌ URL을 열 수 없습니다.")
                            continue
                        elif user_input == 'f':
                            print(f"\n📄 전체 내용:")
                            print(f"{'='*80}")
                            print(f"{row['content']}")
                            print(f"{'='*80}")
                            continue
                        elif user_input in ['y', 'n', 's']:
                            break
                        else:
                            print("y, n, s, q, u, f 중에서 선택해주세요.")
                    
                    if user_input == 's':
                        print("건너뜀")
                        continue
                    
                    # 검증 결과 저장
                    verification_result = {
                        'id': row['id'],
                        'title': row['title'],
                        'content': row['content'],
                        'keyword': row['keyword'],
                        'group_name': row['group_name'],
                        'url': row['url'],
                        'created_at': row['created_at'],
                        'predicted_class': result['classification'],
                        'confidence': result['confidence'],
                        'probabilities': result['probabilities'],
                        'ml_reason': ml_reason,
                        'is_correct': user_input == 'y',
                        'verified_at': datetime.now().isoformat()
                    }
                    
                    if user_input == 'n':
                        # 틀린 경우 분류와 사유 수정
                        final_classification, final_reason = self.modify_classification_and_reason(
                            row, result, ml_reason
                        )
                        verification_result['correct_label'] = final_classification
                        verification_result['correct_reason'] = final_reason
                        verification_result['confidence'] = 1.0  # 수동 수정이므로 1.0
                        print(f"✅ 수정 완료: {final_classification} - {final_reason}")
                    else:
                        # 맞는 경우 ML 사유 그대로 사용
                        verification_result['correct_label'] = result['classification']
                        verification_result['correct_reason'] = ml_reason
                        # ML의 confidence_score 그대로 사용
                    
                    verification_results.append(verification_result)
                    
                    # 즉시 DB에 저장
                    self.save_single_to_database(verification_result)
                    
                    # 세션 자동 저장
                    self.save_session(verification_results, session_file)
                    
                except Exception as e:
                    logger.error(f"검증 중 오류 (ID: {row['id']}): {e}")
            
            # 최종 결과 저장
            self.save_final_results(verification_results)
            
            # 통계 출력
            self.show_statistics(verification_results)
            
            # 세션 파일 정리
            if os.path.exists(session_file):
                os.remove(session_file)
                print("🧹 세션 파일을 정리했습니다.")
            
        except Exception as e:
            logger.error(f"향상된 예측 및 검증 중 오류: {e}")
    
    def save_session(self, results, session_file):
        """세션 저장"""
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"세션 저장 중 오류: {e}")
    
    def save_final_results(self, results):
        """최종 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"verification_results_{timestamp}.json"
        filepath = os.path.join(self.model_path, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 최종 검증 결과 저장 완료: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"최종 결과 저장 중 오류: {e}")
            return None
    
    def show_statistics(self, results):
        """통계 출력"""
        if not results:
            return
        
        correct_count = sum(1 for r in results if r['is_correct'])
        total_count = len(results)
        
        print(f"\n{'='*80}")
        print(f"📊 최종 검증 결과:")
        print(f"  총 검증: {total_count}개")
        print(f"  정확: {correct_count}개")
        print(f"  부정확: {total_count - correct_count}개")
        print(f"  정확도: {correct_count/total_count*100:.1f}%")
        
        # 분류별 통계
        print(f"\n📈 분류별 통계:")
        class_stats = {}
        for r in results:
            pred_class = r['predicted_class']
            if pred_class not in class_stats:
                class_stats[pred_class] = {'total': 0, 'correct': 0}
            class_stats[pred_class]['total'] += 1
            if r['is_correct']:
                class_stats[pred_class]['correct'] += 1
        
        for class_name, stats in class_stats.items():
            accuracy = stats['correct'] / stats['total'] * 100
            print(f"  {class_name}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
        
        # 그룹별 통계
        print(f"\n📊 그룹별 통계:")
        group_stats = {}
        for r in results:
            group_name = r['group_name']
            if group_name not in group_stats:
                group_stats[group_name] = {'total': 0, 'correct': 0}
            group_stats[group_name]['total'] += 1
            if r['is_correct']:
                group_stats[group_name]['correct'] += 1
        
        for group_name, stats in group_stats.items():
            accuracy = stats['correct'] / stats['total'] * 100
            print(f"  {group_name}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
    
    def detect_title_content_mismatch(self, row):
        """제목과 본문의 불일치를 감지"""
        title = row['title'].lower()
        content = row['content'].lower()
        keyword = row['keyword'].lower()
        
        # 제목에 키워드가 없지만 본문에 있는 경우
        if keyword not in title and keyword in content:
            # 제목이 일반적인 패턴인지 확인
            general_title_patterns = [
                '경제계 인사', '인사', '부임', '임명', '이사', '대표',
                '시장 동향', '업계 동향', '트렌드', '분석',
                '주식', '투자', '증시', '코스피',
                '뉴스', '소식', '전망', '전망'
            ]
            
            for pattern in general_title_patterns:
                if pattern in title:
                    return f"제목은 '{pattern}'이지만 본문에 '{keyword}' 관련 내용이 포함됨"
        
        # 제목에 키워드가 있지만 본문에 보도자료 특성이 있는 경우
        if keyword in title:
            press_release_indicators = [
                '~밝혔다', '~전했다', '~발표했다', '~소개했다',
                '관계자에 의하면', '브랜드 관계자 측은', '관계자는'
            ]
            
            for indicator in press_release_indicators:
                if indicator in content:
                    return f"제목에 '{keyword}'가 있지만 본문에 보도자료 특성('{indicator}') 발견"
        
        # 연예인/인플루언서 제품 착용 감지
        celebrity_patterns = [
            '차은우', '아이유', '뉴진스', '블랙핑크', '방탄소년단', '세븐틴',
            '연예인', '배우', '가수', '아이돌', '인플루언서', '유튜버',
            '스타', '셀럽', '유명인'
        ]
        
        for celebrity in celebrity_patterns:
            if celebrity in content and keyword in content:
                return f"연예인/인플루언서('{celebrity}')가 '{keyword}' 제품을 착용하는 내용 포함"
        
        # 모기업-브랜드 관계 감지 (한글-영문 변형 포함)
        company_brand_relations = {
            "F&F": ["F&F", "에프앤에프", "에프앤에프홀딩스"],
            "이랜드": ["이랜드", "E-LAND", "이랜드월드"],
            "영원무역": ["영원무역", "영원무역그룹"]
        }
        
        for parent_company, variations in company_brand_relations.items():
            # 제목에 모기업이 있지만 키워드는 브랜드인 경우
            if any(variation in title for variation in variations):
                # 브랜드 소유 관계 확인
                for brand_company, ownership_info in self.brand_ownership.items():
                    if brand_company == parent_company:
                        owned_brands = ownership_info["brands"]
                        if keyword in owned_brands:
                            return f"제목에 모기업 '{parent_company}'이 있지만 키워드는 소유 브랜드 '{keyword}'임 (모기업 보도자료 가능성)"
        
        return None
    
    def generate_ml_reason(self, row, result):
        """ML이 예측 근거를 생성"""
        classification = result['classification']
        confidence = result['confidence']
        title = row['title']
        content = row['content']
        keyword = row['keyword']
        
        # 제목-본문 불일치 감지
        mismatch = self.detect_title_content_mismatch(row)
        
        # 기본 사유 템플릿
        reasons = {
            "보도자료": [
                f"제목에 '{keyword}' 관련 내용이 포함되어 있고, 본문에 보도자료 특성 표현이 발견됨",
                f"'{keyword}' 기업의 공식 발표나 홍보 내용으로 판단됨",
                f"기업 관계자 언급과 함께 '{keyword}' 관련 정보가 포함됨"
            ],
            "오가닉": [
                f"언론사가 독립적으로 작성한 '{keyword}' 관련 기사로 판단됨",
                f"객관적 분석이나 시장 동향에 '{keyword}'가 언급됨",
                f"홍보성이 아닌 정보성 내용에 '{keyword}'가 포함됨"
            ],
            "해당없음": [
                f"제목과 내용에서 '{keyword}'와 관련이 없는 주제로 판단됨",
                f"'{keyword}'가 단순히 언급되었지만 실제 내용은 다른 주제",
                f"다른 기업의 이벤트에서 '{keyword}'가 참여 브랜드로만 언급됨"
            ]
        }
        
        # 불일치가 있는 경우 사유 수정
        if mismatch:
            if classification == "해당없음" and keyword in content.lower():
                # 연예인 착용 케이스 확인
                celebrity_found = None
                celebrity_patterns = ['차은우', '아이유', '뉴진스', '블랙핑크', '방탄소년단', '세븐틴', '연예인', '배우', '가수', '아이돌', '인플루언서', '유튜버', '스타', '셀럽', '유명인']
                for celebrity in celebrity_patterns:
                    if celebrity in content.lower():
                        celebrity_found = celebrity
                        break
                
                # 모기업-브랜드 관계 케이스 확인
                company_brand_relations = {
                    "F&F": ["F&F", "에프앤에프", "에프앤에프홀딩스"],
                    "이랜드": ["이랜드", "E-LAND", "이랜드월드"],
                    "영원무역": ["영원무역", "영원무역그룹"]
                }
                
                parent_company_found = None
                for parent_company, variations in company_brand_relations.items():
                    if any(variation in title.lower() for variation in variations):
                        # 브랜드 소유 관계 확인
                        for brand_company, ownership_info in self.brand_ownership.items():
                            if brand_company == parent_company:
                                owned_brands = ownership_info["brands"]
                                if keyword in owned_brands:
                                    parent_company_found = parent_company
                                    break
                        if parent_company_found:
                            break
                
                if celebrity_found:
                    reasons["오가닉"] = [
                        f"연예인/인플루언서('{celebrity_found}')가 '{keyword}' 제품을 착용하는 내용이 포함된 오가닉 기사",
                        f"트렌드/라이프스타일 기사에 '{keyword}' 제품 착용 내용 포함",
                        f"연예인 관련 기사에 '{keyword}' 브랜드 제품이 언급됨"
                    ]
                elif parent_company_found:
                    reasons["해당없음"] = [
                        f"제목에 모기업 '{parent_company_found}'이 있지만 키워드는 소유 브랜드 '{keyword}'임 (모기업 보도자료 가능성)",
                        f"모기업 관련 기사이므로 브랜드 키워드와는 직접적 관련 없음",
                        f"제목과 키워드가 다른 주체를 가리킴 (모기업 vs 브랜드)"
                    ]
                else:
                    reasons["해당없음"] = [
                        f"제목은 일반적이지만 본문에 '{keyword}' 관련 내용이 포함됨 (재검토 필요)",
                        f"제목과 본문 내용이 다름 - 본문 확인 필요",
                        f"제목만으로는 판단 어려움 - 본문 내용 기반으로 분류 필요"
                    ]
            elif classification == "보도자료":
                reasons["보도자료"] = [
                    f"제목은 일반적이지만 본문에 '{keyword}' 보도자료 특성 발견",
                    f"본문에 기업 관계자 언급과 함께 '{keyword}' 관련 정보 포함",
                    f"제목과 달리 본문은 '{keyword}' 기업의 공식 발표 내용"
                ]
        
        # 신뢰도에 따른 사유 선택
        if confidence > 0.7:
            reason = reasons[classification][0]
        elif confidence > 0.5:
            reason = reasons[classification][1]
        else:
            reason = reasons[classification][2]
        
        return reason
    
    def modify_classification_and_reason(self, row, result, ml_reason):
        """분류와 사유를 수정"""
        print(f"\n📝 분류와 사유를 수정해주세요:")
        print(f"현재 ML 예측: {result['classification']} - {ml_reason}")
        
        # 분류 선택
        print(f"\n🔸 분류 선택:")
        for i, category in enumerate(self.classification_guide.keys(), 1):
            print(f"{i}. {category}")
        
        while True:
            try:
                label_input = int(input("분류 선택 (1/2/3): ").strip())
                if label_input in [1, 2, 3]:
                    break
                print("1, 2, 또는 3을 입력해주세요.")
            except ValueError:
                print("숫자를 입력해주세요.")
        
        label_map = {1: '보도자료', 2: '오가닉', 3: '해당없음'}
        final_classification = label_map[label_input]
        
        # 사유 수정
        print(f"\n📝 사유 수정:")
        print(f"현재 사유: {ml_reason}")
        print(f"새로운 사유를 입력하세요 (Enter로 현재 사유 유지):")
        
        new_reason = input("사유: ").strip()
        if not new_reason:
            new_reason = ml_reason
        
        return final_classification, new_reason
    
    def save_single_to_database(self, verification_result):
        """개별 검증 결과를 즉시 DB에 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # classification_logs 테이블에 저장 (실제 스키마에 맞게)
            cursor.execute("""
                INSERT OR REPLACE INTO classification_logs 
                (url, title, content, keyword, group_name, classification_result, reason, 
                 confidence_score, created_at, is_saved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                verification_result['url'],
                verification_result['title'],
                verification_result['content'],
                verification_result['keyword'],
                verification_result['group_name'],
                verification_result['correct_label'],
                verification_result['correct_reason'],
                verification_result['confidence'],
                verification_result['verified_at'],
                True  # 수동 검증 완료 표시
            ))
            
            conn.commit()
            conn.close()
            
            confidence_display = f"{verification_result['confidence']:.3f}"
            if verification_result['confidence'] == 1.0:
                confidence_display = "1.000 (수동수정)"
            print(f"💾 DB 저장 완료: {verification_result['correct_label']} (신뢰도: {confidence_display}) - {verification_result['correct_reason'][:50]}...")
            
        except Exception as e:
            logger.error(f"개별 DB 저장 중 오류: {e}")
            print(f"❌ DB 저장 실패: {e}")
    
    def save_to_database(self, verification_results):
        """검증 결과를 DB에 저장 (기존 함수 - 호환성 유지)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for result in verification_results:
                # classification_logs 테이블에 저장 (실제 스키마에 맞게)
                cursor.execute("""
                    INSERT OR REPLACE INTO classification_logs 
                    (url, title, content, keyword, group_name, classification_result, reason, 
                     confidence_score, created_at, is_saved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result['url'],
                    result['title'],
                    result['content'],
                    result['keyword'],
                    result['group_name'],
                    result['correct_label'],
                    result['correct_reason'],
                    result['confidence'],
                    result['verified_at'],
                    True  # 수동 검증 완료 표시
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 {len(verification_results)}개 검증 결과를 DB에 저장했습니다.")
            
        except Exception as e:
            logger.error(f"DB 저장 중 오류: {e}")
    
    def get_wrong_predictions_from_verification(self, verification_file):
        """검증 결과에서 틀린 예측들 추출"""
        try:
            with open(verification_file, 'r', encoding='utf-8') as f:
                verification_data = json.load(f)
            
            # 틀린 예측들만 필터링
            wrong_predictions = []
            for item in verification_data:
                if not item['is_correct'] and 'correct_label' in item:
                    wrong_predictions.append({
                        'title': item['title'],
                        'content': item['content'],
                        'keyword': item['keyword'],
                        'classification_result': item['correct_label']
                    })
            
            logger.info(f"📊 검증 결과에서 틀린 예측 {len(wrong_predictions)}개 추출")
            return wrong_predictions
            
        except Exception as e:
            logger.error(f"검증 결과 로드 중 오류: {e}")
            return []

def main():
    """메인 실행 함수"""
    logger.info("=== 향상된 수동 검증 시스템 시작 ===")
    
    verifier = EnhancedVerification()
    
    # 설정 입력
    try:
        limit = int(input("검증할 데이터 개수를 입력하세요 (기본값: 20): ") or "20")
    except ValueError:
        limit = 20
    
    auto_open_input = input("URL을 자동으로 열까요? (y/n, 기본값: n): ").lower().strip()
    auto_open = auto_open_input == 'y' if auto_open_input else False
    
    if auto_open:
        print("⚠️  자동 URL 열기는 권장하지 않습니다. 수동 검증이 어려워집니다.")
        confirm = input("정말 자동으로 열까요? (y/n): ").lower().strip()
        if confirm != 'y':
            auto_open = False
            print("✅ 수동 모드로 변경했습니다.")
    
    print(f"\n💡 검증 팁:")
    print(f"  1. 원본 기사를 반드시 확인하세요 (URL 클릭)")
    print(f"  2. 제목만으로는 정확한 분류가 어려울 수 있습니다")
    print(f"  3. 기사 내용을 읽고 분류 기준에 따라 판단하세요")
    print(f"  4. 확실하지 않으면 's'로 건너뛰세요")
    print(f"  5. 'c' 옵션으로 URL을 복사할 수 있습니다")
    print(f"  6. 'f' 옵션으로 전체 내용을 터미널에서 확인할 수 있습니다")
    print(f"  7. 각 기사마다 y/n/s/q 중 하나를 선택해야 다음으로 넘어갑니다")
    print(f"\n" + "="*80)
    
    # 향상된 예측 및 검증 실행
    verifier.predict_and_verify_enhanced(limit=limit, auto_open_url=auto_open)
    
    logger.info("=== 향상된 수동 검증 완료 ===")

if __name__ == "__main__":
    main() 