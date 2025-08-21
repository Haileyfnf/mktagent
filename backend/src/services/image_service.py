"""
이미지 URL 처리 서비스
- 이미지 URL 검증 및 변환
- 이미지 메타데이터 추출
"""
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests
from loguru import logger


class ImageService:
    """이미지 URL 처리 서비스"""
    
    def get_image_url(self, url: Optional[str]) -> Optional[str]:
        """이미지 URL 검증 및 변환
        
        Args:
            url (Optional[str]): 원본 이미지 URL
            
        Returns:
            Optional[str]: 검증된 이미지 URL
        """
        if not url:
            return None
            
        try:
            # URL 유효성 검사
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None
                
            # HEAD 요청으로 이미지 존재 여부 및 타입 확인
            response = requests.head(url, timeout=5)
            if response.status_code != 200:
                return None
                
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
                
            return url
            
        except Exception as e:
            logger.warning(f"이미지 URL 검증 실패 ({url}): {e}")
            return None

    def get_image_metadata(self, url: Optional[str]) -> Dict[str, Any]:
        """이미지 메타데이터 조회
        
        Args:
            url (Optional[str]): 이미지 URL
            
        Returns:
            Dict[str, Any]: 이미지 메타데이터
        """
        if not url:
            return {}
            
        try:
            # HEAD 요청으로 메타데이터 조회
            response = requests.head(url, timeout=5)
            if response.status_code != 200:
                return {}
                
            return {
                "content_type": response.headers.get('content-type', ''),
                "content_length": int(response.headers.get('content-length', 0)),
                "last_modified": response.headers.get('last-modified', ''),
                "etag": response.headers.get('etag', '').strip('"')
            }
            
        except Exception as e:
            logger.warning(f"이미지 메타데이터 조회 실패 ({url}): {e}")
            return {}

    def check_image_exists(self, url: Optional[str]) -> bool:
        """이미지 존재 여부 확인
        
        Args:
            url (Optional[str]): 이미지 URL
            
        Returns:
            bool: 이미지 존재 여부
        """
        if not url:
            return False
            
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200 and response.headers.get('content-type', '').startswith('image/')
        except Exception as e:
            logger.warning(f"이미지 존재 여부 확인 실패 ({url}): {e}")
            return False


# 전역 서비스 인스턴스
image_service = ImageService()
