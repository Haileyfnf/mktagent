"""
캠페인 컨텐츠 프리뷰 서비스
- 최신 업로드된 컨텐츠 조회
- 인게이지먼트 데이터 통합
- 실시간 성과 집계
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

from .snowflake_service import get_snowflake_service
from .ontology_duckdb import ontology_db
from .image_service import image_service


class ContentPreviewService:
    """캠페인 컨텐츠 프리뷰 서비스"""

    def get_latest_contents(
        self,
        hours_back: int = 24,
        limit: int = 10,
        brand_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """최신 업로드된 컨텐츠 조회
        
        Args:
            hours_back (int): 몇 시간 전까지 조회할지 (기본 24시간)
            limit (int): 최대 몇 개의 컨텐츠를 가져올지 (기본 10개)
            brand_id (Optional[str]): 특정 브랜드만 조회할 경우
        """
        try:
            # 컨텐츠 기본 정보 조회 쿼리
            base_query = """
            WITH ranked_contents AS (
                SELECT 
                    ci.id as campaign_influencer_id,
                    ci.contents_post_dt,
                    ci.influencer_id,
                    ci.campaign_id,
                    c.camp_nm,
                    c.brand_id,
                    c.campaign_hashtags,
                    i.channel_name,
                    i.follower_count,
                    co.content_url,
                    co.thumbnail_url,
                    co.likes_count,
                    co.comments_count,
                    co.views_count,
                    ROUND(
                        (COALESCE(co.likes_count, 0) + COALESCE(co.comments_count, 0) * 3) / 
                        NULLIF(i.follower_count, 0) * 100, 
                        2
                    ) as engagement_rate,
                    ROW_NUMBER() OVER (
                        PARTITION BY ci.campaign_id 
                        ORDER BY ci.contents_post_dt DESC
                    ) as content_rank
                FROM campaign_influencer ci
                JOIN campaign c ON ci.campaign_id = c.id
                JOIN influencer i ON ci.influencer_id = i.id
                LEFT JOIN content co ON ci.rep_contents_id = co.id
                WHERE ci.contents_post_dt >= :cutoff_time
                AND ci.contents_post_dt IS NOT NULL
                {brand_filter}
            )
            SELECT *
            FROM ranked_contents
            WHERE content_rank = 1  -- 각 캠페인당 최신 컨텐츠만
            ORDER BY contents_post_dt DESC
            LIMIT :limit
            """

            # 브랜드 필터 추가
            brand_filter = "AND c.brand_id = :brand_id" if brand_id else ""
            query = base_query.format(brand_filter=brand_filter)

            # 쿼리 파라미터
            params = {
                "cutoff_time": (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d %H:%M:%S'),
                "limit": limit
            }
            if brand_id:
                params["brand_id"] = brand_id

            # 쿼리 실행
            contents = get_snowflake_service().execute_query(query, params)

            # 컨텐츠별 추가 정보 조회
            enriched_contents = []
            for content in contents:
                # 해시태그 파싱
                hashtags = content.get('campaign_hashtags', '').split(',') if content.get('campaign_hashtags') else []
                
                # 성과 통계
                stats = self._calculate_content_stats(content)
                
                # 브랜드 정보
                brand_info = self._get_brand_info(content.get('brand_id'))

                # 이미지 URL 처리
                content_url = content.get('content_url')
                thumbnail_url = content.get('thumbnail_url')
                
                # 이미지 URL 검증
                content_url = image_service.get_image_url(content_url)
                thumbnail_url = image_service.get_image_url(thumbnail_url)
                
                # 이미지 메타데이터 조회 (메인 이미지만)
                image_metadata = image_service.get_image_metadata(content_url) if content_url else {}

                enriched_contents.append({
                    "content_id": content.get('campaign_influencer_id'),
                    "posted_at": content.get('contents_post_dt'),
                    "campaign": {
                        "id": content.get('campaign_id'),
                        "name": content.get('camp_nm'),
                        "brand": brand_info
                    },
                    "influencer": {
                        "id": content.get('influencer_id'),
                        "channel_name": content.get('channel_name'),
                        "follower_count": content.get('follower_count')
                    },
                    "content": {
                        "url": content_url,
                        "thumbnail_url": thumbnail_url,
                        "hashtags": hashtags,
                        "metadata": {
                            "content_type": image_metadata.get('content_type', ''),
                            "size": image_metadata.get('content_length', 0),
                            "last_modified": image_metadata.get('last_modified', ''),
                            "additional": image_metadata.get('metadata', {})
                        }
                    },
                    "stats": stats,
                    "engagement": {
                        "rate": content.get('engagement_rate', 0),
                        "likes": content.get('likes_count', 0),
                        "comments": content.get('comments_count', 0),
                        "views": content.get('views_count', 0)
                    }
                })

            return enriched_contents

        except Exception as e:
            logger.error(f"최신 컨텐츠 조회 실패: {e}")
            return []

    def _calculate_content_stats(self, content: Dict) -> Dict[str, Any]:
        """컨텐츠 성과 통계 계산"""
        try:
            # 평균 대비 성과 계산
            avg_query = """
            SELECT 
                AVG(likes_count) as avg_likes,
                AVG(comments_count) as avg_comments,
                AVG(views_count) as avg_views,
                AVG(
                    (COALESCE(likes_count, 0) + COALESCE(comments_count, 0) * 3) / 
                    NULLIF(i.follower_count, 0) * 100
                ) as avg_engagement
            FROM content co
            JOIN campaign_influencer ci ON co.id = ci.rep_contents_id
            JOIN influencer i ON ci.influencer_id = i.id
            JOIN campaign c ON ci.campaign_id = c.id
            WHERE c.brand_id = :brand_id
            AND co.created_at >= DATEADD(month, -1, CURRENT_TIMESTAMP())
            """
            
            avg_stats = get_snowflake_service().execute_query(
                avg_query, 
                {"brand_id": content.get('brand_id')}
            )[0]

            current_likes = content.get('likes_count', 0)
            current_comments = content.get('comments_count', 0)
            current_views = content.get('views_count', 0)
            current_engagement = content.get('engagement_rate', 0)

            return {
                "likes_vs_avg": round((current_likes / avg_stats['avg_likes'] - 1) * 100, 1) if avg_stats['avg_likes'] else 0,
                "comments_vs_avg": round((current_comments / avg_stats['avg_comments'] - 1) * 100, 1) if avg_stats['avg_comments'] else 0,
                "views_vs_avg": round((current_views / avg_stats['avg_views'] - 1) * 100, 1) if avg_stats['avg_views'] else 0,
                "engagement_vs_avg": round((current_engagement / avg_stats['avg_engagement'] - 1) * 100, 1) if avg_stats['avg_engagement'] else 0
            }

        except Exception as e:
            logger.error(f"컨텐츠 통계 계산 실패: {e}")
            return {
                "likes_vs_avg": 0,
                "comments_vs_avg": 0,
                "views_vs_avg": 0,
                "engagement_vs_avg": 0
            }

    def _get_brand_info(self, brand_id: str) -> Dict[str, Any]:
        """브랜드 정보 조회"""
        try:
            brand_query = "SELECT * FROM brand WHERE id = :brand_id"
            brands = get_snowflake_service().execute_query(brand_query, {"brand_id": brand_id})
            
            if brands:
                brand = brands[0]
                return {
                    "id": brand_id,
                    "name": brand.get('brand_nm', ''),
                    "code": brand.get('brand_cd', '')
                }
            return {"id": brand_id, "name": "", "code": ""}

        except Exception as e:
            logger.error(f"브랜드 정보 조회 실패: {e}")
            return {"id": brand_id, "name": "", "code": ""}


# 전역 서비스 인스턴스
content_preview_service = ContentPreviewService()
