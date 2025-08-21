import os
from dotenv import load_dotenv

def test_env_loading():
    """환경변수 로딩 테스트"""
    print("=== .env 파일 로딩 테스트 ===")
    
    # .env 파일 로드
    load_dotenv()
    
    # OpenAI API 키 확인
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"OpenAI API Key: {openai_key[:10] + '...' if openai_key and len(openai_key) > 10 else 'Not set'}")
    
    # 네이버 API 키 확인
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
    print(f"Naver Client ID: {naver_client_id}")
    print(f"Naver Client Secret: {naver_client_secret[:5] + '...' if naver_client_secret else 'Not set'}")
    
    if not openai_key or openai_key == "your-openai-api-key-here":
        print("\n⚠️  경고: OpenAI API 키가 설정되지 않았습니다.")
        print("   .env 파일에서 OPENAI_API_KEY를 실제 API 키로 변경해주세요.")
    else:
        print("\n✅ OpenAI API 키가 정상적으로 설정되었습니다.")

if __name__ == "__main__":
    test_env_loading() 