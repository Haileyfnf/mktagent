# MKT AI Agent

마케팅 AI 에이전트 시스템 - 뉴스 모니터링 및 키워드 분석

## 🚀 주요 기능

### 1. 뉴스 수집 및 모니터링
- 네이버 뉴스 API를 통한 실시간 뉴스 수집
- 키워드별 자동 뉴스 모니터링
- **스마트 필터링 시스템** - 관련성 높은 기사만 선별

### 2. 스마트 필터링 시스템 ✨ NEW!

API 통신을 최적화하고 원하는 내용만 정확히 수집하는 필터링 시스템을 추가했습니다.

#### 주요 특징:
- **제목 기반 필터링**: 제목만으로 빠른 필터링하여 API 호출 최적화
- **키워드별 맞춤 필터**: 각 키워드마다 제외 키워드 설정으로 원하지 않는 내용 필터링
- **중복 검사 강화**: 제목 기반 빠른 중복 검사로 불필요한 API 호출 방지
- **효율적인 처리**: 제목에서 필터링된 기사는 내용 추출을 건너뛰어 API 호출 절약

#### 예시: MLB 키워드 필터링
```python
# MLB 키워드 설정
KEYWORD_FILTERS = {
    "MLB": {
        "exclude_keywords": ["야구", "베이스볼", "메이저리그", "투수", "타자", "홈런", "안타", "볼넷", "삼진", "경기", "시즌", "팀", "선수", "구단", "리그", "월드시리즈"],
        "required_keywords": ["MLB"],
        "description": "패션 브랜드 MLB 관련 기사만 수집 (야구 관련 제외)"
    }
}
```

#### API 엔드포인트:
- `GET /news/filter_config` - 필터 설정 조회
- `POST /news/filter_config` - 필터 설정 업데이트
- `POST /news/test_filter` - 필터 테스트
- `GET /news/optimized_search` - 최적화된 검색
- `POST /news/fetch_and_save` - 필터링 적용 뉴스 수집
- `POST /news/search_all_pages` - 페이지 끝까지 모든 기사 검색 및 저장

### 3. 데이터베이스 관리
- SQLite 기반 데이터 저장
- 키워드별 기사 분류 및 저장
- 중복 기사 자동 필터링

### 4. 웹 인터페이스
- React 기반 프론트엔드
- 실시간 뉴스 모니터링 대시보드
- 키워드 관리 및 설정

## 🛠️ 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
DB_PATH=backend/src/database/db.sqlite
```

### 3. 데이터베이스 초기화
```bash
cd backend/src/database
python init_db.py
```

### 4. 백엔드 실행
```bash
cd backend
python run.py
```

### 5. 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

## 📊 필터링 시스템 사용법

### 1. 기본 사용
```python
# 필터링 적용하여 뉴스 수집
POST /news/fetch_and_save
{
    "keyword": "MLB",
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "use_filter": true  # 필터 사용 (기본값)
}
```

### 2. 필터 설정 확인
```python
GET /news/filter_config
```

### 3. 필터 테스트
```python
POST /news/test_filter
{
    "keyword": "MLB",
    "title": "MLB 패션 브랜드 신상품 출시",
    "content": "MLB 패션 브랜드가 새로운 캡 컬렉션을 출시했다..."
}
```

### 4. 최적화된 검색
```python
GET /news/optimized_search?keyword=MLB&display=10&use_optimized_query=true
```

### 5. 페이지 끝까지 검색
```python
POST /news/search_all_pages
{
    "keyword": "MLB",
    "start_date": "2025-07-05",
    "end_date": "2025-07-07",
    "use_filter": true
}
```

### 6. 제목 기반 필터링 시스템 사용 예시
```python
# API 응답 예시
{
    "message": "3건 저장 완료",
    "total": 20,
    "saved": 3,
    "skipped": 2,
    "title_filtered": 15,        # 제목에서 필터링된 기사 수
    "api_calls_saved": 15,       # 절약된 API 호출 수
    "optimization_info": {
        "total_articles": 20,
        "title_filtered": 15,
        "content_extracted": 5,  # 실제 내용을 추출한 기사 수
        "api_calls_saved": 15,
        "efficiency_rate": "75.0%"  # API 호출 절약률
    }
}
```

## 🧪 테스트

### 필터링 시스템 테스트
```bash
cd backend/tests
python test_filter_system.py
```

### 전체 시스템 테스트
```bash
cd backend/src/api
python naver_news_api.py
```

## 📈 성능 최적화

### API 호출 최적화
- **스마트 쿼리**: 키워드 + 관련 키워드 조합으로 검색 정확도 향상
- **중복 검사**: 제목 기반 빠른 중복 검사로 불필요한 API 호출 방지
- **배치 처리**: 여러 키워드를 효율적으로 처리

### 필터링 성능
- **실시간 필터링**: 기사 내용 분석으로 관련성 즉시 판단
- **키워드 매칭**: 포함/제외 키워드 기반 정확한 분류
- **메모리 효율성**: 대용량 데이터 처리 최적화

## 🔧 설정 및 커스터마이징

### 새로운 키워드 필터 추가
```python
KEYWORD_FILTERS["새로운키워드"] = {
    "exclude_keywords": ["제외할_키워드1", "제외할_키워드2"],
    "required_keywords": ["반드시_포함되어야_할_키워드"],
    "description": "필터 설명"
}
```

### 필터 설정 동적 업데이트
```python
POST /news/filter_config
{
    "keyword": "새로운키워드",
    "filter_config": {
        "exclude_keywords": ["스포츠", "야구", "축구"],
        "required_keywords": ["새로운키워드"],
        "description": "새로운 필터 설정"
    }
}
```

## 📝 라이센스

MIT License

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
