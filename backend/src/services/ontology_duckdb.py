"""
DuckDB 기반 온톨로지 파싱 및 저장 서비스
F&F 인플루언서 마케팅 온톨로지 구조를 DuckDB에 저장하고 관리
"""
import os
import yaml
import duckdb
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic import BaseModel
from loguru import logger


class DomainConcept(BaseModel):
    """도메인 개념 모델"""
    name: str
    description: str
    properties: List[str]
    domain: str


class DomainRelation(BaseModel):
    """도메인 관계 모델"""
    relation: str
    from_entity: str
    to_entity: str
    via: str
    description: str
    cardinality: str


class BusinessRule(BaseModel):
    """비즈니스 규칙 모델"""
    id: str
    name: str
    condition: str
    action: str
    priority: str
    description: str
    staff_alert_template: Optional[str] = None
    influencer_message_template: Optional[str] = None


class OntologyDuckDB:
    """DuckDB 기반 온톨로지 관리 클래스"""
    
    def __init__(self, db_path: str = "ontology.duckdb", ontology_path: str = "ontology"):
        """
        온톨로지 DuckDB 초기화
        
        Args:
            db_path: DuckDB 파일 경로
            ontology_path: 온톨로지 YAML 파일들이 있는 경로
        """
        # 프로젝트 루트에서 상대 경로 계산
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent
        self.ontology_path = project_root / ontology_path
        
        # DuckDB 파일을 app/db/ 폴더에 저장
        db_dir = current_dir.parent.parent / "src" / "database"  # backend/app/services -> backend/src/database
        self.db_path = db_dir / db_path
        
        # DuckDB 연결 (UTF-8 인코딩 문제 해결)
        try:
            self.conn = duckdb.connect(str(self.db_path))
        except UnicodeDecodeError:
            # 경로에 한글이 있을 경우 임시 디렉토리 사용
            import tempfile
            temp_db_path = Path(tempfile.gettempdir()) / "ontology.duckdb"
            logger.warning(f"경로 인코딩 문제로 임시 경로 사용: {temp_db_path}")
            self.db_path = temp_db_path
            self.conn = duckdb.connect(str(self.db_path))
        
        # 테이블 초기화
        self._create_tables()
        
        logger.info(f"DuckDB 온톨로지 초기화 - DB: {self.db_path}, 온톨로지: {self.ontology_path}")
    
    def _create_tables(self):
        """온톨로지 저장용 테이블 생성"""
        
        # 도메인 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS domains (
                name VARCHAR PRIMARY KEY,
                description VARCHAR,
                version VARCHAR,
                raw_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 개념 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id VARCHAR PRIMARY KEY,
                domain VARCHAR,
                name VARCHAR,
                description VARCHAR,
                properties JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (domain) REFERENCES domains(name)
            )
        """)
        
        # 관계 테이블  
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id VARCHAR PRIMARY KEY,
                relation VARCHAR,
                from_entity VARCHAR,
                to_entity VARCHAR,
                via VARCHAR,
                description VARCHAR,
                cardinality VARCHAR,
                section VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 비즈니스 규칙 테이블
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS business_rules (
                id VARCHAR PRIMARY KEY,
                name VARCHAR,
                condition VARCHAR,
                action VARCHAR,
                priority VARCHAR,
                description VARCHAR,
                staff_alert_template VARCHAR,
                influencer_message_template VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. 테이블 매핑 정보
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS table_mappings (
                domain VARCHAR NOT NULL,
                concept_name VARCHAR NOT NULL,
                table_name VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (domain, concept_name)
            )
        """)
        
        logger.info("DuckDB 테이블 생성 완료")
    
    def load_all(self) -> bool:
        """모든 온톨로지 파일을 로드하고 DuckDB에 저장"""
        try:
            # 기존 데이터 삭제
            self._clear_all_data()
            
            # 새 데이터 로드
            self._load_domains()
            self._load_relations()
            self._load_business_rules()
            
            logger.info("온톨로지 DuckDB 로드 완료")
            return True
        except Exception as e:
            logger.error(f"온톨로지 DuckDB 로드 실패: {e}")
            return False
    
    def _clear_all_data(self):
        """모든 테이블 데이터 삭제"""
        self.conn.execute("DELETE FROM business_rules")
        self.conn.execute("DELETE FROM relations")
        self.conn.execute("DELETE FROM concepts")
        self.conn.execute("DELETE FROM domains")
        self.conn.execute("DELETE FROM table_mappings")
        logger.info("기존 데이터 삭제 완료")
    
    def _load_domains(self):
        """도메인 파일들 로드 및 저장"""
        domains_path = self.ontology_path / "domains"
        
        if not domains_path.exists():
            raise FileNotFoundError(f"도메인 경로를 찾을 수 없습니다: {domains_path}")
        
        domain_files = ["product.yaml", "marketing.yaml", "delivery.yaml"]
        
        for file_name in domain_files:
            file_path = domains_path / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    domain_data = yaml.safe_load(f)
                    domain_name = domain_data.get('domain', file_name.replace('.yaml', ''))
                    
                    # 도메인 저장
                    self.conn.execute("""
                        INSERT INTO domains (name, description, version, raw_data)
                        VALUES (?, ?, ?, ?)
                    """, (
                        domain_name,
                        domain_data.get('description', ''),
                        domain_data.get('version', '1.0.0'),
                        json.dumps(domain_data, ensure_ascii=False)
                    ))
                    
                    # 테이블 매핑 저장
                    table_mappings = domain_data.get('table_mapping', {})
                    for concept_name, table_name in table_mappings.items():
                        self.conn.execute("""
                            INSERT INTO table_mappings (domain, concept_name, table_name)
                            VALUES (?, ?, ?)
                        """, (domain_name, concept_name, table_name))
                    
                    # 개념들 저장
                    concepts = domain_data.get('concepts', {})
                    for concept_name, concept_data in concepts.items():
                        if isinstance(concept_data, dict):
                            properties = concept_data.get('properties', [])
                            
                            # properties 정규화
                            if isinstance(properties, dict):
                                properties = [f"{k}: {v}" for k, v in properties.items()]
                            elif isinstance(properties, list):
                                properties = [str(prop) if not isinstance(prop, str) else prop for prop in properties]
                            
                            concept_id = f"{domain_name}.{concept_name}"
                            self.conn.execute("""
                                INSERT INTO concepts (id, domain, name, description, properties)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                concept_id,
                                domain_name,
                                concept_name,
                                concept_data.get('description', ''),
                                json.dumps(properties, ensure_ascii=False)
                            ))
                    
                    logger.info(f"도메인 저장 완료: {domain_name} ({len(concepts)}개 개념)")
    
    def _load_relations(self):
        """관계 파일 로드 및 저장"""
        relations_path = self.ontology_path / "domains" / "_relations.yaml"
        
        if not relations_path.exists():
            logger.warning(f"관계 파일을 찾을 수 없습니다: {relations_path}")
            return
        
        with open(relations_path, 'r', encoding='utf-8') as f:
            relations_data = yaml.safe_load(f)
        
        relation_id = 1
        for section_name, section_data in relations_data.items():
            if section_name in ['version', 'description']:
                continue
            
            if isinstance(section_data, list):
                for relation_data in section_data:
                    if isinstance(relation_data, dict) and 'relation' in relation_data:
                        self.conn.execute("""
                            INSERT INTO relations (
                                id, relation, from_entity, to_entity, via,
                                description, cardinality, section
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            f"rel_{relation_id:03d}",
                            relation_data.get('relation', ''),
                            relation_data.get('from', ''),
                            relation_data.get('to', ''),
                            relation_data.get('via', ''),
                            relation_data.get('description', ''),
                            relation_data.get('cardinality', ''),
                            section_name
                        ))
                        relation_id += 1
        
        logger.info(f"관계 저장 완료: {relation_id-1}개")
    
    def _load_business_rules(self):
        """비즈니스 규칙 파일 로드 및 저장"""
        rules_path = self.ontology_path / "rules" / "business_rules.yaml"
        
        if not rules_path.exists():
            logger.warning(f"비즈니스 규칙 파일을 찾을 수 없습니다: {rules_path}")
            return
        
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules_data = yaml.safe_load(f)
        
        marketing_rules = rules_data.get('marketing_rules', [])
        for rule_data in marketing_rules:
            self.conn.execute("""
                INSERT INTO business_rules (
                    id, name, condition, action, priority, description,
                    staff_alert_template, influencer_message_template
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_data.get('id'),
                rule_data.get('name'),
                rule_data.get('condition'),
                rule_data.get('action'),
                rule_data.get('priority'),
                rule_data.get('description'),
                rule_data.get('staff_alert_template'),
                rule_data.get('influencer_message_template')
            ))
        
        logger.info(f"비즈니스 규칙 저장 완료: {len(marketing_rules)}개")
    
    def get_domain_concepts(self, domain_name: str) -> Dict[str, DomainConcept]:
        """특정 도메인의 개념들 조회"""
        result = self.conn.execute("""
            SELECT name, description, properties, domain
            FROM concepts
            WHERE domain = ?
        """, (domain_name,)).fetchall()
        
        concepts = {}
        for row in result:
            name, description, properties_json, domain = row
            properties = json.loads(properties_json) if properties_json else []
            
            concepts[name] = DomainConcept(
                name=name,
                description=description,
                properties=properties,
                domain=domain
            )
        
        return concepts
    
    def get_domain_relations(self, from_domain: str = None, to_domain: str = None) -> List[DomainRelation]:
        """도메인 간 관계 조회"""
        query = "SELECT relation, from_entity, to_entity, via, description, cardinality FROM relations"
        params = []
        
        conditions = []
        if from_domain:
            conditions.append("from_entity LIKE ?")
            params.append(f"{from_domain}.%")
        if to_domain:
            conditions.append("to_entity LIKE ?")
            params.append(f"{to_domain}.%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        result = self.conn.execute(query, params).fetchall()
        
        relations = []
        for row in result:
            relation, from_entity, to_entity, via, description, cardinality = row
            relations.append(DomainRelation(
                relation=relation,
                from_entity=from_entity,
                to_entity=to_entity,
                via=via,
                description=description,
                cardinality=cardinality
            ))
        
        return relations
    
    def get_business_rules(self, priority: str = None) -> List[BusinessRule]:
        """비즈니스 규칙 조회"""
        query = """
            SELECT id, name, condition, action, priority, description,
                   staff_alert_template, influencer_message_template
            FROM business_rules
        """
        params = []
        
        if priority:
            query += " WHERE priority = ?"
            params.append(priority)
        
        result = self.conn.execute(query, params).fetchall()
        
        rules = []
        for row in result:
            id, name, condition, action, priority, description, staff_alert, influencer_msg = row
            rules.append(BusinessRule(
                id=id,
                name=name,
                condition=condition,
                action=action,
                priority=priority,
                description=description,
                staff_alert_template=staff_alert,
                influencer_message_template=influencer_msg
            ))
        
        return rules
    
    def get_business_rule_by_id(self, rule_id: str) -> Optional[BusinessRule]:
        """ID로 특정 비즈니스 규칙 조회"""
        result = self.conn.execute("""
            SELECT id, name, condition, action, priority, description,
                   staff_alert_template, influencer_message_template
            FROM business_rules
            WHERE id = ?
        """, (rule_id,)).fetchone()
        
        if not result:
            return None
        
        id, name, condition, action, priority, description, staff_alert, influencer_msg = result
        return BusinessRule(
            id=id,
            name=name,
            condition=condition,
            action=action,
            priority=priority,
            description=description,
            staff_alert_template=staff_alert,
            influencer_message_template=influencer_msg
        )
    
    def get_all_domains(self) -> List[str]:
        """모든 도메인 이름 조회"""
        result = self.conn.execute("SELECT name FROM domains").fetchall()
        return [row[0] for row in result]
    
    def get_domain_summary(self) -> Dict[str, Any]:
        """온톨로지 전체 요약 정보"""
        # 도메인별 개념 수
        domain_stats = self.conn.execute("""
            SELECT d.name, COUNT(c.id) as concept_count
            FROM domains d
            LEFT JOIN concepts c ON d.name = c.domain
            GROUP BY d.name
        """).fetchall()
        
        # 전체 통계
        total_relations = self.conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
        total_rules = self.conn.execute("SELECT COUNT(*) FROM business_rules").fetchone()[0]
        
        # 우선순위별 규칙 수
        priority_stats = self.conn.execute("""
            SELECT priority, COUNT(*) 
            FROM business_rules 
            GROUP BY priority
        """).fetchall()
        
        return {
            "domains": {name: {"concept_count": count} for name, count in domain_stats},
            "total_relations": total_relations,
            "total_business_rules": total_rules,
            "relations_by_priority": {priority: count for priority, count in priority_stats}
        }
    
    def search_concepts(self, query: str, domain: str = None) -> Dict[str, List[str]]:
        """개념 검색"""
        sql = """
            SELECT domain, name
            FROM concepts
            WHERE LOWER(name) LIKE ?
        """
        params = [f"%{query.lower()}%"]
        
        if domain:
            sql += " AND domain = ?"
            params.append(domain)
        
        result = self.conn.execute(sql, params).fetchall()
        
        results = {}
        for domain_name, concept_name in result:
            if domain_name not in results:
                results[domain_name] = []
            results[domain_name].append(concept_name)
        
        return results
    
    def execute_custom_query(self, query: str, params: List = None) -> List[tuple]:
        """커스텀 SQL 쿼리 실행"""
        if params is None:
            params = []
        return self.conn.execute(query, params).fetchall()
    
    def get_table_mappings(self, domain: str = None) -> Dict[str, str]:
        """테이블 매핑 정보 조회 (concept_name -> table_name)"""
        query = "SELECT concept_name, table_name FROM table_mappings"
        params = []
        
        if domain:
            query += " WHERE domain = ?"
            params.append(domain)
        
        results = self.conn.execute(query, params).fetchall()
        return {row[0]: row[1] for row in results}
    
    def get_all_table_mappings(self) -> Dict[str, Dict[str, str]]:
        """모든 도메인의 테이블 매핑 정보 조회"""
        query = "SELECT domain, concept_name, table_name FROM table_mappings"
        results = self.conn.execute(query).fetchall()
        
        mappings = {}
        for domain, concept_name, table_name in results:
            if domain not in mappings:
                mappings[domain] = {}
            mappings[domain][concept_name] = table_name
        
        return mappings

    def close(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB 연결 종료")


# 전역 DuckDB 인스턴스
ontology_db = OntologyDuckDB()
