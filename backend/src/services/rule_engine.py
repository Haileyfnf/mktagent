"""
비즈니스 룰 엔진
온톨로지에 정의된 비즈니스 규칙을 실제로 실행하는 엔진
"""
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from pydantic import BaseModel

from .ontology_duckdb import ontology_db, BusinessRule
from .snowflake_service import snowflake_service


class RuleContext(BaseModel):
    """규칙 실행 컨텍스트"""
    current_date: datetime
    delivery_entries: List[Dict] = []
    campaign_influencers: List[Dict] = []
    campaigns: List[Dict] = []
    contents: List[Dict] = []


class RuleResult(BaseModel):
    """규칙 실행 결과"""
    rule_id: str
    rule_name: str
    triggered: bool
    matched_records: List[Dict] = []
    actions_executed: List[str] = []
    error_message: Optional[str] = None


class NotificationService:
    """알림 서비스 (Mock 구현)"""
    
    @staticmethod
    def send_staff_alert(message: str, rule_id: str) -> bool:
        """실무자 알림 발송"""
        logger.info(f"[스태프 알림] {rule_id}: {message}")
        # 실제로는 이메일, 슬랙, SMS 등으로 발송
        return True
    
    @staticmethod
    def send_influencer_dm(influencer_id: str, message: str, rule_id: str) -> bool:
        """인플루언서 DM 발송"""
        logger.info(f"[인플루언서 DM] {rule_id} → {influencer_id}: {message}")
        # 실제로는 인스타그램 DM, 카카오톡 등으로 발송
        return True


class RuleEngine:
    """비즈니스 룰 엔진"""
    
    def __init__(self):
        """룰 엔진 초기화"""
        self.notification_service = NotificationService()
        self.supported_operators = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            'IN': lambda a, b: a in b,
            'NOT IN': lambda a, b: a not in b,
            'IS NULL': lambda a, b: a is None,
            'IS NOT NULL': lambda a, b: a is not None,
            'LIKE': lambda a, b: str(b) in str(a)
        }
        logger.info("비즈니스 룰 엔진 초기화 완료")
    
    def execute_all_rules(self, context: RuleContext) -> List[RuleResult]:
        """모든 비즈니스 규칙을 실행"""
        logger.info(f"비즈니스 규칙 실행 시작 - 컨텍스트: {context.current_date}")
        
        rules = ontology_db.get_business_rules()
        results = []
        
        for rule in rules:
            try:
                result = self.execute_rule(rule, context)
                results.append(result)
                
                if result.triggered:
                    logger.info(f"규칙 '{rule.id}' 트리거됨 - {len(result.matched_records)}건 매칭")
                
            except Exception as e:
                logger.error(f"규칙 '{rule.id}' 실행 실패: {e}")
                results.append(RuleResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    triggered=False,
                    error_message=str(e)
                ))
        
        triggered_count = sum(1 for r in results if r.triggered)
        logger.info(f"비즈니스 규칙 실행 완료 - 총 {len(results)}개 중 {triggered_count}개 트리거됨")
        
        return results
    
    def execute_rule(self, rule: BusinessRule, context: RuleContext) -> RuleResult:
        """개별 규칙 실행"""
        logger.debug(f"규칙 '{rule.id}' 실행 시작")
        
        result = RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            triggered=False
        )
        
        try:
            # 조건 평가
            matched_records = self._evaluate_condition(rule.condition, context)
            
            if matched_records:
                result.triggered = True
                result.matched_records = matched_records
                
                # 액션 실행
                actions_executed = self._execute_actions(rule, matched_records, context)
                result.actions_executed = actions_executed
                
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"규칙 '{rule.id}' 실행 중 오류: {e}")
        
        return result
    
    def _evaluate_condition(self, condition: str, context: RuleContext) -> List[Dict]:
        """조건문 평가"""
        logger.debug(f"조건 평가: {condition}")
        
        # 조건문을 파싱하여 실제 데이터와 비교
        # 예: "delivery_entry.status == 'COMPLETE' AND delivery_entry.delivery_confirm_dt < current_date - 7_days"
        
        matched_records = []
        
        # MKT_001: 컨텐츠 업로드 미완료 알림
        if "delivery_entry.status == 'COMPLETE'" in condition and "contents_post_dt IS NULL" in condition:
            matched_records = self._check_content_upload_overdue(context)
        
        # MKT_002: 캠페인 종료 임박 알림
        elif "campaign.end_date - current_date <= 3_days" in condition:
            matched_records = self._check_campaign_ending_soon(context)
        
        # MKT_003: 배송 지연으로 인한 캠페인 연장 검토
        elif "campaign.end_date - current_date <= 1_day" in condition and "DELIVERY_IN_PROGRESS" in condition:
            matched_records = self._check_delivery_delay(context)
        
        # MKT_004: 해시태그 가이드라인 미준수
        elif "required_hashtags NOT IN content.hashtags" in condition:
            matched_records = self._check_hashtag_compliance(context)
        
        else:
            # 일반적인 조건 파싱 (향후 확장)
            logger.warning(f"지원되지 않는 조건문: {condition}")
        
        return matched_records
    
    def _check_content_upload_overdue(self, context: RuleContext) -> List[Dict]:
        """컨텐츠 업로드 미완료 체크"""
        matched = []
        seven_days_ago = context.current_date - timedelta(days=7)
        
        for delivery in context.delivery_entries:
            if (delivery.get('status') == 'COMPLETE' and 
                delivery.get('delivery_confirm_dt') and
                datetime.fromisoformat(delivery['delivery_confirm_dt']) < seven_days_ago):
                
                # 해당 캠페인 인플루언서의 컨텐츠 업로드 여부 확인
                for ci in context.campaign_influencers:
                    if (ci.get('id') == delivery.get('campaign_influencer_id') and
                        not ci.get('contents_post_dt')):
                        matched.append({
                            'delivery_entry': delivery,
                            'campaign_influencer': ci,
                            'days_overdue': (context.current_date - datetime.fromisoformat(delivery['delivery_confirm_dt'])).days
                        })
        
        return matched
    
    def _check_campaign_ending_soon(self, context: RuleContext) -> List[Dict]:
        """캠페인 종료 임박 체크"""
        matched = []
        three_days_later = context.current_date + timedelta(days=3)
        
        for campaign in context.campaigns:
            if (campaign.get('end_date') and
                datetime.fromisoformat(campaign['end_date']) <= three_days_later):
                
                # 해당 캠페인의 미업로드 인플루언서 찾기
                for ci in context.campaign_influencers:
                    if (ci.get('campaign_id') == campaign.get('id') and
                        not ci.get('contents_post_dt')):
                        matched.append({
                            'campaign': campaign,
                            'campaign_influencer': ci,
                            'days_remaining': (datetime.fromisoformat(campaign['end_date']) - context.current_date).days
                        })
        
        return matched
    
    def _check_delivery_delay(self, context: RuleContext) -> List[Dict]:
        """배송 지연 체크"""
        matched = []
        tomorrow = context.current_date + timedelta(days=1)
        
        for campaign in context.campaigns:
            if (campaign.get('end_date') and
                datetime.fromisoformat(campaign['end_date']) <= tomorrow):
                
                # 해당 캠페인의 배송 진행 중인 항목들 찾기
                for delivery in context.delivery_entries:
                    if (delivery.get('status') in ['AWAITING_DELIVERY_START', 'DELIVERY_IN_PROGRESS']):
                        for ci in context.campaign_influencers:
                            if (ci.get('campaign_id') == campaign.get('id') and
                                ci.get('id') == delivery.get('campaign_influencer_id')):
                                matched.append({
                                    'campaign': campaign,
                                    'delivery_entry': delivery,
                                    'campaign_influencer': ci
                                })
        
        return matched
    
    def _check_hashtag_compliance(self, context: RuleContext) -> List[Dict]:
        """해시태그 준수 체크"""
        matched = []
        
        for content in context.contents:
            # 캠페인의 필수 해시태그 확인
            for campaign in context.campaigns:
                required_hashtags = campaign.get('required_hashtags', [])
                content_hashtags = content.get('hashtags', [])
                
                for required_tag in required_hashtags:
                    if required_tag not in content_hashtags:
                        matched.append({
                            'content': content,
                            'campaign': campaign,
                            'missing_hashtag': required_tag
                        })
        
        return matched
    
    def _execute_actions(self, rule: BusinessRule, matched_records: List[Dict], context: RuleContext) -> List[str]:
        """액션 실행"""
        actions_executed = []
        
        try:
            # MKT_001: 마케팅 담당자 알림
            if rule.id == "MKT_001":
                for record in matched_records:
                    message = f"배송 완료 후 {record['days_overdue']}일이 지났으나 컨텐츠 업로드가 되지 않았습니다."
                    if self.notification_service.send_staff_alert(message, rule.id):
                        actions_executed.append(f"스태프 알림 발송: {message}")
            
            # MKT_002: 인플루언서 리마인드
            elif rule.id == "MKT_002":
                for record in matched_records:
                    influencer_id = record['campaign_influencer'].get('influencer_id')
                    message = f"캠페인 종료까지 {record['days_remaining']}일 남았습니다. 컨텐츠 업로드를 부탁드립니다."
                    if self.notification_service.send_influencer_dm(influencer_id, message, rule.id):
                        actions_executed.append(f"인플루언서 DM 발송: {influencer_id}")
            
            # MKT_003: 캠페인 연장 검토 요청
            elif rule.id == "MKT_003":
                for record in matched_records:
                    campaign_name = record['campaign'].get('camp_nm')
                    message = f"'{campaign_name}' 캠페인의 배송 지연으로 인한 기간 연장을 검토해주세요."
                    if self.notification_service.send_staff_alert(message, rule.id):
                        actions_executed.append(f"캠페인 연장 검토 요청: {campaign_name}")
            
            # MKT_004: 해시태그 미준수 알림
            elif rule.id == "MKT_004":
                for record in matched_records:
                    # 스태프 알림
                    if rule.staff_alert_template:
                        staff_message = rule.staff_alert_template.format(
                            campaign_name=record['campaign'].get('camp_nm'),
                            influencer_name=record.get('influencer_name', 'Unknown'),
                            required_hashtag=record['missing_hashtag']
                        )
                        if self.notification_service.send_staff_alert(staff_message, rule.id):
                            actions_executed.append(f"스태프 알림 발송")
                    
                    # 인플루언서 DM
                    if rule.influencer_message_template:
                        influencer_message = rule.influencer_message_template.format(
                            influencer_name=record.get('influencer_name', '인플루언서'),
                            required_hashtag=record['missing_hashtag']
                        )
                        influencer_id = record.get('influencer_id', 'unknown')
                        if self.notification_service.send_influencer_dm(influencer_id, influencer_message, rule.id):
                            actions_executed.append(f"인플루언서 DM 발송: {influencer_id}")
            
        except Exception as e:
            logger.error(f"액션 실행 실패 (규칙: {rule.id}): {e}")
            actions_executed.append(f"액션 실행 실패: {str(e)}")
        
        return actions_executed
    
    def get_rule_execution_history(self, limit: int = 100) -> List[Dict]:
        """규칙 실행 이력 조회 (향후 구현용)"""
        # 실제로는 DB에 실행 이력을 저장하고 조회
        return []
    
    def execute_rules_with_real_data(self, days_back: int = 30) -> List[RuleResult]:
        """Snowflake에서 실제 데이터를 가져와서 규칙 실행"""
        logger.info(f"Snowflake 실제 데이터로 규칙 실행 시작 (최근 {days_back}일)")
        
        try:
            # Snowflake에서 실제 데이터 조회
            data = snowflake_service.get_rule_context_data(days_back=days_back)
            
            # RuleContext 생성
            context = RuleContext(
                current_date=datetime.now(),
                delivery_entries=data["delivery_entries"],
                campaign_influencers=data["campaign_influencers"],
                campaigns=data["campaigns"],
                contents=data["contents"]
            )
            
            logger.info(f"실제 데이터 로드 완료 - "
                       f"배송: {len(context.delivery_entries)}, "
                       f"캠페인 인플루언서: {len(context.campaign_influencers)}, "
                       f"캠페인: {len(context.campaigns)}, "
                       f"컨텐츠: {len(context.contents)}")
            
            # 모든 룰 실행
            results = self.execute_all_rules(context)
            
            return results
            
        except Exception as e:
            logger.error(f"실제 데이터로 규칙 실행 실패: {e}")
            raise
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """데이터 소스 상태 확인"""
        try:
            # Snowflake 연결 테스트
            snowflake_status = snowflake_service.test_connection()
            
            # DuckDB 온톨로지 상태
            ontology_rules = ontology_db.get_business_rules()
            
            return {
                "snowflake": snowflake_status,
                "ontology": {
                    "status": "connected",
                    "total_rules": len(ontology_rules),
                    "rules": [{"id": r.id, "name": r.name, "priority": r.priority} for r in ontology_rules]
                },
                "integration_status": "ready" if snowflake_status["status"] == "success" else "snowflake_error"
            }
            
        except Exception as e:
            logger.error(f"데이터 소스 상태 확인 실패: {e}")
            return {
                "snowflake": {"status": "error", "error": str(e)},
                "ontology": {"status": "error", "error": str(e)},
                "integration_status": "error"
            }


# 전역 룰 엔진 인스턴스
rule_engine = RuleEngine()
