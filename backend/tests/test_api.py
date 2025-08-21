import requests
import urllib.parse
import json

# 네이버 개발자센터에서 발급받은 Client ID/Secret
CLIENT_ID = 'O91Y7OVgSkaSFIcGCtlC'
CLIENT_SECRET = 'N7tGh3ZuvD'

def test_naver_api():
    print("=== 네이버 검색 API 테스트 ===")
    
    # 테스트 키워드
    test_keyword = "삼성전자"
    query = urllib.parse.quote(test_keyword)
    
    # API URL
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&start=1&sort=date"
    
    # 헤더 설정
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    
    print(f"요청 URL: {url}")
    print(f"헤더: {headers}")
    print("-" * 50)
    
    try:
        # API 호출
        response = requests.get(url, headers=headers)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 호출 성공!")
            print(f"총 결과 수: {data.get('total', 'N/A')}")
            print(f"표시된 결과 수: {data.get('display', 'N/A')}")
            print(f"시작 위치: {data.get('start', 'N/A')}")
            print("-" * 50)
            
            # 결과 출력
            items = data.get('items', [])
            print(f"검색된 기사 수: {len(items)}")
            
            for i, item in enumerate(items, 1):
                print(f"\n{i}. 기사 정보:")
                print(f"   제목: {item.get('title', 'N/A')}")
                print(f"   링크: {item.get('link', 'N/A')}")
                print(f"   언론사: {item.get('originallink', 'N/A')}")
                print(f"   발행일: {item.get('pubDate', 'N/A')}")
                print(f"   요약: {item.get('description', 'N/A')[:100]}...")
                
        else:
            print("❌ API 호출 실패!")
            print(f"에러 응답: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 중 오류 발생: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

def test_api_quota():
    """API 할당량 확인"""
    print("\n=== API 할당량 확인 ===")
    
    # 간단한 검색으로 할당량 확인
    test_keyword = "테스트"
    query = urllib.parse.quote(test_keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=1&start=1"
    
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        # 응답 헤더에서 할당량 정보 확인
        quota_headers = {
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
            'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
        }
        
        print(f"할당량 정보: {quota_headers}")
        
        if response.status_code == 429:
            print("⚠️ API 할당량 초과!")
        elif response.status_code == 200:
            print("✅ API 할당량 정상")
            
    except Exception as e:
        print(f"할당량 확인 중 오류: {e}")

if __name__ == "__main__":
    test_naver_api()
    test_api_quota() 