"""
인플루언서 모니터링 대시보드 API
- 캠페인 업데이트 및 실시간 모니터링
- 온톨로지 기반 비즈니스 룰 적용
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel

from ..services.snowflake_service import get_snowflake_service
from ..services.ontology_duckdb import ontology_db
from ..services.rule_engine import rule_engine
from ..services.content_preview_service import content_preview_service

router = APIRouter()


# === REQUEST/RESPONSE 모델 ===

class CampaignUpdateRequest(BaseModel):
    """캠페인 상태 업데이트 요청"""
    campaign_id: str
    status: Optional[str] = None
    end_date: Optional[str] = None  # ISO format
    target_cnt: Optional[int] = None
    notes: Optional[str] = None


class InfluencerProgressUpdate(BaseModel):
    """인플루언서 진행 상태 업데이트"""
    campaign_influencer_id: str
    progress: Literal[
        "AWAITING_INVITATION", "AWAITING_RESPONSE", "AWAITING_BENEFIT",
        "AWAITING_SHIPPING", "AWAITING_CONTENTS_UPLOAD", 
        "AWAITING_EVALUATION", "COMPLETE", "CANCELLED"
    ]
    cast_status: Optional[Literal["NOT_STARTED", "AWAITING_RESPONSE", "ACCEPTED", "DECLINED"]] = None
    contents_post_dt: Optional[str] = None  # ISO format
    notes: Optional[str] = None


class CampaignDashboardResponse(BaseModel):
    """캠페인 대시보드 응답"""
    campaign_id: str
    camp_nm: str
    status: str
    progress_summary: Dict[str, int]  # {"COMPLETE": 5, "AWAITING_CONTENTS_UPLOAD": 3, ...}
    total_influencers: int
    completion_rate: float
    content_upload_rate: float
    delivery_completion_rate: float
    upcoming_deadlines: List[Dict[str, Any]]
    business_rule_alerts: List[Dict[str, Any]]


# === 필터 옵션 API ===

@router.get("/filter-options/brands", summary="브랜드 목록 조회")
async def get_brands() -> Dict[str, Any]:
    """인플루언서 모니터링용 브랜드 목록 조회"""
    try:
        brands = get_snowflake_service().get_brands()
        
        # 브랜드별 캠페인 수 포함
        brand_options = []
        for brand in brands:
            brand_id = str(brand.get('id', ''))
            brand_name = brand.get('brand_nm', '')
            
            # 해당 브랜드의 캠페인 수 조회
            campaign_count_query = """
            SELECT COUNT(*) as count FROM campaign WHERE brand_id = :brand_id
            """
            count_result = get_snowflake_service().execute_query(
                campaign_count_query, {"brand_id": brand_id}
            )
            campaign_count = count_result[0]['count'] if count_result else 0
            
            brand_options.append({
                "brand_id": brand_id,
                "brand_name": brand_name,
                "campaign_count": campaign_count
            })
        
        return {
            "brands": brand_options,
            "total": len(brand_options)
        }
        
    except Exception as e:
        logger.error(f"브랜드 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/filter-options/brands/{brand_id}/months", summary="브랜드별 월 목록 조회")
async def get_brand_months(brand_id: str) -> Dict[str, Any]:
    """특정 브랜드의 캠페인이 있는 월 목록 조회"""
    try:
        # 해당 브랜드의 캠페인 기간 조회
        months_query = """
        SELECT DISTINCT 
            DATE_TRUNC('month', start_date) as campaign_month,
            COUNT(*) as campaign_count
        FROM campaign 
        WHERE brand_id = :brand_id
        GROUP BY DATE_TRUNC('month', start_date)
        ORDER BY campaign_month DESC
        """
        
        months_result = get_snowflake_service().execute_query(
            months_query, {"brand_id": brand_id}
        )
        
        month_options = []
        for row in months_result:
            campaign_month = row.get('campaign_month')
            if campaign_month:
                # YYYY-MM 형태로 변환
                month_str = campaign_month.strftime('%Y-%m')
                month_display = campaign_month.strftime('%Y년 %m월')
                
                month_options.append({
                    "month_key": month_str,
                    "month_display": month_display,
                    "campaign_count": row.get('campaign_count', 0)
                })
        
        return {
            "brand_id": brand_id,
            "months": month_options,
            "total": len(month_options)
        }
        
    except Exception as e:
        logger.error(f"브랜드별 월 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/filter-options/brands/{brand_id}/months/{month}/campaigns", summary="브랜드+월별 캠페인 목록")
async def get_brand_month_campaigns(brand_id: str, month: str) -> Dict[str, Any]:
    """특정 브랜드의 특정 월 캠페인 목록 조회"""
    try:
        # month 형태: "2025-07"
        month_start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
        if month_start.month == 12:
            month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
        
        campaigns_query = """
        SELECT 
            id, camp_code, camp_nm, start_date, end_date, status, 
            target_cnt, engmt_avg, engmt_cnt
        FROM campaign 
        WHERE brand_id = :brand_id
        AND (
            start_date BETWEEN :month_start AND :month_end
            OR end_date BETWEEN :month_start AND :month_end
            OR (start_date <= :month_start AND end_date >= :month_end)
        )
        ORDER BY start_date DESC
        """
        
        campaigns = get_snowflake_service().execute_query(campaigns_query, {
            "brand_id": brand_id,
            "month_start": month_start.strftime('%Y-%m-%d'),
            "month_end": month_end.strftime('%Y-%m-%d')
        })
        
        # 각 캠페인별 기본 통계 추가
        campaign_options = []
        for campaign in campaigns:
            campaign_id = str(campaign['id'])
            
            # 인플루언서 참여 수 조회
            influencer_count_query = """
            SELECT COUNT(*) as count FROM campaign_influencer 
            WHERE campaign_id = :campaign_id
            """
            influencer_count = get_snowflake_service().execute_query(
                influencer_count_query, {"campaign_id": campaign_id}
            )[0]['count']
            
            campaign_options.append({
                "campaign_id": campaign_id,
                "camp_code": campaign.get('camp_code', ''),
                "camp_nm": campaign.get('camp_nm', ''),
                "status": campaign.get('status', ''),
                "start_date": campaign.get('start_date'),
                "end_date": campaign.get('end_date'),
                "target_cnt": campaign.get('target_cnt', 0),
                "actual_influencer_count": influencer_count
            })
        
        return {
            "brand_id": brand_id,
            "month": month,
            "campaigns": campaign_options,
            "total": len(campaign_options)
        }
        
    except Exception as e:
        logger.error(f"브랜드+월별 캠페인 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


# === 캠페인 모니터링 API ===

@router.get("/latest-contents", summary="최신 컨텐츠 프리뷰")
async def get_latest_contents(
    hours: int = Query(24, ge=1, le=168, description="몇 시간 전까지 조회할지"),
    limit: int = Query(10, ge=1, le=50, description="조회할 컨텐츠 수"),
    brand_id: Optional[str] = Query(None, description="브랜드 필터")
) -> Dict[str, Any]:
    """최근 업로드된 캠페인 컨텐츠 프리뷰 조회"""
    try:
        contents = content_preview_service.get_latest_contents(
            hours_back=hours,
            limit=limit,
            brand_id=brand_id
        )
        
        return {
            "contents": contents,
            "total": len(contents),
            "filters_applied": {
                "hours_back": hours,
                "brand_id": brand_id
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"최신 컨텐츠 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/campaigns", summary="전체 캠페인 목록 조회")
async def get_campaigns_overview(
    status: Optional[str] = Query(None, description="캠페인 상태 필터"),
    brand_id: Optional[str] = Query(None, description="브랜드 필터"),
    month: Optional[str] = Query(None, description="월 필터 (YYYY-MM 형태)"),
    campaign_ids: Optional[str] = Query(None, description="캠페인 ID 리스트 (쉼표 구분)"),
    limit: int = Query(50, ge=1, le=200, description="조회 개수")
) -> Dict[str, Any]:
    """인플루언서 모니터링 대시보드용 캠페인 목록 조회 (다중 필터 지원)"""
    try:
        # 동적 쿼리 생성
        base_query = """
        SELECT id, camp_code, camp_nm, start_date, end_date, status, 
               target_cnt, brand_id, engmt_avg, engmt_cnt, part_cds, campaign_hashtags
        FROM campaign 
        WHERE 1=1
        """
        
        params = {}
        
        # 브랜드 필터
        if brand_id:
            base_query += " AND brand_id = :brand_id"
            params["brand_id"] = brand_id
        
        # 상태 필터
        if status:
            base_query += " AND status = :status"
            params["status"] = status
        
        # 월 필터
        if month:
            try:
                month_start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
                if month_start.month == 12:
                    month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
                
                base_query += """ AND (
                    start_date BETWEEN :month_start AND :month_end
                    OR end_date BETWEEN :month_start AND :month_end
                    OR (start_date <= :month_start AND end_date >= :month_end)
                )"""
                params["month_start"] = month_start.strftime('%Y-%m-%d')
                params["month_end"] = month_end.strftime('%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="월 형식이 올바르지 않습니다 (YYYY-MM)")
        
        # 특정 캠페인 ID들 필터
        if campaign_ids:
            try:
                id_list = [id.strip() for id in campaign_ids.split(',') if id.strip()]
                if id_list:
                    placeholders = ', '.join([f':campaign_id_{i}' for i in range(len(id_list))])
                    base_query += f" AND id IN ({placeholders})"
                    for i, campaign_id in enumerate(id_list):
                        params[f"campaign_id_{i}"] = campaign_id
            except Exception:
                raise HTTPException(status_code=400, detail="캠페인 ID 형식이 올바르지 않습니다")
        
        # 정렬 및 제한
        base_query += " ORDER BY start_date DESC"
        if limit:
            base_query += f" LIMIT {limit}"
        
        # 쿼리 실행
        campaigns = get_snowflake_service().execute_query(base_query, params)
        
        # 각 캠페인별 상세 정보 집계
        dashboard_data = []
        for campaign in campaigns:
            campaign_data = await _build_campaign_dashboard_data(campaign)
            dashboard_data.append(campaign_data)
        
        return {
            "campaigns": dashboard_data,
            "total": len(dashboard_data),
            "filters_applied": {
                "status": status,
                "brand_id": brand_id,
                "month": month,
                "campaign_ids": campaign_ids.split(',') if campaign_ids else None
            }
        }
        
    except Exception as e:
        logger.error(f"캠페인 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/campaigns/{campaign_id}/detail", summary="캠페인 상세 모니터링")
async def get_campaign_detail(campaign_id: str) -> CampaignDashboardResponse:
    """특정 캠페인의 상세 모니터링 정보"""
    try:
        # 캠페인 기본 정보
        campaigns = get_snowflake_service().execute_query(
            "SELECT * FROM campaign WHERE id = :campaign_id",
            {"campaign_id": campaign_id}
        )
        
        if not campaigns:
            raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다")
        
        campaign = campaigns[0]
        return await _build_campaign_dashboard_data(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캠페인 상세 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/campaigns/{campaign_id}/influencers", summary="캠페인 인플루언서 현황")
async def get_campaign_influencers(
    campaign_id: str,
    progress_filter: Optional[str] = Query(None, description="진행 상태 필터")
) -> Dict[str, Any]:
    """캠페인별 인플루언서 진행 현황 상세 조회"""
    try:
        # 인플루언서 목록 조회
        influencers = get_snowflake_service().get_campaign_influencers(
            campaign_id=campaign_id
        )
        
        if progress_filter:
            influencers = [i for i in influencers if i.get('progress') == progress_filter]
        
        # 배송 정보도 함께 조회
        if influencers:
            influencer_ids = [str(i['id']) for i in influencers]
            deliveries_query = f"""
            SELECT campaign_influencer_id, status, delivery_confirm_dt, 
                   create_dt, qty, price_total
            FROM delivery_entry 
            WHERE campaign_influencer_id IN ('{"', '".join(influencer_ids)}')
            """
            deliveries = get_snowflake_service().execute_query(deliveries_query)
            delivery_map = {str(d['campaign_influencer_id']): d for d in deliveries}
        else:
            delivery_map = {}
        
        # 데이터 통합
        detailed_influencers = []
        for influencer in influencers:
            influencer_id = str(influencer['id'])
            delivery_info = delivery_map.get(influencer_id, {})
            
            detailed_influencers.append({
                **influencer,
                "delivery_info": delivery_info,
                "days_since_casting": _calculate_days_since(influencer.get('cast_msg_dt')),
                "days_since_delivery": _calculate_days_since(delivery_info.get('delivery_confirm_dt')),
                "needs_attention": _check_needs_attention(influencer, delivery_info)
            })
        
        return {
            "campaign_id": campaign_id,
            "influencers": detailed_influencers,
            "total": len(detailed_influencers),
            "progress_summary": _summarize_progress(influencers)
        }
        
    except Exception as e:
        logger.error(f"캠페인 인플루언서 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


# === 상태 업데이트 API ===

@router.put("/campaigns/{campaign_id}/update", summary="캠페인 상태 업데이트")
async def update_campaign(
    campaign_id: str,
    update_data: CampaignUpdateRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """캠페인 상태 및 정보 업데이트"""
    try:
        # 업데이트 쿼리 구성
        update_fields = []
        params = {"campaign_id": campaign_id}
        
        if update_data.status:
            update_fields.append("status = :status")
            params["status"] = update_data.status
            
        if update_data.end_date:
            update_fields.append("end_date = :end_date")
            params["end_date"] = update_data.end_date
            
        if update_data.target_cnt is not None:
            update_fields.append("target_cnt = :target_cnt")
            params["target_cnt"] = update_data.target_cnt
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="업데이트할 필드가 없습니다")
        
        # 업데이트 실행
        update_query = f"""
        UPDATE campaign 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP()
        WHERE id = :campaign_id
        """
        
        get_snowflake_service().execute_query(update_query, params)
        
        # 백그라운드에서 비즈니스 룰 체크
        background_tasks.add_task(_check_campaign_business_rules, campaign_id)
        
        logger.info(f"캠페인 {campaign_id} 업데이트 완료: {update_data.dict(exclude_none=True)}")
        
        return {
            "message": "캠페인이 성공적으로 업데이트되었습니다",
            "campaign_id": campaign_id,
            "updated_fields": list(params.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캠페인 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"업데이트 실패: {str(e)}")


@router.put("/influencers/{influencer_id}/progress", summary="인플루언서 진행 상태 업데이트")
async def update_influencer_progress(
    influencer_id: str,
    update_data: InfluencerProgressUpdate,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """인플루언서 진행 상태 업데이트"""
    try:
        # 업데이트 쿼리 구성
        update_fields = ["progress = :progress"]
        params = {
            "influencer_id": influencer_id,
            "progress": update_data.progress
        }
        
        if update_data.cast_status:
            update_fields.append("cast_status = :cast_status")
            params["cast_status"] = update_data.cast_status
            
        if update_data.contents_post_dt:
            update_fields.append("contents_post_dt = :contents_post_dt")
            params["contents_post_dt"] = update_data.contents_post_dt
        
        # 업데이트 실행
        update_query = f"""
        UPDATE campaign_influencer 
        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP()
        WHERE id = :influencer_id
        """
        
        get_snowflake_service().execute_query(update_query, params)
        
        # 백그라운드에서 비즈니스 룰 체크
        background_tasks.add_task(_check_influencer_business_rules, influencer_id)
        
        logger.info(f"인플루언서 {influencer_id} 진행 상태 업데이트: {update_data.progress}")
        
        return {
            "message": "진행 상태가 성공적으로 업데이트되었습니다",
            "influencer_id": influencer_id,
            "new_progress": update_data.progress
        }
        
    except Exception as e:
        logger.error(f"인플루언서 진행 상태 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"업데이트 실패: {str(e)}")


# === 비즈니스 룰 모니터링 ===

@router.get("/campaigns/{campaign_id}/alerts", summary="캠페인 비즈니스 룰 알림")
async def get_campaign_alerts(campaign_id: str) -> Dict[str, Any]:
    """특정 캠페인의 비즈니스 룰 위반 알림 조회"""
    try:
        # 캠페인 관련 데이터 조회
        campaigns = get_snowflake_service().execute_query(
            "SELECT * FROM campaign WHERE id = :campaign_id",
            {"campaign_id": campaign_id}
        )
        
        if not campaigns:
            raise HTTPException(status_code=404, detail="캠페인을 찾을 수 없습니다")
        
        # 룰 엔진 실행
        rule_results = rule_engine.execute_rules_with_real_data(days_back=30)
        
        # 해당 캠페인 관련 알림만 필터링
        campaign_alerts = []
        for result in rule_results:
            if result.triggered:
                for record in result.matched_records:
                    if (record.get('campaign_influencer', {}).get('campaign_id') == campaign_id or
                        record.get('campaign', {}).get('id') == campaign_id):
                        campaign_alerts.append({
                            "rule_id": result.rule_id,
                            "rule_name": _get_rule_name(result.rule_id),
                            "priority": _get_rule_priority(result.rule_id),
                            "details": record,
                            "triggered_at": result.execution_time.isoformat()
                        })
        
        return {
            "campaign_id": campaign_id,
            "alerts": campaign_alerts,
            "total_alerts": len(campaign_alerts),
            "high_priority_count": len([a for a in campaign_alerts if a["priority"] == "high"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캠페인 알림 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


# === 통계 및 요약 API ===

@router.get("/filter-options/hierarchical", summary="계층적 필터 옵션 전체 조회")
async def get_hierarchical_filter_options() -> Dict[str, Any]:
    """브랜드 → 월 → 캠페인 계층적 필터 옵션 한번에 조회"""
    try:
        # 전체 브랜드 목록
        brands = get_snowflake_service().get_brands()
        
        hierarchical_data = []
        
        for brand in brands:
            brand_id = str(brand.get('id', ''))
            brand_name = brand.get('brand_nm', '')
            
            # 해당 브랜드의 월별 데이터
            months_query = """
            SELECT DISTINCT 
                DATE_TRUNC('month', start_date) as campaign_month,
                COUNT(*) as campaign_count
            FROM campaign 
            WHERE brand_id = :brand_id
            GROUP BY DATE_TRUNC('month', start_date)
            ORDER BY campaign_month DESC
            """
            
            months_result = get_snowflake_service().execute_query(
                months_query, {"brand_id": brand_id}
            )
            
            month_data = []
            for row in months_result:
                campaign_month = row.get('campaign_month')
                if campaign_month:
                    month_str = campaign_month.strftime('%Y-%m')
                    month_display = campaign_month.strftime('%Y년 %m월')
                    
                    # 해당 월의 캠페인 목록 (간단 버전)
                    month_start = campaign_month
                    if month_start.month == 12:
                        month_end = datetime(month_start.year + 1, 1, 1) - timedelta(days=1)
                    else:
                        month_end = datetime(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
                    
                    campaigns_query = """
                    SELECT id, camp_code, camp_nm, status
                    FROM campaign 
                    WHERE brand_id = :brand_id
                    AND (start_date BETWEEN :month_start AND :month_end
                         OR end_date BETWEEN :month_start AND :month_end)
                    ORDER BY start_date DESC
                    """
                    
                    month_campaigns = get_snowflake_service().execute_query(campaigns_query, {
                        "brand_id": brand_id,
                        "month_start": month_start.strftime('%Y-%m-%d'),
                        "month_end": month_end.strftime('%Y-%m-%d')
                    })
                    
                    campaign_list = [
                        {
                            "campaign_id": str(c['id']),
                            "camp_code": c.get('camp_code', ''),
                            "camp_nm": c.get('camp_nm', ''),
                            "status": c.get('status', '')
                        }
                        for c in month_campaigns
                    ]
                    
                    month_data.append({
                        "month_key": month_str,
                        "month_display": month_display,
                        "campaign_count": row.get('campaign_count', 0),
                        "campaigns": campaign_list
                    })
            
            hierarchical_data.append({
                "brand_id": brand_id,
                "brand_name": brand_name,
                "total_campaigns": sum(m["campaign_count"] for m in month_data),
                "months": month_data
            })
        
        return {
            "hierarchical_filters": hierarchical_data,
            "summary": {
                "total_brands": len(hierarchical_data),
                "total_campaigns": sum(b["total_campaigns"] for b in hierarchical_data)
            }
        }
        
    except Exception as e:
        logger.error(f"계층적 필터 옵션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@router.get("/dashboard/summary", summary="대시보드 전체 요약")
async def get_dashboard_summary(
    days_range: int = Query(30, ge=1, le=90, description="조회 기간 (일)"),
    brand_id: Optional[str] = Query(None, description="브랜드 필터"),
    month: Optional[str] = Query(None, description="월 필터 (YYYY-MM 형태)"),
    campaign_ids: Optional[str] = Query(None, description="캠페인 ID 리스트 (쉼표 구분)")
) -> Dict[str, Any]:
    """인플루언서 모니터링 대시보드 전체 요약 정보 (필터 지원)"""
    try:
        # 필터 적용된 캠페인 현황 조회
        query_params = {}
        
        if brand_id:
            query_params["brand_id"] = brand_id
        if month:
            query_params["month"] = month
        if campaign_ids:
            query_params["campaign_ids"] = campaign_ids
        
        # get_campaigns_overview의 로직을 재사용하여 필터된 캠페인 조회
        filtered_campaigns_response = await get_campaigns_overview(
            status=None,
            brand_id=brand_id,
            month=month,
            campaign_ids=campaign_ids,
            limit=1000  # 요약을 위해 많은 수 조회
        )
        
        campaigns = [c for campaign_data in filtered_campaigns_response["campaigns"] 
                    for c in [{"id": campaign_data["campaign_id"], 
                              "status": campaign_data["status"]}]]
        
        # 전체 캠페인에서 활성 캠페인 필터링
        active_campaigns = [c for c in campaigns if c.get('status') not in ['COMPLETE', 'CANCELLED']]
        
        # 전체 인플루언서 현황
        all_influencers = get_snowflake_service().get_campaign_influencers()
        
        # 배송 현황
        deliveries = get_snowflake_service().get_delivery_entries(
            date_from=datetime.now() - timedelta(days=days_range)
        )
        
        # 비즈니스 룰 알림
        rule_results = rule_engine.execute_rules_with_real_data(days_back=days_range)
        active_alerts = [r for r in rule_results if r.triggered]
        
        return {
            "period": f"최근 {days_range}일",
            "filters_applied": {
                "brand_id": brand_id,
                "month": month,
                "campaign_ids": campaign_ids.split(',') if campaign_ids else None
            },
            "campaigns": {
                "total": len(campaigns),
                "active": len(active_campaigns),
                "completed_this_period": len([c for c in campaigns if c.get('status') == 'COMPLETE'])
            },
            "influencers": {
                "total_participations": len(all_influencers),
                "content_uploaded": len([i for i in all_influencers if i.get('contents_post_dt')]),
                "awaiting_upload": len([i for i in all_influencers if not i.get('contents_post_dt')])
            },
            "delivery": {
                "total_entries": len(deliveries),
                "completed": len([d for d in deliveries if d.get('status') == 'COMPLETE']),
                "in_progress": len([d for d in deliveries if d.get('status') in ['DELIVERY_IN_PROGRESS', 'AWAITING_DELIVERY_START']])
            },
            "alerts": {
                "total_rules_triggered": len(active_alerts),
                "high_priority": len([a for a in active_alerts if _get_rule_priority(a.rule_id) == "high"]),
                "recent_alerts": active_alerts[:5]
            }
        }
        
    except Exception as e:
        logger.error(f"대시보드 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


# === 헬퍼 함수들 ===

async def _build_campaign_dashboard_data(campaign: Dict) -> CampaignDashboardResponse:
    """캠페인 대시보드 데이터 구성"""
    campaign_id = str(campaign['id'])
    
    # 인플루언서 현황 조회
    influencers = get_snowflake_service().get_campaign_influencers(campaign_id=campaign_id)
    
    # 진행 상태별 집계
    progress_summary = {}
    for influencer in influencers:
        progress = influencer.get('progress', 'UNKNOWN')
        progress_summary[progress] = progress_summary.get(progress, 0) + 1
    
    # 완료율 계산
    total_influencers = len(influencers)
    completed_count = progress_summary.get('COMPLETE', 0)
    completion_rate = (completed_count / total_influencers * 100) if total_influencers > 0 else 0
    
    # 컨텐츠 업로드율
    uploaded_count = len([i for i in influencers if i.get('contents_post_dt')])
    content_upload_rate = (uploaded_count / total_influencers * 100) if total_influencers > 0 else 0
    
    # 배송 완료율 (해당 캠페인의 배송 정보 조회)
    if influencers:
        influencer_ids = [str(i['id']) for i in influencers]
        deliveries_query = f"""
        SELECT status FROM delivery_entry 
        WHERE campaign_influencer_id IN ('{"', '".join(influencer_ids)}')
        """
        deliveries = get_snowflake_service().execute_query(deliveries_query)
        delivery_completed = len([d for d in deliveries if d.get('status') == 'COMPLETE'])
        delivery_completion_rate = (delivery_completed / len(deliveries) * 100) if deliveries else 0
    else:
        delivery_completion_rate = 0
    
    # 임박한 마감일 체크
    upcoming_deadlines = _check_upcoming_deadlines(campaign, influencers)
    
    # 비즈니스 룰 알림
    business_rule_alerts = await _get_campaign_business_rule_alerts(campaign_id)
    
    return CampaignDashboardResponse(
        campaign_id=campaign_id,
        camp_nm=campaign.get('camp_nm', ''),
        status=campaign.get('status', ''),
        progress_summary=progress_summary,
        total_influencers=total_influencers,
        completion_rate=round(completion_rate, 2),
        content_upload_rate=round(content_upload_rate, 2),
        delivery_completion_rate=round(delivery_completion_rate, 2),
        upcoming_deadlines=upcoming_deadlines,
        business_rule_alerts=business_rule_alerts
    )


def _calculate_days_since(date_str: Optional[str]) -> Optional[int]:
    """날짜로부터 경과일 계산"""
    if not date_str:
        return None
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return (datetime.now() - date_obj).days
    except:
        return None


def _check_needs_attention(influencer: Dict, delivery_info: Dict) -> bool:
    """주의 필요 여부 체크"""
    # 배송 완료 후 7일 이상 컨텐츠 미업로드
    if (delivery_info.get('status') == 'COMPLETE' and 
        not influencer.get('contents_post_dt') and
        _calculate_days_since(delivery_info.get('delivery_confirm_dt', '')) and
        _calculate_days_since(delivery_info.get('delivery_confirm_dt', '')) > 7):
        return True
    
    # 섭외 후 3일 이상 응답 없음
    if (influencer.get('cast_status') == 'AWAITING_RESPONSE' and
        _calculate_days_since(influencer.get('cast_msg_dt', '')) and
        _calculate_days_since(influencer.get('cast_msg_dt', '')) > 3):
        return True
    
    return False


def _summarize_progress(influencers: List[Dict]) -> Dict[str, int]:
    """진행 상태 요약"""
    summary = {}
    for influencer in influencers:
        progress = influencer.get('progress', 'UNKNOWN')
        summary[progress] = summary.get(progress, 0) + 1
    return summary


def _check_upcoming_deadlines(campaign: Dict, influencers: List[Dict]) -> List[Dict]:
    """임박한 마감일 체크"""
    deadlines = []
    
    # 캠페인 종료일 체크
    end_date = campaign.get('end_date')
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            days_left = (end_dt - datetime.now()).days
            
            if 0 <= days_left <= 3:  # 3일 이내 마감
                pending_uploads = [i for i in influencers if not i.get('contents_post_dt')]
                deadlines.append({
                    "type": "campaign_end",
                    "days_left": days_left,
                    "description": f"캠페인 종료까지 {days_left}일",
                    "pending_influencers": len(pending_uploads)
                })
        except:
            pass
    
    return deadlines


async def _get_campaign_business_rule_alerts(campaign_id: str) -> List[Dict]:
    """캠페인별 비즈니스 룰 알림 조회"""
    try:
        rule_results = rule_engine.execute_rules_with_real_data(days_back=30)
        alerts = []
        
        for result in rule_results:
            if result.triggered:
                for record in result.matched_records:
                    if (record.get('campaign_influencer', {}).get('campaign_id') == campaign_id):
                        alerts.append({
                            "rule_id": result.rule_id,
                            "priority": _get_rule_priority(result.rule_id),
                            "message": _format_rule_message(result.rule_id, record)
                        })
        
        return alerts[:5]  # 최대 5개까지
    except:
        return []


def _get_rule_name(rule_id: str) -> str:
    """룰 ID로 룰 이름 조회"""
    rule_names = {
        "MKT_001": "컨텐츠 업로드 미완료 알림",
        "MKT_002": "캠페인 종료 임박 알림",
        "MKT_003": "배송 지연으로 인한 캠페인 연장 검토",
        "MKT_004": "해시태그 가이드라인 미준수 알림"
    }
    return rule_names.get(rule_id, f"규칙 {rule_id}")


def _get_rule_priority(rule_id: str) -> str:
    """룰 ID로 우선순위 조회"""
    priorities = {
        "MKT_001": "high",
        "MKT_002": "high", 
        "MKT_003": "medium",
        "MKT_004": "high"
    }
    return priorities.get(rule_id, "medium")


def _format_rule_message(rule_id: str, record: Dict) -> str:
    """룰 위반 메시지 포맷팅"""
    if rule_id == "MKT_001":
        days = record.get('days_overdue', 0)
        return f"배송 완료 후 {days}일이 지났으나 컨텐츠가 업로드되지 않았습니다"
    elif rule_id == "MKT_002":
        return "캠페인 종료가 임박했으나 컨텐츠가 업로드되지 않았습니다"
    elif rule_id == "MKT_003":
        return "배송 지연으로 인한 캠페인 기간 연장 검토가 필요합니다"
    elif rule_id == "MKT_004":
        return "필수 해시태그가 포함되지 않은 컨텐츠가 업로드되었습니다"
    return "비즈니스 규칙 위반이 감지되었습니다"


async def _check_campaign_business_rules(campaign_id: str):
    """캠페인 비즈니스 룰 체크 (백그라운드)"""
    try:
        logger.info(f"캠페인 {campaign_id} 비즈니스 룰 체크 시작")
        rule_results = rule_engine.execute_rules_with_real_data(days_back=30)
        # 실제 알림 처리 로직 구현 가능
    except Exception as e:
        logger.error(f"캠페인 비즈니스 룰 체크 실패: {e}")


async def _check_influencer_business_rules(influencer_id: str):
    """인플루언서 비즈니스 룰 체크 (백그라운드)"""
    try:
        logger.info(f"인플루언서 {influencer_id} 비즈니스 룰 체크 시작")
        rule_results = rule_engine.execute_rules_with_real_data(days_back=30)
        # 실제 알림 처리 로직 구현 가능
    except Exception as e:
        logger.error(f"인플루언서 비즈니스 룰 체크 실패: {e}")
