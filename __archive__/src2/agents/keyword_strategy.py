# 키워드별 검색 전략 정의

KEYWORD_STRATEGIES = {
    "MLB": {
        "search_terms": [
            "MLB 패션",
            "MLB 의류", 
            "MLB 브랜드",
            "MLB 쇼핑",
            "MLB 스타일",
            "MLB 컬렉션"
        ],
        "exclude_terms": [
            "야구", "baseball", "투수", "타자", "홈런", "구단", "감독", "코치",
            "pitcher", "batter", "hitter", "home run", "team", "manager", "coach"
        ]
    },
    "F&F": {
        "search_terms": [
            "F&F 패션",
            "F&F 의류",
            "F&F 브랜드",
            "F&F 쇼핑"
        ],
        "exclude_terms": []
    },
    "디스커버리 익스페디션": {
        "search_terms": [
            "디스커버리 익스페디션",
            "디스커버리 패션",
            "디스커버리 의류"
        ],
        "exclude_terms": []
    },
    "엠엘비": {
        "search_terms": [
            "엠엘비 패션",
            "엠엘비 의류",
            "엠엘비 브랜드"
        ],
        "exclude_terms": [
            "야구", "baseball", "투수", "타자"
        ]
    }
}

def get_search_query(keyword):
    """키워드에 따른 검색 쿼리 생성"""
    if keyword in KEYWORD_STRATEGIES:
        strategy = KEYWORD_STRATEGIES[keyword]
        search_terms = strategy["search_terms"]
        exclude_terms = strategy["exclude_terms"]
        
        # 검색어 조합
        query = " OR ".join(search_terms)
        
        # 제외할 키워드 추가
        if exclude_terms:
            exclude_part = " ".join([f"-{term}" for term in exclude_terms])
            query = f"({query}) {exclude_part}"
        
        return query
    else:
        return keyword

def get_exclude_terms(keyword):
    """키워드에 따른 제외할 키워드 반환"""
    if keyword in KEYWORD_STRATEGIES:
        return KEYWORD_STRATEGIES[keyword]["exclude_terms"]
    return [] 