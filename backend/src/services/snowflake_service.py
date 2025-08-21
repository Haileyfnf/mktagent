"""
Snowflake 데이터베이스 연결 및 쿼리 서비스
F&F 인플루언서 마케팅 실제 데이터 소스 연동
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import snowflake.connector
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
from loguru import logger
from pydantic import BaseModel


class SnowflakeConfig(BaseModel):
    """Snowflake 연결 설정"""
    account: str
    user: str
    password: str
    warehouse: str
    database: str
    schema_name: str  # 'schema' 대신 'schema_name' 사용
    role: Optional[str] = None


class SnowflakeService:
    """Snowflake 데이터베이스 서비스"""
    
    def __init__(self, config: SnowflakeConfig = None):
        """
        Snowflake 서비스 초기화
        
        Args:
            config: Snowflake 연결 설정
        """
        self.config = config or self._load_config_from_env()
        self.engine = None
        self.session = None
        
        logger.info(f"Snowflake 서비스 초기화 - {self.config.account}/{self.config.database}")
    
    def _load_config_from_env(self) -> SnowflakeConfig:
        """환경변수에서 Snowflake 설정 로드 (.env 파일에서 미리 로드되어야 함)"""
        return SnowflakeConfig(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema_name=os.getenv("SNOWFLAKE_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE")
        )
    
    def connect(self) -> bool:
        """Snowflake 연결"""
        try:
            # 디버깅: config 값 확인
            logger.info(f"Snowflake Config 확인:")
            logger.info(f"  account: {self.config.account}")
            logger.info(f"  user: {self.config.user}")
            logger.info(f"  warehouse: {self.config.warehouse}")
            logger.info(f"  database: {self.config.database}")
            logger.info(f"  schema: {self.config.schema_name}")
            
            # SQLAlchemy 엔진 생성
            connection_string = (
                f"snowflake://{self.config.user}:{self.config.password}@"
                f"{self.config.account}/{self.config.database}/{self.config.schema_name}"
                f"?warehouse={self.config.warehouse}"
            )
            
            if self.config.role:
                connection_string += f"&role={self.config.role}"
            
            logger.info(f"연결 문자열 (비밀번호 제외): snowflake://{self.config.user}:***@{self.config.account}/{self.config.database}/{self.config.schema_name}?warehouse={self.config.warehouse}")
            
            self.engine = create_engine(connection_string)
            
            # 연결 테스트
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT CURRENT_VERSION()"))
                version = result.fetchone()[0]
                logger.info(f"Snowflake 연결 성공 - 버전: {version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Snowflake 연결 실패: {e}")
            return False
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """SQL 쿼리 실행 (READ-ONLY 권한으로 안전)"""
        try:
            if not self.engine:
                if not self.connect():
                    raise Exception("Snowflake 연결이 필요합니다")
            
            logger.info(f"쿼리 실행: {query[:100]}...")
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                
                # 결과를 딕셔너리 리스트로 변환
                columns = result.keys()
                rows = result.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"쿼리 실행 실패: {e}")
            raise
    
    def get_delivery_entries(self, 
                           status: Optional[str] = None,
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Dict]:
        """배송 정보 조회"""
        
        query = """
        SELECT 
            id,
            create_dt,
            delivery_confirm_dt,
            delivery_req_dt,
            entry_code,
            color,
            size,
            order_detail_number,
            order_number,
            price,
            price_total,
            qty,
            qty_confirmed,
            status,
            tracking_number,
            tracking_status,
            request_status,
            brand_id,
            campaign_influencer_id,
            delivery_id,
            influencer_id,
            categorized_item_id
        FROM delivery_entry
        WHERE 1=1
        """
        
        params = {}
        
        if status:
            query += " AND status = :status"
            params["status"] = status
        
        if date_from:
            query += " AND create_dt >= :date_from"
            params["date_from"] = date_from
        
        if date_to:
            query += " AND create_dt <= :date_to" 
            params["date_to"] = date_to
        
        query += " ORDER BY create_dt DESC"
        
        return self.execute_query(query, params)
    
    def get_campaign_influencers(self,
                               campaign_id: Optional[str] = None,
                               status: Optional[str] = None) -> List[Dict]:
        """캠페인 인플루언서 정보 조회"""
        
        query = """
        SELECT 
            id,
            cast_msg_dt,
            cast_res_date,
            cast_status,
            contents_post_dt,
            delivery_dt,
            invitation_status,
            progress,
            brand_id,
            campaign_id,
            channel_account_id,
            influencer_id,
            rep_contents_id
        FROM campaign_influencer
        WHERE 1=1
        """
        
        params = {}
        
        if campaign_id:
            query += " AND campaign_id = :campaign_id"
            params["campaign_id"] = campaign_id
        
        if status:
            query += " AND cast_status = :status"
            params["status"] = status
        
        query += " ORDER BY cast_msg_dt DESC"
        
        return self.execute_query(query, params)
    
    def get_campaigns(self,
                     active_only: bool = False,
                     brand_id: Optional[str] = None) -> List[Dict]:
        """캠페인 정보 조회"""
        
        query = """
        SELECT 
            id,
            camp_code,
            camp_nm,
            start_date,
            end_date,
            status,
            target_cnt,
            brand_id,
            channel_id,
            engmt_avg,
            engmt_cnt,
            part_cds,
            campaign_hashtags,
            prdt_kind_nms
        FROM campaign
        WHERE 1=1
        """
        
        params = {}
        
        if active_only:
            query += " AND status != 'COMPLETE' AND end_date >= CURRENT_DATE()"
        
        if brand_id:
            query += " AND brand_id = :brand_id"
            params["brand_id"] = brand_id
        
        query += " ORDER BY start_date DESC"
        
        return self.execute_query(query, params)
    
    def get_products(self,
                    brand_cd: Optional[str] = None,
                    category: Optional[str] = None) -> List[Dict]:
        """제품 정보 조회"""
        
        query = """
        SELECT 
            id,
            part_cd,
            prdt_nm,
            brd_cd,
            brd_nm,
            sesn,
            cat,
            cat_nm,
            sub_cat_nm,
            item,
            item_nm,
            prdt_kind_cd,
            prdt_kind_nm,
            domain1,
            domain1_name,
            tag_price,
            unit_price,
            prdt_image,
            create_dt
        FROM categorized_item
        WHERE 1=1
        """
        
        params = {}
        
        if brand_cd:
            query += " AND brd_cd = :brand_cd"
            params["brand_cd"] = brand_cd
        
        if category:
            query += " AND cat_nm = :category"
            params["category"] = category
        
        query += " ORDER BY create_dt DESC"
        
        return self.execute_query(query, params)
    
    def get_brands(self) -> List[Dict]:
        """브랜드 정보 조회"""
        
        query = """
        SELECT 
            id,
            brand_nm
        FROM FNF.INFLUENCER.BRAND
        ORDER BY brand_nm
        """
        
        return self.execute_query(query)
    
    def get_contents(self,
                    campaign_id: Optional[str] = None,
                    influencer_id: Optional[str] = None) -> List[Dict]:
        """컨텐츠 정보 조회 (향후 구현용)"""
        
        # 실제 컨텐츠 테이블 구조에 맞게 수정 필요
        query = """
        SELECT 
            id,
            campaign_id,
            influencer_id,
            content_url,
            hashtags,
            post_date,
            engagement_count,
            like_count,
            comment_count,
            share_count
        FROM content
        WHERE 1=1
        """
        
        params = {}
        
        if campaign_id:
            query += " AND campaign_id = :campaign_id"
            params["campaign_id"] = campaign_id
        
        if influencer_id:
            query += " AND influencer_id = :influencer_id"
            params["influencer_id"] = influencer_id
        
        query += " ORDER BY post_date DESC"
        
        return self.execute_query(query, params)
    
    def get_rule_context_data(self, 
                            days_back: int = 30) -> Dict[str, List[Dict]]:
        """룰 엔진용 종합 데이터 조회"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            # 병렬로 모든 데이터 조회
            delivery_entries = self.get_delivery_entries(date_from=cutoff_date)
            campaign_influencers = self.get_campaign_influencers()
            campaigns = self.get_campaigns(active_only=True)
            contents = self.get_contents()
            
            logger.info(f"룰 컨텍스트 데이터 조회 완료 - "
                       f"배송: {len(delivery_entries)}, "
                       f"캠페인 인플루언서: {len(campaign_influencers)}, "
                       f"캠페인: {len(campaigns)}, "
                       f"컨텐츠: {len(contents)}")
            
            return {
                "delivery_entries": delivery_entries,
                "campaign_influencers": campaign_influencers,
                "campaigns": campaigns,
                "contents": contents
            }
            
        except Exception as e:
            logger.error(f"룰 컨텍스트 데이터 조회 실패: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """연결 테스트"""
        try:
            if not self.connect():
                return {"status": "failed", "error": "연결 실패"}
            
            # 각 테이블 레코드 수 확인
            tables = ["delivery_entry", "campaign_influencer", "campaign", "categorized_item"]
            table_counts = {}
            
            for table in tables:
                try:
                    result = self.execute_query(f"SELECT COUNT(*) as cnt FROM {table}")
                    table_counts[table] = result[0]["CNT"] if result else 0
                except:
                    table_counts[table] = "접근 불가"
            
            return {
                "status": "success",
                "database": f"{self.config.database}.{self.config.schema_name}",
                "warehouse": self.config.warehouse,
                "table_counts": table_counts
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def close(self):
        """연결 종료"""
        if self.engine:
            self.engine.dispose()
            logger.info("Snowflake 연결 종료")


# 전역 Snowflake 서비스 인스턴스 (lazy loading)
snowflake_service = None

def get_snowflake_service():
    """Snowflake 서비스 인스턴스를 lazy loading으로 반환"""
    global snowflake_service
    if snowflake_service is None:
        snowflake_service = SnowflakeService()
    return snowflake_service
