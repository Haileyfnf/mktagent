"""
AI 기반 마케팅 분석 보고서 서비스
GPT API를 사용하여 온톨로지 데이터를 분석하고 인사이트 보고서 생성
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import anthropic
from loguru import logger
from pydantic import BaseModel

from .snowflake_service import get_snowflake_service
from .ontology_duckdb import ontology_db


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    analysis_type: str  # "campaign_performance", "delivery_analysis", "influencer_insights"
    days_back: int = 30
    brand_id: Optional[str] = None
    include_recommendations: bool = True


class AnalysisReport(BaseModel):
    """분석 보고서 모델"""
    title: str
    analysis_type: str
    generated_at: datetime
    data_period: str
    markdown_content: str
    key_insights: List[str]
    recommendations: List[str]


class AIAnalysisService:
    """AI 기반 분석 서비스"""
    
    def __init__(self):
        """AI 분석 서비스 초기화"""
        self.claude_client = anthropic.Anthropic(
            api_key=os.getenv("CLAUDE_API_KEY")
        )
        # 절대경로로 reports 디렉토리 설정 (backend/src/reports)
        current_file = Path(__file__)
        src_root = current_file.parent.parent  # backend/src/services -> backend/src/
        self.output_dir = src_root / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("AI 분석 서비스 초기화 완료")
    
    def _build_ontology_context(self) -> str:
        """온톨로지 정보를 프롬프트 컨텍스트로 구성"""
        try:
            # 온톨로지 데이터 로드
            ontology_db.load_all()
            
            # 비즈니스 룰 조회
            business_rules = ontology_db.get_business_rules()
            rules_context = []
            for rule in business_rules:
                if hasattr(rule, 'name') and hasattr(rule, 'description'):
                    rules_context.append(f"- {rule.name}: {rule.description}")
            
            # 도메인과 개념 조회
            domains = ontology_db.get_all_domains()
            domain_concepts = {}
            for domain in domains:
                try:
                    concepts_dict = ontology_db.get_domain_concepts(domain)  # Dict[str, DomainConcept] 반환
                    concepts_list = list(concepts_dict.values())  # DomainConcept 객체들의 리스트
                    domain_concepts[domain] = [concept.name for concept in concepts_list[:3] if hasattr(concept, 'name')]  # 상위 3개만
                except Exception as domain_err:
                    logger.warning(f"도메인 {domain} 개념 조회 실패: {domain_err}")
                    domain_concepts[domain] = []
            
            # 도메인 관계 조회
            try:
                relations = list(ontology_db.get_domain_relations())  # 리스트로 변환
                relation_context = []
                for relation in relations[:5]:  # 상위 5개만
                    if hasattr(relation, 'from_entity') and hasattr(relation, 'to_entity') and hasattr(relation, 'description'):
                        relation_context.append(f"- {relation.from_entity} → {relation.to_entity}: {relation.description}")
            except Exception as rel_err:
                logger.warning(f"도메인 관계 조회 실패: {rel_err}")
                relation_context = []
            
            # 테이블 매핑 정보 조회
            try:
                table_mappings = ontology_db.get_all_table_mappings()
                table_context = []
                for domain, mappings in table_mappings.items():
                    if mappings:  # 매핑이 있는 경우에만
                        mapping_items = [f"{concept} → {table}" for concept, table in mappings.items()]
                        table_context.append(f"**{domain}**: {', '.join(mapping_items)}")
            except Exception as table_err:
                logger.warning(f"테이블 매핑 조회 실패: {table_err}")
                table_context = []
            
            # 컨텍스트 생성 시 빈 리스트 처리
            rules_section = chr(10).join(rules_context) if rules_context else "- 기본 비즈니스 룰이 적용됩니다"
            domains_section = chr(10).join([f"**{domain}**: {', '.join(concepts)}" for domain, concepts in domain_concepts.items() if concepts]) if domain_concepts else "- 기본 도메인 개념을 사용합니다"
            tables_section = chr(10).join(table_context) if table_context else "- 기본 테이블 매핑을 사용합니다"
            relations_section = chr(10).join(relation_context) if relation_context else "- 기본 도메인 관계를 고려합니다"
            
            ontology_context = f"""
## F&F 인플루언서 마케팅 온톨로지 기반 분석 가이드

### 핵심 비즈니스 룰
{rules_section}

### 도메인별 주요 개념
{domains_section}

### 실제 데이터베이스 테이블 매핑
{tables_section}

### 도메인 간 관계
{relations_section}

### 분석 시 고려사항
- 위 비즈니스 룰을 기반으로 성과 지표를 평가하세요
- 각 도메인(마케팅, 상품, 배송)의 연관성을 고려한 분석을 제공하세요
- 온톨로지에 정의된 관계를 바탕으로 개선 방안을 제시하세요
"""
            
            return ontology_context
            
        except Exception as e:
            logger.warning(f"온톨로지 컨텍스트 생성 실패: {e}")
            return """## 기본 분석 가이드

### 분석 원칙
- 데이터 기반의 객관적인 분석을 제공하세요
- 실행 가능한 개선 방안을 제시하세요
- 마케팅, 상품, 배송 도메인의 연관성을 고려하세요

### 주요 성과 지표
- 캠페인 성공률 및 완료율
- 인플루언서 참여율 및 콘텐츠 업로드율
- 배송 완료율 및 시딩 효과성
- 브랜드별 캠페인 효율성
"""

    def _check_business_rule_violations(self, campaigns, campaign_influencers, delivery_entries) -> str:
        """비즈니스 룰 위반 상황 분석"""
        try:
            violations = []
            
            # 컨텐츠 업로드 지연 체크 (7일 이상 지연)
            overdue_content = 0
            for ci in campaign_influencers:
                if ci.get('CAST_STATUS') == 'ACCEPTED' and not ci.get('CONTENTS_POST_DT'):
                    cast_date = ci.get('CAST_MSG_DT')
                    if cast_date and isinstance(cast_date, str):
                        try:
                            cast_dt = datetime.strptime(cast_date, '%Y-%m-%d')
                            if (datetime.now() - cast_dt).days > 7:
                                overdue_content += 1
                        except:
                            pass
            
            if overdue_content > 0:
                violations.append(f"- 컨텐츠 업로드 지연: {overdue_content}건 (7일 초과)")
            
            # 배송 지연 체크
            overdue_delivery = 0
            for delivery in delivery_entries:
                if delivery.get('STATUS') in ['DELIVERY_IN_PROGRESS', 'READY']:
                    create_date = delivery.get('CREATE_DT')
                    if create_date and isinstance(create_date, str):
                        try:
                            create_dt = datetime.strptime(create_date, '%Y-%m-%d')
                            if (datetime.now() - create_dt).days > 5:
                                overdue_delivery += 1
                        except:
                            pass
            
            if overdue_delivery > 0:
                violations.append(f"- 배송 지연: {overdue_delivery}건 (5일 초과)")
            
            # 캠페인 참여율 체크
            if campaigns and campaign_influencers:
                participation_rate = len(campaign_influencers) / len(campaigns)
                if participation_rate < 5:  # 캠페인당 평균 5명 미만
                    violations.append(f"- 인플루언서 참여율 저조: 캠페인당 평균 {participation_rate:.1f}명")
            
            if violations:
                return "### ⚠️ 비즈니스 룰 위반 감지\n" + "\n".join(violations)
            else:
                return "### ✅ 비즈니스 룰 준수 양호\n- 주요 위반 사항 없음"
                
        except Exception as e:
            logger.warning(f"비즈니스 룰 체크 실패: {e}")
            return "### 📋 비즈니스 룰 체크\n- 체크 과정에서 오류 발생"

    def _call_claude_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """Claude API 호출 (온톨로지 컨텍스트 포함)"""
        try:
            # 온톨로지 컨텍스트 추가
            ontology_context = self._build_ontology_context()
            
            # 시스템 메시지에 온톨로지 정보 포함
            system_message = f"""당신은 F&F의 인플루언서 마케팅 데이터 분석 전문가입니다. 

{ontology_context}

주어진 데이터와 위의 온톨로지 정보를 바탕으로 통찰력 있는 분석과 실행 가능한 권장사항을 제공하세요."""
            
            # Claude API 호출
            response = self.claude_client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                max_tokens=max_tokens,
                temperature=0.7,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
            raise
    
    def _save_markdown_report(self, content: str, filename: str) -> str:
        """마크다운 보고서 파일 저장"""
        try:
            file_path = self.output_dir / f"{filename}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"보고서 저장 완료: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"보고서 저장 실패: {e}")
            raise
    
    def analyze_campaign_performance(self, days_back: int = 30, brand_id: str = None, specific_month: str = None) -> AnalysisReport:
        """캠페인 성과 분석"""
        logger.info(f"캠페인 성과 분석 시작 - 최근 {days_back}일")
        
        try:
            # 특정 월 지정된 경우 (예: "2024-07")
            if specific_month:
                logger.info(f"특정 월 분석: {specific_month}")
                month_start = datetime.strptime(f"{specific_month}-01", "%Y-%m-%d")
                if month_start.month == 12:
                    month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
                
                # 특정 월 캠페인 조회 쿼리 (캠페인 기간이 해당 월과 겹치는 모든 캠페인)
                campaigns_query = f"""
                SELECT id, camp_code, camp_nm, start_date, end_date, status, 
                       target_cnt, brand_id, engmt_avg, engmt_cnt, part_cds, campaign_hashtags
                FROM campaign 
                WHERE (
                    START_DATE BETWEEN '{month_start.strftime('%Y-%m-%d')}' AND '{month_end.strftime('%Y-%m-%d')}'
                    OR END_DATE BETWEEN '{month_start.strftime('%Y-%m-%d')}' AND '{month_end.strftime('%Y-%m-%d')}'
                )
                {f"AND brand_id = '{brand_id}'" if brand_id else ""}
                ORDER BY start_date
                """
                campaigns = get_snowflake_service().execute_query(campaigns_query)
                
                # 해당 캠페인의 인플루언서들
                if campaigns:
                    campaign_ids = [str(c['id']) for c in campaigns]
                    campaign_ids_str = "', '".join(campaign_ids)
                    
                    influencers_query = f"""
                    SELECT id, cast_msg_dt, cast_status, contents_post_dt, 
                           progress, brand_id, campaign_id, influencer_id
                    FROM campaign_influencer 
                    WHERE campaign_id IN ('{campaign_ids_str}')
                    """
                    campaign_influencers = get_snowflake_service().execute_query(influencers_query)
                    
                    # 해당 인플루언서들의 배송
                    if campaign_influencers:
                        influencer_ids = [str(ci['id']) for ci in campaign_influencers]
                        influencer_ids_str = "', '".join(influencer_ids)
                        
                        deliveries_query = f"""
                        SELECT id, create_dt, delivery_confirm_dt, status, 
                               brand_id, campaign_influencer_id, qty, price_total
                        FROM delivery_entry 
                        WHERE campaign_influencer_id IN ('{influencer_ids_str}')
                        """
                        delivery_entries = get_snowflake_service().execute_query(deliveries_query)
                    else:
                        delivery_entries = []
                else:
                    campaign_influencers = []
                    delivery_entries = []
            else:
                # 기존 방식 (최근 N일)
                campaigns = get_snowflake_service().get_campaigns(active_only=False, brand_id=brand_id)
                campaign_influencers = get_snowflake_service().get_campaign_influencers()
                delivery_entries = get_snowflake_service().get_delivery_entries(
                    date_from=datetime.now() - timedelta(days=days_back)
                )
            
            # 데이터 집계
            campaign_stats = self._calculate_campaign_stats(campaigns, campaign_influencers, delivery_entries)
            
            # 비즈니스 룰 위반 상황 체크
            rule_violations = self._check_business_rule_violations(campaigns, campaign_influencers, delivery_entries)
            
            # 온톨로지 기반 프롬프트 생성
            period_text = f"특정 월 ({specific_month})" if specific_month else f"최근 {days_back}일"
            
            prompt = f"""
            F&F 인플루언서 마케팅 캠페인 진행 현황을 온톨로지 기반으로 분석해주세요.
            
            ⚠️ 중요: 브랜드를 언급할 때는 반드시 실제 브랜드명(MLB, Discovery, Sergio Tacchini 등)을 사용하고, "브랜드 1", "브랜드 2" 같은 숫자는 절대 사용하지 마세요!
            
            ## 분석 데이터 개요
            - 분석 기간: {period_text}
            - 총 캠페인 수: {len(campaigns)}개
            - 총 인플루언서 참여: {len(campaign_influencers)}명
            - 총 배송 건수: {len(delivery_entries)}건
            
            ## 상세 성과 통계
            {json.dumps(campaign_stats, ensure_ascii=False, indent=2)}
            
            ## 비즈니스 룰 준수 현황
            {rule_violations}
            
            ## 온톨로지 기반 분석 요청사항
            1. **마케팅 도메인 성과**: 캠페인 성공률, 참여율, 목표 달성도 평가
            2. **상품-마케팅 연계**: 브랜드별/카테고리별 캠페인 효율성 분석 (반드시 MLB, Discovery, Sergio Tacchini 등 실제 브랜드명 사용, 브랜드 숫자 금지)
            3. **배송-마케팅 플로우**: 시딩 배송과 컨텐츠 업로드 간의 상관관계 분석
            4. **비즈니스 룰 위반**: 정의된 규칙 대비 실제 성과 갭 분석
            5. **도메인 간 개선 기회**: 마케팅↔상품↔배송 프로세스 최적화 방안
            6. **온톨로지 기반 권장사항**: 각 도메인 및 관계 개선을 위한 구체적 액션
            
            ## 작성 가이드라인
            - 온톨로지에 정의된 도메인과 관계를 기반으로 분석
            - 비즈니스 룰 위반 사항에 대한 구체적 대응 방안 제시
            - 각 도메인(마케팅/상품/배송) 연계성 고려
            - **중요**: 브랜드 언급 시 반드시 brand_breakdown_with_names의 실제 브랜드명(MLB, Discovery, Sergio Tacchini 등)을 사용하고, "브랜드 1", "브랜드 2" 같은 숫자 표기는 절대 사용하지 마세요
            - Markdown 형식, 구조화된 보고서
            - 데이터 기반의 정량적 인사이트
            - **개선 방안은 실무진이 바로 실행할 수 있는 구체적인 커뮤니케이션 전략 중심으로 제안**
            - 인센티브/보상보다는 효과적인 소통 방법, 업로드 독려 메시지, 팔로우업 전략에 집중
            - 예시: "배송 후 3일차 리마인드 메시지", "업로드 가이드 제공", "개별 맞춤 피드백", "단계별 소통 프로세스" 등
            - 실행 가능한 개선 방안 (우선순위 포함)
            """
            
            # Claude API 호출
            markdown_content = self._call_claude_api(prompt)
            
            # 보고서 생성
            report = AnalysisReport(
                title="인플루언서 마케팅 캠페인 성과 분석",
                analysis_type="campaign_performance",
                generated_at=datetime.now(),
                data_period=f"최근 {days_back}일",
                markdown_content=markdown_content,
                key_insights=self._extract_insights(markdown_content),
                recommendations=self._extract_recommendations(markdown_content)
            )
            
            # 파일 저장
            filename = f"campaign_performance_{datetime.now().strftime('%m%d%H%M')}"
            self._save_markdown_report(markdown_content, filename)
            
            return report
            
        except Exception as e:
            logger.error(f"캠페인 성과 분석 실패: {e}")
            raise
    
    def analyze_delivery_performance(self, days_back: int = 30) -> AnalysisReport:
        """배송 성과 분석"""
        logger.info(f"배송 성과 분석 시작 - 최근 {days_back}일")
        
        try:
            # 배송 데이터 조회
            delivery_entries = get_snowflake_service().get_delivery_entries(
                date_from=datetime.now() - timedelta(days=days_back)
            )
            
            # 배송 통계 계산
            delivery_stats = self._calculate_delivery_stats(delivery_entries)
            
            prompt = f"""
            F&F 인플루언서 마케팅 배송 성과를 분석해주세요.
            
            ## 분석 데이터
            - 분석 기간: 최근 {days_back}일
            - 총 배송 건수: {len(delivery_entries)}
            
            ## 배송 성과 통계
            {json.dumps(delivery_stats, ensure_ascii=False, indent=2)}
            
            ## 요청사항
            1. 전체 배송 성과 요약 (완료율, 평균 배송 시간, 지연율)
            2. 브랜드별 배송 성과 비교
            3. 배송 상태별 현황 분석
            4. 배송 지연 원인 및 패턴 분석
            5. 배송 개선을 위한 권장사항
            
            ## 작성 가이드라인
            - Markdown 형식으로 작성
            - 데이터 기반의 명확한 분석
            - 개선 가능한 구체적 방안 제시
            - 최대 40줄, 한 줄당 최대 100자
            """
            
            markdown_content = self._call_claude_api(prompt)
            
            report = AnalysisReport(
                title="인플루언서 마케팅 배송 성과 분석",
                analysis_type="delivery_analysis",
                generated_at=datetime.now(),
                data_period=f"최근 {days_back}일",
                markdown_content=markdown_content,
                key_insights=self._extract_insights(markdown_content),
                recommendations=self._extract_recommendations(markdown_content)
            )
            
            filename = f"delivery_analysis_{datetime.now().strftime('%m%d%H%M')}"
            self._save_markdown_report(markdown_content, filename)
            
            return report
            
        except Exception as e:
            logger.error(f"배송 성과 분석 실패: {e}")
            raise
    
    def analyze_business_rules_impact(self, days_back: int = 30) -> AnalysisReport:
        """비즈니스 룰 영향도 분석"""
        logger.info(f"비즈니스 룰 영향도 분석 시작 - 최근 {days_back}일")
        
        try:
            # 온톨로지에서 비즈니스 룰 조회
            business_rules = ontology_db.get_business_rules()
            
            # 실제 데이터로 룰 실행 (시뮬레이션)
            from .rule_engine import rule_engine
            rule_results = rule_engine.execute_rules_with_real_data(days_back=days_back)
            
            # 룰 영향도 통계
            rule_impact_stats = self._calculate_rule_impact_stats(business_rules, rule_results)
            
            prompt = f"""
            F&F 인플루언서 마케팅 비즈니스 룰의 영향도를 분석해주세요.
            
            ## 분석 데이터
            - 분석 기간: 최근 {days_back}일
            - 총 비즈니스 룰 수: {len(business_rules)}
            - 룰 실행 결과: {len(rule_results)}건
            
            ## 비즈니스 룰 정의
            {json.dumps([{"id": r.id, "name": r.name, "priority": r.priority, "description": r.description} for r in business_rules], ensure_ascii=False, indent=2)}
            
            ## 룰 영향도 통계
            {json.dumps(rule_impact_stats, ensure_ascii=False, indent=2)}
            
            ## 요청사항
            1. 각 비즈니스 룰의 트리거 빈도 및 영향도 분석
            2. 우선순위별 룰 효과성 평가
            3. 가장 중요한 룰과 개선이 필요한 룰 식별
            4. 룰 최적화를 위한 권장사항
            5. 신규 룰 제안 (필요한 경우)
            
            ## 작성 가이드라인
            - Markdown 형식으로 작성
            - 각 룰별 구체적인 분석 제공
            - 데이터 기반 개선 방안 제시
            - 최대 50줄, 한 줄당 최대 100자
            """
            
            markdown_content = self._call_claude_api(prompt)
            
            report = AnalysisReport(
                title="비즈니스 룰 영향도 분석",
                analysis_type="business_rules_impact",
                generated_at=datetime.now(),
                data_period=f"최근 {days_back}일",
                markdown_content=markdown_content,
                key_insights=self._extract_insights(markdown_content),
                recommendations=self._extract_recommendations(markdown_content)
            )
            
            filename = f"business_rules_impact_{datetime.now().strftime('%m%d%H%M')}"
            self._save_markdown_report(markdown_content, filename)
            
            return report
            
        except Exception as e:
            logger.error(f"비즈니스 룰 영향도 분석 실패: {e}")
            raise
    
    def _get_brand_mapping(self) -> Dict[str, str]:
        """브랜드 ID와 브랜드명 매핑 조회"""
        try:
            # brand 테이블에서 브랜드 정보 조회
            brands = get_snowflake_service().get_brands()
            brand_mapping = {}
            
            for brand in brands:
                brand_id = str(brand.get('id', ''))  # campaign 테이블의 brand_id(문자열)와 매칭
                brand_name = brand.get('brand_nm', '')
                if brand_id and brand_name:
                    brand_mapping[brand_id] = brand_name
            
            return brand_mapping
            
        except Exception as e:
            logger.error(f"브랜드 매핑 조회 실패: {e}")
            return {}
    
    def _calculate_campaign_stats(self, campaigns: List[Dict], campaign_influencers: List[Dict], deliveries: List[Dict]) -> Dict:
        """캠페인 통계 계산"""
        try:
            # 브랜드 매핑 정보 조회
            brand_mapping = self._get_brand_mapping()
            
            stats = {
                "total_campaigns": len(campaigns),
                "active_campaigns": len([c for c in campaigns if c.get('status') != 'COMPLETE']),
                "total_influencers": len(campaign_influencers),
                "content_upload_rate": 0,
                "delivery_completion_rate": 0,
                "brand_breakdown_with_names": {},
                "status_breakdown": {}
            }
            
            # 컨텐츠 업로드율 계산
            uploaded_count = len([ci for ci in campaign_influencers if ci.get('contents_post_dt')])
            if campaign_influencers:
                stats["content_upload_rate"] = round(uploaded_count / len(campaign_influencers) * 100, 2)
            
            # 배송 완료율 계산
            completed_deliveries = len([d for d in deliveries if d.get('status') == 'COMPLETE'])
            if deliveries:
                stats["delivery_completion_rate"] = round(completed_deliveries / len(deliveries) * 100, 2)
            
            # 브랜드별 분류
            for campaign in campaigns:
                brand_id = campaign.get('brand_id', 'Unknown')
                brand_name = brand_mapping.get(brand_id, f"브랜드 {brand_id}")  # 매핑이 없으면 "브랜드 ID" 형태로 표시
                
                # 브랜드명 기반 분류만 사용
                if brand_name not in stats["brand_breakdown_with_names"]:
                    stats["brand_breakdown_with_names"][brand_name] = 0
                stats["brand_breakdown_with_names"][brand_name] += 1
            
            # 상태별 분류
            for campaign in campaigns:
                status = campaign.get('status', 'Unknown')
                if status not in stats["status_breakdown"]:
                    stats["status_breakdown"][status] = 0
                stats["status_breakdown"][status] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"캠페인 통계 계산 실패: {e}")
            return {}
    
    def _calculate_delivery_stats(self, deliveries: List[Dict]) -> Dict:
        """배송 통계 계산"""
        try:
            stats = {
                "total_deliveries": len(deliveries),
                "status_breakdown": {},
                "brand_breakdown": {},
                "completion_rate": 0,
                "average_delivery_days": 0
            }
            
            # 상태별 분류
            for delivery in deliveries:
                status = delivery.get('status', 'Unknown')
                if status not in stats["status_breakdown"]:
                    stats["status_breakdown"][status] = 0
                stats["status_breakdown"][status] += 1
            
            # 브랜드별 분류
            for delivery in deliveries:
                brand = delivery.get('brand_id', 'Unknown')
                if brand not in stats["brand_breakdown"]:
                    stats["brand_breakdown"][brand] = 0
                stats["brand_breakdown"][brand] += 1
            
            # 완료율 계산
            completed = stats["status_breakdown"].get('COMPLETE', 0)
            if deliveries:
                stats["completion_rate"] = round(completed / len(deliveries) * 100, 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"배송 통계 계산 실패: {e}")
            return {}
    
    def _calculate_rule_impact_stats(self, rules: List, rule_results: List) -> Dict:
        """룰 영향도 통계 계산"""
        try:
            stats = {
                "total_rules": len(rules),
                "triggered_rules": len([r for r in rule_results if r.triggered]),
                "trigger_rate": 0,
                "priority_breakdown": {},
                "rule_effectiveness": {}
            }
            
            # 트리거율 계산
            if rule_results:
                stats["trigger_rate"] = round(stats["triggered_rules"] / len(rule_results) * 100, 2)
            
            # 우선순위별 분류
            for rule in rules:
                priority = rule.priority
                if priority not in stats["priority_breakdown"]:
                    stats["priority_breakdown"][priority] = {"total": 0, "triggered": 0}
                stats["priority_breakdown"][priority]["total"] += 1
            
            # 룰별 효과성
            for result in rule_results:
                if result.triggered:
                    rule_id = result.rule_id
                    if rule_id not in stats["rule_effectiveness"]:
                        stats["rule_effectiveness"][rule_id] = 0
                    stats["rule_effectiveness"][rule_id] += len(result.matched_records)
            
            return stats
            
        except Exception as e:
            logger.error(f"룰 영향도 통계 계산 실패: {e}")
            return {}
    
    def _extract_insights(self, markdown_content: str) -> List[str]:
        """마크다운에서 핵심 인사이트 추출"""
        # 간단한 추출 로직 (실제로는 더 정교한 파싱 필요)
        insights = []
        lines = markdown_content.split('\n')
        
        for line in lines:
            if '인사이트' in line or '핵심' in line or '중요' in line:
                insights.append(line.strip('- ').strip('#').strip())
        
        return insights[:5]  # 최대 5개
    
    def _extract_recommendations(self, markdown_content: str) -> List[str]:
        """마크다운에서 권장사항 추출"""
        recommendations = []
        lines = markdown_content.split('\n')
        
        for line in lines:
            if '권장' in line or '추천' in line or '제안' in line:
                recommendations.append(line.strip('- ').strip('#').strip())
        
        return recommendations[:5]  # 최대 5개


# 전역 AI 분석 서비스 인스턴스 (lazy loading)
ai_analysis_service = None

def get_ai_analysis_service():
    """AI 분석 서비스 인스턴스를 lazy loading으로 반환"""
    global ai_analysis_service
    if ai_analysis_service is None:
        ai_analysis_service = AIAnalysisService()
    return ai_analysis_service
