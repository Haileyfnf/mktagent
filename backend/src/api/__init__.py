"""
API 라우터 모듈 초기화
"""
from fastapi import APIRouter
from .ontology import router as ontology_router
from .business_rules_engine import router as business_rules_router
from .ai_analysis import router as ai_analysis_router

api_router = APIRouter()

# 온톨로지 관련 엔드포인트 등록
api_router.include_router(ontology_router, prefix="/ontology", tags=["ontology"])

# 비즈니스 룰 엔진 엔드포인트 등록
api_router.include_router(business_rules_router, prefix="/rules", tags=["business-rules"])

# AI 분석 엔드포인트 등록
api_router.include_router(ai_analysis_router, prefix="/ai-analysis", tags=["ai-analysis"])
