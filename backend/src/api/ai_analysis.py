"""
AI 분석 보고서 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from ..services.ai_analysis_service import get_ai_analysis_service, AnalysisRequest, AnalysisReport

router = APIRouter()


@router.post("/generate/campaign-performance", summary="캠페인 성과 AI 분석")
async def generate_campaign_analysis(
    background_tasks: BackgroundTasks,
    days_back: int = Query(30, description="분석 기간 (일)", ge=1, le=365),
    brand_id: Optional[str] = Query(None, description="특정 브랜드 ID"),
    specific_month: Optional[str] = Query(None, description="특정 월 분석 (YYYY-MM 형식, 예: 2024-07)"),
    run_async: bool = Query(False, description="백그라운드 실행 여부")
) -> Dict[str, Any]:
    """캠페인 성과 AI 분석 보고서를 생성합니다."""
    try:
        if run_async:
            # 백그라운드에서 실행
            background_tasks.add_task(
                get_ai_analysis_service().analyze_campaign_performance,
                days_back=days_back,
                brand_id=brand_id,
                specific_month=specific_month
            )
            return {
                "message": f"캠페인 성과 분석이 백그라운드에서 시작되었습니다. {'(' + specific_month + ' 월 분석)' if specific_month else ''}",
                "status": "processing",
                "estimated_time": "2-3분"
            }
        else:
            # 동기 실행
            report = get_ai_analysis_service().analyze_campaign_performance(
                days_back=days_back,
                brand_id=brand_id,
                specific_month=specific_month
            )
            return {
                "message": "캠페인 성과 분석 완료",
                "status": "completed",
                "report": report.dict()
            }
            
    except Exception as e:
        logger.error(f"캠페인 성과 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")


@router.post("/generate/delivery-analysis", summary="배송 성과 AI 분석")
async def generate_delivery_analysis(
    background_tasks: BackgroundTasks,
    days_back: int = Query(30, description="분석 기간 (일)", ge=1, le=365),
    run_async: bool = Query(False, description="백그라운드 실행 여부")
) -> Dict[str, Any]:
    """배송 성과 AI 분석 보고서를 생성합니다."""
    try:
        if run_async:
            background_tasks.add_task(
                get_ai_analysis_service().analyze_delivery_performance,
                days_back=days_back
            )
            return {
                "message": "배송 성과 분석이 백그라운드에서 시작되었습니다.",
                "status": "processing"
            }
        else:
            report = get_ai_analysis_service().analyze_delivery_performance(days_back=days_back)
            return {
                "message": "배송 성과 분석 완료",
                "status": "completed", 
                "report": report.dict()
            }
            
    except Exception as e:
        logger.error(f"배송 성과 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")


@router.post("/generate/business-rules-impact", summary="비즈니스 룰 영향도 AI 분석")
async def generate_business_rules_analysis(
    background_tasks: BackgroundTasks,
    days_back: int = Query(30, description="분석 기간 (일)", ge=1, le=365),
    run_async: bool = Query(False, description="백그라운드 실행 여부")
) -> Dict[str, Any]:
    """비즈니스 룰 영향도 AI 분석 보고서를 생성합니다."""
    try:
        if run_async:
            background_tasks.add_task(
                get_ai_analysis_service().analyze_business_rules_impact,
                days_back=days_back
            )
            return {
                "message": "비즈니스 룰 영향도 분석이 백그라운드에서 시작되었습니다.",
                "status": "processing"
            }
        else:
            report = get_ai_analysis_service().analyze_business_rules_impact(days_back=days_back)
            return {
                "message": "비즈니스 룰 영향도 분석 완료",
                "status": "completed",
                "report": report.dict()
            }
            
    except Exception as e:
        logger.error(f"비즈니스 룰 영향도 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")


@router.get("/reports/list", summary="생성된 보고서 목록")
async def list_reports() -> Dict[str, Any]:
    """생성된 AI 분석 보고서 목록을 조회합니다."""
    try:
        import os
        from pathlib import Path
        
        reports_dir = Path("backend/reports")
        if not reports_dir.exists():
            return {"reports": [], "total": 0}
        
        report_files = []
        for file_path in reports_dir.glob("*.md"):
            stat = file_path.stat()
            report_files.append({
                "filename": file_path.name,
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # 최신순 정렬
        report_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "reports": report_files,
            "total": len(report_files)
        }
        
    except Exception as e:
        logger.error(f"보고서 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="보고서 목록 조회 실패")


@router.get("/reports/{filename}", summary="보고서 내용 조회")
async def get_report_content(filename: str) -> Dict[str, Any]:
    """특정 보고서의 내용을 조회합니다."""
    try:
        from pathlib import Path
        
        # 보안을 위해 파일명 검증
        if not filename.endswith('.md') or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="잘못된 파일명입니다.")
        
        file_path = Path("backend/reports") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        stat = file_path.stat()
        
        return {
            "filename": filename,
            "content": content,
            "size_kb": round(stat.st_size / 1024, 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 내용 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="보고서 조회 실패")


@router.delete("/reports/{filename}", summary="보고서 삭제")
async def delete_report(filename: str) -> Dict[str, Any]:
    """특정 보고서를 삭제합니다."""
    try:
        from pathlib import Path
        
        # 보안을 위해 파일명 검증
        if not filename.endswith('.md') or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="잘못된 파일명입니다.")
        
        file_path = Path("backend/reports") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
        
        file_path.unlink()
        
        return {
            "message": f"보고서 '{filename}'이 삭제되었습니다.",
            "status": "deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="보고서 삭제 실패")


@router.get("/test/ontology-integration", summary="온톨로지 연동 상태 테스트")
async def test_ontology_integration() -> Dict[str, Any]:
    """온톨로지와 AI 분석의 연동 상태를 테스트"""
    try:
        # 온톨로지 컨텍스트 생성 테스트
        ontology_context = get_ai_analysis_service()._build_ontology_context()
        
        # 비즈니스 룰 체크 테스트 (샘플 데이터)
        sample_campaigns = [{"id": "test1", "status": "ACTIVE"}]
        sample_influencers = [{"id": "ci1", "CAST_STATUS": "ACCEPTED", "CONTENTS_POST_DT": None, "CAST_MSG_DT": "2024-01-01"}]
        sample_deliveries = [{"id": "del1", "STATUS": "COMPLETE"}]
        
        rule_violations = get_ai_analysis_service()._check_business_rule_violations(
            sample_campaigns, sample_influencers, sample_deliveries
        )
        
        return {
            "message": "온톨로지 연동 테스트 완료",
            "status": "success",
            "ontology_context_length": len(ontology_context),
            "context_preview": ontology_context[:500] + "..." if len(ontology_context) > 500 else ontology_context,
            "rule_violations_test": rule_violations,
            "integration_status": "연동 성공" if "F&F 인플루언서 마케팅 온톨로지" in ontology_context else "연동 실패"
        }
        
    except Exception as e:
        logger.error(f"온톨로지 연동 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"온톨로지 연동 테스트 실패: {str(e)}")


@router.get("/test/sample-analysis", summary="샘플 AI 분석 테스트")
async def test_sample_analysis() -> Dict[str, Any]:
    """Mock 데이터로 AI 분석 테스트를 실행합니다."""
    try:
        # 간단한 테스트 데이터
        test_data = {
            "campaigns": [
                {"id": "camp_001", "name": "여름 신상 캠페인", "status": "COMPLETE", "brand_id": "M"},
                {"id": "camp_002", "name": "가을 컬렉션", "status": "CASTING", "brand_id": "X"}
            ],
            "delivery_stats": {
                "total_deliveries": 150,
                "completed": 120,
                "in_progress": 25,
                "failed": 5,
                "completion_rate": 80.0
            }
        }
        
        # 온톨로지 기반 GPT 호출 테스트
        prompt = f"""
        다음 F&F 인플루언서 마케팅 데이터를 온톨로지 관점에서 분석해주세요:
        
        {json.dumps(test_data, ensure_ascii=False, indent=2)}
        
        ## 온톨로지 기반 분석 요청사항
        1. **마케팅 도메인**: 캠페인 현황 및 브랜드별 성과 요약
        2. **배송 도메인**: 시딩 배송 성과 및 효율성 분석
        3. **도메인 간 연계**: 마케팅-배송 플로우 최적화 관점
        4. **비즈니스 룰**: 정의된 규칙 대비 준수 현황
        5. **개선 권장사항**: 각 도메인 및 도메인 간 관계 개선 방안 2가지
        
        Markdown 형식으로 구조화하여 작성해주세요 (최대 25줄).
        """
        
        import json
        
        # GPT API 호출
        analysis_result = get_ai_analysis_service()._call_claude_api(prompt, max_tokens=1000)
        
        return {
            "message": "온톨로지 기반 샘플 AI 분석 테스트 완료",
            "test_data": test_data,
            "ai_analysis": analysis_result,
            "status": "success",
            "note": "이 분석은 YAML 온톨로지 컨텍스트를 포함합니다"
        }
        
    except Exception as e:
        logger.error(f"샘플 분석 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"테스트 실패: {str(e)}")


@router.get("/health", summary="AI 분석 서비스 상태")
async def ai_analysis_health() -> Dict[str, Any]:
    """AI 분석 서비스의 상태를 확인합니다."""
    try:
        import os
        
        # Claude API 키 확인
        api_key_status = "configured" if os.getenv("CLAUDE_API_KEY") else "missing"
        
        # 보고서 디렉토리 확인
        reports_dir = Path("backend/reports")
        reports_exist = reports_dir.exists()
        
        return {
            "status": "healthy",
            "claude_api_key": api_key_status,
            "reports_directory": "exists" if reports_exist else "missing",
            "available_analyses": [
                "campaign_performance",
                "delivery_analysis", 
                "business_rules_impact"
            ],
            "service": "ai_analysis_service"
        }
        
    except Exception as e:
        logger.error(f"AI 분석 서비스 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail="서비스 상태 확인 실패")
