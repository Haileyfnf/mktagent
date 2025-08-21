#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MLB 야구 관련 기사 자동 분류 스크립트
2025년 7월 MLB 관련 기사 중 야구 관련 기사들을 '해당없음'으로 분류합니다.
"""

import sqlite3
import re
from datetime import datetime

# 야구 관련 키워드 목록
BASEBALL_KEYWORDS = [
    # 선수 관련
    '이정후', '김하성', '김혜성', '오타니', '류현진', '최지만', '추신수', '박찬호',
    '타자', '투수', '포수', '내야수', '외야수', '지명타자', '마무리', '선발', '불펜',
    
    # 야구 용어
    '이닝', '타석', '타율', '방어율', '홈런', '안타', '삼진', '볼넷', '도루', '타점',
    'RBI', 'ERA', 'OPS', '승리', '패배', '세이브', '블론세이브', '완봉', '완투',
    '더블헤더', '연장', '콜드게임', '우천취소',
    
    # 팀명
    '다저스', '양키스', '레드삭스', '자이언츠', '애스트로스', '브루어스', '패드리스',
    '엔젤스', '메츠', '필리스', '브레이브스', '컵스', '화이트삭스', '오리올스',
    '레인저스', '마리너스', '레이스', '타이거스', '로열스', '트윈스', '가디언스',
    '애슬레틱스', '내셔널스', '말린스', '파이리츠', '레즈', '카디널스', '록키스',
    '디백스', '탬파베이',
    
    # 리그/대회
    'MLB', 'KBO', '메이저리그', '아메리칸리그', '내셔널리그', '월드시리즈',
    '플레이오프', '포스트시즌', '올스타', '스프링캠프', 'WBC', '프리미어12',
    
    # 구장/시설
    '구장', '스타디움', '마운드', '홈플레이트', '베이스', '덕아웃', '불펜',
    
    # 기타 야구 관련
    '시즌', '트레이드', '웨이버', 'DL', 'IL', '부상자명단', '마이너리그',
    '메이저리그', '콜업', '옵션', '논텐더', 'FA', '자유계약', '재계약',
    '구원', '세팅', '클로저', '좌완', '우완', '언더핸드', '사이드암'
]

def contains_baseball_keywords(title, content=''):
    """제목이나 내용에 야구 관련 키워드가 포함되어 있는지 확인"""
    text = (title + ' ' + content).lower()
    
    for keyword in BASEBALL_KEYWORDS:
        if keyword.lower() in text:
            return True, keyword
    
    # 정규식으로 추가 패턴 검사
    patterns = [
        r'\d+회(?:\s*)?(?:초|말)',  # "5회초", "9회말" 등
        r'\d+[-\d]*(?:\s*)?승(?:\s*)?(?:\d+[-\d]*)?패',  # "10승5패" 등
        r'\d+[-\d]*(?:\s*)?패(?:\s*)?(?:\d+[-\d]*)?승',  # "5패10승" 등
        r'(?:선발|마무리|세팅|중간)(?:\s*)?(?:투수|등판)',
        r'(?:1|2|3|홈)(?:\s*)?루(?:타|수|베이스)',
        r'(?:우|좌)(?:\s*)?(?:타|투)',
        r'\d+(?:\s*)?(?:타수|안타|홈런|타점|득점)',
        r'(?:승|패|무)(?:\s*)?(?:투수|기록)',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True, f"패턴매칭: {pattern}"
    
    return False, None

def classify_mlb_baseball_articles():
    """MLB 야구 관련 기사들을 '해당없음'으로 분류"""
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    try:
        # 2025년 7월 MLB 관련 미분류 기사 조회
        cursor.execute('''
            SELECT a.id, a.url, a.title, a.keyword, a.pub_date, a.group_name
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE (a.group_name LIKE "%MLB%" OR a.group_name LIKE "%엠엘비%")
            AND DATE(a.pub_date) LIKE "2025-07-%"
            AND cl.url IS NULL
        ''')
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        baseball_articles = []
        
        print(f"📊 총 {total_articles}개의 미분류 MLB 기사를 검사합니다...")
        print("-" * 60)
        
        # 각 기사별로 야구 관련 키워드 검사
        for article in articles:
            article_id, url, title, keyword, pub_date, group_name = article
            
            is_baseball, matched_keyword = contains_baseball_keywords(title)
            
            if is_baseball:
                baseball_articles.append({
                    'id': article_id,
                    'url': url,
                    'title': title,
                    'keyword': keyword,
                    'pub_date': pub_date,
                    'group_name': group_name,
                    'matched_keyword': matched_keyword
                })
                print(f"⚾ {title[:50]}... (키워드: {matched_keyword})")
        
        print("-" * 60)
        print(f"🎯 야구 관련 기사 {len(baseball_articles)}개 발견 (전체의 {len(baseball_articles)/total_articles*100:.1f}%)")
        
        if not baseball_articles:
            print("❌ 야구 관련 기사가 없습니다.")
            return
        
        # 자동 분류 시작
        print(f"\n🚀 {len(baseball_articles)}개 기사를 자동으로 '해당없음'으로 분류합니다...")
        
        # classification_logs에 삽입
        classified_count = 0
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for article in baseball_articles:
            try:
                cursor.execute('''
                    INSERT INTO classification_logs 
                    (url, keyword, classification_result, confidence_score, reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    article['url'],
                    article['keyword'],
                    '해당없음',
                    1,
                    '스포츠 야구 관련 기사로 패션 브랜드 MLB와 연관없음',
                    current_time
                ))
                classified_count += 1
                
                if classified_count % 50 == 0:
                    print(f"📝 진행상황: {classified_count}/{len(baseball_articles)}")
                    
            except sqlite3.IntegrityError as e:
                print(f"⚠️ 중복 URL 건너뜀: {article['url']}")
                continue
        
        # 변경사항 저장
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ 작업 완료!")
        print(f"📊 총 {classified_count}개의 야구 관련 기사를 '해당없음'으로 분류했습니다.")
        print(f"🔗 분류 결과: 해당없음")
        print(f"🎯 신뢰도: 1.0")
        print(f"📝 사유: 스포츠 야구 관련 기사로 패션 브랜드 MLB와 연관없음")
        print("=" * 60)
        
        # 결과 확인
        cursor.execute('''
            SELECT classification_result, COUNT(*) as count
            FROM classification_logs cl
            JOIN articles a ON cl.url = a.url
            WHERE a.group_name LIKE "%MLB%"
            AND DATE(a.pub_date) LIKE "2025-07-%"
            GROUP BY classification_result
        ''')
        
        results = cursor.fetchall()
        print(f"\n📈 2025년 7월 MLB 그룹 분류 현황:")
        for result, count in results:
            print(f"  - {result}: {count}개")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 MLB 야구 관련 기사 자동 분류 시작")
    print("=" * 60)
    classify_mlb_baseball_articles() 