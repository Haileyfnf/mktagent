"""
온톨로지 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from loguru import logger

from ..services.ontology_duckdb import ontology_db, DomainConcept, DomainRelation, BusinessRule

router = APIRouter()


@router.on_event("startup")
async def load_ontology():
    """앱 시작 시 온톨로지 파일 로드"""
    success = ontology_db.load_all()
    if not success:
        logger.error("온톨로지 DuckDB 로드 실패")
    else:
        logger.info("온톨로지 DuckDB 로드 성공")


@router.get("/", summary="온톨로지 전체 요약")
async def get_ontology_summary() -> Dict[str, Any]:
    """온톨로지 전체 요약 정보를 반환합니다."""
    try:
        return ontology_db.get_domain_summary()
    except Exception as e:
        logger.error(f"온톨로지 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="온톨로지 요약 조회 실패")


@router.get("/domains", summary="모든 도메인 목록")
async def get_domains() -> List[str]:
    """모든 도메인 이름 목록을 반환합니다."""
    try:
        return ontology_db.get_all_domains()
    except Exception as e:
        logger.error(f"도메인 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="도메인 목록 조회 실패")


@router.get("/domains/{domain_name}/concepts", summary="도메인 개념 조회")
async def get_domain_concepts(domain_name: str) -> Dict[str, DomainConcept]:
    """특정 도메인의 모든 개념을 반환합니다."""
    try:
        concepts = ontology_db.get_domain_concepts(domain_name)
        if not concepts:
            raise HTTPException(
                status_code=404, 
                detail=f"도메인 '{domain_name}'을 찾을 수 없거나 개념이 없습니다."
            )
        return concepts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"도메인 개념 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="도메인 개념 조회 실패")


@router.get("/relations", summary="도메인 간 관계 조회")
async def get_relations(
    from_domain: Optional[str] = Query(None, description="출발 도메인 필터"),
    to_domain: Optional[str] = Query(None, description="도착 도메인 필터")
) -> List[DomainRelation]:
    """도메인 간 관계를 조회합니다. 필터 조건을 적용할 수 있습니다."""
    try:
        return ontology_db.get_domain_relations(from_domain, to_domain)
    except Exception as e:
        logger.error(f"관계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="관계 조회 실패")


@router.get("/business-rules", summary="비즈니스 규칙 조회")
async def get_business_rules(
    priority: Optional[str] = Query(None, description="우선순위 필터 (high, medium, low)")
) -> List[BusinessRule]:
    """비즈니스 규칙을 조회합니다. 우선순위로 필터링할 수 있습니다."""
    try:
        return ontology_db.get_business_rules(priority)
    except Exception as e:
        logger.error(f"비즈니스 규칙 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="비즈니스 규칙 조회 실패")


@router.get("/business-rules/{rule_id}", summary="특정 비즈니스 규칙 조회")
async def get_business_rule(rule_id: str) -> BusinessRule:
    """ID로 특정 비즈니스 규칙을 조회합니다."""
    try:
        rule = ontology_db.get_business_rule_by_id(rule_id)
        if not rule:
            raise HTTPException(
                status_code=404, 
                detail=f"비즈니스 규칙 '{rule_id}'를 찾을 수 없습니다."
            )
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비즈니스 규칙 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="비즈니스 규칙 조회 실패")


@router.get("/search/concepts", summary="개념 검색")
async def search_concepts(
    query: str = Query(..., description="검색할 개념명"),
    domain: Optional[str] = Query(None, description="검색할 도메인 제한")
) -> Dict[str, List[str]]:
    """개념명으로 검색합니다."""
    try:
        return ontology_db.search_concepts(query, domain)
    except Exception as e:
        logger.error(f"개념 검색 실패: {e}")
        raise HTTPException(status_code=500, detail="개념 검색 실패")


@router.get("/validate", summary="온톨로지 검증")
async def validate_ontology() -> Dict[str, Any]:
    """온톨로지의 일관성을 검증합니다."""
    try:
        # 기본적인 검증 로직
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "domain_count": len(ontology_db.get_all_domains()),
            "relation_count": len(ontology_db.get_domain_relations()),
            "rule_count": len(ontology_db.get_business_rules())
        }
        
        # 도메인 검증
        for domain_name in ontology_db.get_all_domains():
            concepts = ontology_db.get_domain_concepts(domain_name)
            if not concepts:
                validation_result["warnings"].append(f"도메인 '{domain_name}'에 개념이 없습니다.")
        
        # 비즈니스 규칙 검증
        for rule in ontology_db.get_business_rules():
            if not rule.condition.strip():
                validation_result["errors"].append(f"규칙 '{rule.id}'의 조건이 비어있습니다.")
                validation_result["is_valid"] = False
            if not rule.action.strip():
                validation_result["errors"].append(f"규칙 '{rule.id}'의 액션이 비어있습니다.")
                validation_result["is_valid"] = False
        
        return validation_result
    except Exception as e:
        logger.error(f"온톨로지 검증 실패: {e}")
        raise HTTPException(status_code=500, detail="온톨로지 검증 실패")


@router.get("/analytics/domain-stats", summary="도메인별 통계")
async def get_domain_analytics() -> Dict[str, Any]:
    """도메인별 상세 통계를 반환합니다."""
    try:
        # DuckDB의 SQL 분석 기능 활용
        stats = ontology_db.execute_custom_query("""
            SELECT 
                d.name as domain,
                d.description,
                COUNT(c.id) as concept_count,
                COUNT(DISTINCT c.name) as unique_concepts,
                AVG(JSON_ARRAY_LENGTH(c.properties)) as avg_properties_per_concept
            FROM domains d
            LEFT JOIN concepts c ON d.name = c.domain
            GROUP BY d.name, d.description
            ORDER BY concept_count DESC
        """)
        
        # 관계 통계
        relation_stats = ontology_db.execute_custom_query("""
            SELECT 
                section,
                COUNT(*) as relation_count,
                COUNT(DISTINCT from_entity) as unique_from_entities,
                COUNT(DISTINCT to_entity) as unique_to_entities
            FROM relations
            GROUP BY section
        """)
        
        return {
            "domain_statistics": [
                {
                    "domain": row[0],
                    "description": row[1],
                    "concept_count": row[2],
                    "unique_concepts": row[3],
                    "avg_properties_per_concept": float(row[4]) if row[4] else 0
                }
                for row in stats
            ],
            "relation_statistics": [
                {
                    "section": row[0],
                    "relation_count": row[1],
                    "unique_from_entities": row[2],
                    "unique_to_entities": row[3]
                }
                for row in relation_stats
            ]
        }
    except Exception as e:
        logger.error(f"도메인 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="도메인 통계 조회 실패")


@router.get("/query/complex-relations", summary="복합 관계 조회")
async def get_complex_relations(
    entity: str = Query(..., description="조회할 엔티티명"),
    depth: int = Query(1, description="관계 탐색 깊이", ge=1, le=3)
) -> Dict[str, Any]:
    """특정 엔티티와 연결된 모든 관계를 깊이별로 조회합니다."""
    try:
        # 직접 연결된 관계
        direct_relations = ontology_db.execute_custom_query("""
            SELECT relation, from_entity, to_entity, description, cardinality
            FROM relations
            WHERE from_entity LIKE ? OR to_entity LIKE ?
        """, [f"%{entity}%", f"%{entity}%"])
        
        # 간접 관계 (2단계)
        indirect_relations = []
        if depth >= 2:
            indirect_relations = ontology_db.execute_custom_query("""
                WITH direct_connected AS (
                    SELECT DISTINCT 
                        CASE WHEN from_entity LIKE ? THEN to_entity ELSE from_entity END as connected_entity
                    FROM relations
                    WHERE from_entity LIKE ? OR to_entity LIKE ?
                )
                SELECT DISTINCT r.relation, r.from_entity, r.to_entity, r.description, r.cardinality
                FROM relations r
                JOIN direct_connected dc ON (r.from_entity = dc.connected_entity OR r.to_entity = dc.connected_entity)
                WHERE NOT (r.from_entity LIKE ? OR r.to_entity LIKE ?)
            """, [f"%{entity}%", f"%{entity}%", f"%{entity}%", f"%{entity}%", f"%{entity}%"])
        
        return {
            "entity": entity,
            "depth": depth,
            "direct_relations": [
                {
                    "relation": row[0],
                    "from_entity": row[1],
                    "to_entity": row[2],
                    "description": row[3],
                    "cardinality": row[4]
                }
                for row in direct_relations
            ],
            "indirect_relations": [
                {
                    "relation": row[0],
                    "from_entity": row[1],
                    "to_entity": row[2],
                    "description": row[3],
                    "cardinality": row[4]
                }
                for row in indirect_relations
            ] if depth >= 2 else []
        }
    except Exception as e:
        logger.error(f"복합 관계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="복합 관계 조회 실패")


@router.post("/query/custom", summary="커스텀 SQL 쿼리")
async def execute_custom_query(
    query: str = Query(..., description="실행할 SQL 쿼리")
) -> Dict[str, Any]:
    """커스텀 SQL 쿼리를 실행합니다. (읽기 전용)"""
    try:
        # 보안을 위해 SELECT 문만 허용
        if not query.strip().upper().startswith('SELECT'):
            raise HTTPException(status_code=400, detail="SELECT 문만 허용됩니다.")
        
        # 위험한 키워드 차단
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE']
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise HTTPException(status_code=400, detail=f"'{keyword}' 키워드는 허용되지 않습니다.")
        
        result = ontology_db.execute_custom_query(query)
        
        return {
            "query": query,
            "result_count": len(result),
            "results": result[:100]  # 최대 100개 결과만 반환
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"커스텀 쿼리 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"쿼리 실행 실패: {str(e)}")
