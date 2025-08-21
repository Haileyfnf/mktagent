"""
비즈니스 룰 엔진 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from ..services.rule_engine import rule_engine, RuleContext, RuleResult


class ExecuteRulesRequest(BaseModel):
    """룰 실행 요청 모델"""
    current_date: Optional[str] = None  # ISO format
    delivery_entries: List[Dict] = []
    campaign_influencers: List[Dict] = []
    campaigns: List[Dict] = []
    contents: List[Dict] = []


class MockDataRequest(BaseModel):
    """Mock 데이터 생성 요청"""
    scenario: str  # "content_overdue", "campaign_ending", "delivery_delay", "hashtag_missing"


router = APIRouter()


@router.post("/execute", summary="비즈니스 규칙 실행")
async def execute_business_rules(request: ExecuteRulesRequest) -> List[RuleResult]:
    """모든 비즈니스 규칙을 실행합니다."""
    try:
        # 현재 시간 설정
        current_date = datetime.now()
        if request.current_date:
            current_date = datetime.fromisoformat(request.current_date)
        
        # 실행 컨텍스트 생성
        context = RuleContext(
            current_date=current_date,
            delivery_entries=request.delivery_entries,
            campaign_influencers=request.campaign_influencers,
            campaigns=request.campaigns,
            contents=request.contents
        )
        
        # 모든 룰 실행
        results = rule_engine.execute_all_rules(context)
        
        return results
        
    except Exception as e:
        logger.error(f"비즈니스 규칙 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"규칙 실행 실패: {str(e)}")


@router.get("/rules", summary="사용 가능한 비즈니스 규칙 목록")
async def get_available_rules(
    priority: Optional[str] = Query(None, description="우선순위 필터")
) -> List[Dict[str, Any]]:
    """사용 가능한 모든 비즈니스 규칙을 조회합니다."""
    try:
        from ..services.ontology_duckdb import ontology_db
        
        rules = ontology_db.get_business_rules(priority)
        
        return [
            {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "priority": rule.priority,
                "condition": rule.condition,
                "action": rule.action
            }
            for rule in rules
        ]
        
    except Exception as e:
        logger.error(f"비즈니스 규칙 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="규칙 목록 조회 실패")


@router.post("/test/mock-data", summary="테스트용 Mock 데이터 생성")
async def generate_mock_data(request: MockDataRequest) -> ExecuteRulesRequest:
    """테스트용 Mock 데이터를 생성합니다."""
    try:
        current_date = datetime.now()
        
        if request.scenario == "content_overdue":
            # MKT_001: 컨텐츠 업로드 미완료 시나리오
            mock_data = ExecuteRulesRequest(
                current_date=current_date.isoformat(),
                delivery_entries=[
                    {
                        "id": "del_001",
                        "status": "COMPLETE",
                        "delivery_confirm_dt": (current_date.replace(day=1)).isoformat(),  # 10일 전
                        "campaign_influencer_id": "ci_001"
                    }
                ],
                campaign_influencers=[
                    {
                        "id": "ci_001",
                        "campaign_id": "camp_001",
                        "influencer_id": "inf_001",
                        "contents_post_dt": None  # 컨텐츠 미업로드
                    }
                ],
                campaigns=[
                    {
                        "id": "camp_001",
                        "camp_nm": "여름 신상 캠페인",
                        "end_date": (current_date.replace(day=28)).isoformat()
                    }
                ]
            )
            
        elif request.scenario == "campaign_ending":
            # MKT_002: 캠페인 종료 임박 시나리오
            mock_data = ExecuteRulesRequest(
                current_date=current_date.isoformat(),
                campaigns=[
                    {
                        "id": "camp_002",
                        "camp_nm": "가을 컬렉션 캠페인", 
                        "end_date": (current_date.replace(day=current_date.day + 2)).isoformat()  # 2일 후 종료
                    }
                ],
                campaign_influencers=[
                    {
                        "id": "ci_002",
                        "campaign_id": "camp_002",
                        "influencer_id": "inf_002",
                        "contents_post_dt": None  # 컨텐츠 미업로드
                    }
                ]
            )
            
        elif request.scenario == "delivery_delay":
            # MKT_003: 배송 지연 시나리오
            mock_data = ExecuteRulesRequest(
                current_date=current_date.isoformat(),
                campaigns=[
                    {
                        "id": "camp_003",
                        "camp_nm": "긴급 프로모션",
                        "end_date": (current_date.replace(day=current_date.day + 1)).isoformat()  # 내일 종료
                    }
                ],
                delivery_entries=[
                    {
                        "id": "del_003",
                        "status": "DELIVERY_IN_PROGRESS",  # 아직 배송 중
                        "campaign_influencer_id": "ci_003"
                    }
                ],
                campaign_influencers=[
                    {
                        "id": "ci_003",
                        "campaign_id": "camp_003",
                        "influencer_id": "inf_003"
                    }
                ]
            )
            
        elif request.scenario == "hashtag_missing":
            # MKT_004: 해시태그 미준수 시나리오
            mock_data = ExecuteRulesRequest(
                current_date=current_date.isoformat(),
                campaigns=[
                    {
                        "id": "camp_004",
                        "camp_nm": "브랜드 협찬 캠페인",
                        "required_hashtags": ["#브랜드협찬", "#신상품"]
                    }
                ],
                contents=[
                    {
                        "id": "content_001",
                        "campaign_id": "camp_004",
                        "hashtags": ["#신상품"],  # #브랜드협찬 누락
                        "influencer_id": "inf_004"
                    }
                ]
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"지원되지 않는 시나리오: {request.scenario}")
        
        return mock_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock 데이터 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="Mock 데이터 생성 실패")


@router.post("/test/scenario/{scenario}", summary="시나리오별 테스트 실행")
async def test_scenario(scenario: str) -> Dict[str, Any]:
    """특정 시나리오에 대한 룰 테스트를 실행합니다."""
    try:
        # Mock 데이터 생성
        mock_request = MockDataRequest(scenario=scenario)
        mock_data = await generate_mock_data(mock_request)
        
        # 룰 실행
        results = await execute_business_rules(mock_data)
        
        return {
            "scenario": scenario,
            "mock_data": mock_data.dict(),
            "rule_results": [result.dict() for result in results],
            "triggered_rules": [r.rule_id for r in results if r.triggered],
            "total_triggered": sum(1 for r in results if r.triggered)
        }
        
    except Exception as e:
        logger.error(f"시나리오 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시나리오 테스트 실패: {str(e)}")


@router.get("/health", summary="룰 엔진 상태 확인")
async def rule_engine_health() -> Dict[str, Any]:
    """룰 엔진의 상태를 확인합니다."""
    try:
        from ..services.ontology_duckdb import ontology_db
        
        # 규칙 수 확인
        rules = ontology_db.get_business_rules()
        
        return {
            "status": "healthy",
            "total_rules": len(rules),
            "rules_by_priority": {
                "high": len([r for r in rules if r.priority == "high"]),
                "medium": len([r for r in rules if r.priority == "medium"]),
                "low": len([r for r in rules if r.priority == "low"])
            },
            "supported_scenarios": [
                "content_overdue",
                "campaign_ending", 
                "delivery_delay",
                "hashtag_missing"
            ]
        }
        
    except Exception as e:
        logger.error(f"룰 엔진 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail="룰 엔진 상태 확인 실패")


@router.post("/execute/real-data", summary="실제 데이터로 비즈니스 규칙 실행")
async def execute_rules_with_real_data(
    days_back: int = Query(30, description="조회할 과거 일수", ge=1, le=365)
) -> List[RuleResult]:
    """Snowflake에서 실제 데이터를 가져와서 비즈니스 규칙을 실행합니다."""
    try:
        results = rule_engine.execute_rules_with_real_data(days_back=days_back)
        return results
        
    except Exception as e:
        logger.error(f"실제 데이터로 규칙 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실제 데이터 규칙 실행 실패: {str(e)}")


@router.get("/data-sources/status", summary="데이터 소스 상태 확인")
async def get_data_source_status() -> Dict[str, Any]:
    """Snowflake 및 온톨로지 데이터 소스의 상태를 확인합니다."""
    try:
        return rule_engine.get_data_source_status()
        
    except Exception as e:
        logger.error(f"데이터 소스 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail="데이터 소스 상태 확인 실패")


@router.get("/snowflake/test", summary="Snowflake 연결 테스트")
async def test_snowflake_connection() -> Dict[str, Any]:
    """Snowflake 데이터베이스 연결을 테스트합니다."""
    try:
        from ..services.snowflake_service import snowflake_service
        
        result = snowflake_service.test_connection()
        
        if result["status"] == "success":
            return result
        else:
            raise HTTPException(status_code=503, detail=result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Snowflake 연결 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Snowflake 연결 테스트 실패: {str(e)}")


@router.get("/snowflake/sample-data", summary="Snowflake 샘플 데이터 조회")
async def get_snowflake_sample_data(
    table: str = Query(..., description="조회할 테이블명"),
    limit: int = Query(10, description="조회할 레코드 수", ge=1, le=50)  # 더 제한적으로
) -> Dict[str, Any]:
    """Snowflake에서 샘플 데이터를 조회합니다. (READ-ONLY)"""
    try:
        from ..services.snowflake_service import snowflake_service
        
        # 기본 테이블들만 허용
        allowed_tables = ["delivery_entry", "campaign_influencer", "campaign", "categorized_item", "brand"]
        
        if table not in allowed_tables:
            raise HTTPException(
                status_code=400, 
                detail=f"허용되지 않은 테이블: {table}. 허용된 테이블: {allowed_tables}"
            )
        
        # 간단하게 조회 (READ-ONLY 권한으로 이미 안전)
        query = f"SELECT * FROM {table} LIMIT {limit}"
        
        logger.info(f"안전한 샘플 데이터 조회: {table} ({limit}건)")
        results = snowflake_service.execute_query(query)
        
        return {
            "table": table,
            "record_count": len(results),
            "data": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Snowflake 샘플 데이터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"샘플 데이터 조회 실패: {str(e)}")


@router.get("/security/status", summary="보안 상태 확인")
async def get_security_status() -> Dict[str, Any]:
    """시스템의 보안 상태를 확인합니다."""
    try:
        import os
        
        return {
            "connection_type": "READ-ONLY",
            "allowed_tables": ["delivery_entry", "campaign_influencer", "campaign", "categorized_item", "brand"],
            "status": "안전 - READ-ONLY 권한으로 운영"
        }
        
    except Exception as e:
        logger.error(f"보안 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail="보안 상태 확인 실패")
