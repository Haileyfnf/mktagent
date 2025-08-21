#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노스페이스 롯데온 관련 기사 자동 분류 스크립트
2025년 7월 노스페이스 키워드 기사 중 '롯데온'이 포함된 기사들을 '오가닉'으로 분류합니다.
"""

import sqlite3
from datetime import datetime

def classify_northface_lotteone_articles():
    """노스페이스 롯데온 관련 기사들을 '오가닉'으로 분류"""
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    try:
        # 2025년 7월 노스페이스 관련 미분류 기사 중 '롯데온' 포함 기사 조회
        cursor.execute('''
            SELECT a.id, a.url, a.title, a.keyword, a.pub_date, a.group_name, a.content
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE a.keyword = '노스페이스'
            AND DATE(a.pub_date) LIKE "2025-07-%"
            AND cl.url IS NULL
            AND a.title LIKE "%롯데온%"
        ''')
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        
        print(f"🚀 노스페이스 롯데온 관련 기사 자동 분류 시작")
        print("=" * 60)
        print(f"📊 총 {total_articles}개의 노스페이스 롯데온 기사를 검사합니다...")
        print("-" * 60)
        
        if not articles:
            print("❌ 조건에 맞는 기사가 없습니다.")
            return
        
        # 각 기사 출력
        for article in articles:
            article_id, url, title, keyword, pub_date, group_name, content = article
            print(f"🛍️  {title[:70]}... ({pub_date})")
        
        print("-" * 60)
        print(f"🎯 롯데온 관련 기사 {total_articles}개 발견")
        print(f"🚀 {total_articles}개 기사를 자동으로 '오가닉'으로 분류합니다...")
        
        # classification_logs에 삽입
        classified_count = 0
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for article in articles:
            article_id, url, title, keyword, pub_date, group_name, content = article
            
            try:
                cursor.execute('''
                    INSERT INTO classification_logs 
                    (url, keyword, group_name, title, content, classification_result, confidence_score, reason, is_saved, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    url,
                    keyword,
                    group_name,
                    title,
                    content,
                    '오가닉',
                    1,
                    '온라인 플랫폼에 노스페이스가 할인 프로모션에 참여한다는 내용이 포함되어 있음',
                    1,
                    current_time
                ))
                classified_count += 1
                print(f"✅ 분류 완료: {title[:50]}...")
                
            except sqlite3.IntegrityError as e:
                print(f"⚠️ 중복 URL 건너뜀: {url}")
                continue
        
        # 변경사항 저장
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ 작업 완료!")
        print(f"📊 총 {classified_count}개의 노스페이스 롯데온 기사를 '오가닉'으로 분류했습니다.")
        print(f"🔗 분류 결과: 오가닉")
        print(f"🎯 신뢰도: 1.0")
        print(f"📝 사유: 온라인 플랫폼에 노스페이스가 할인 프로모션에 참여한다는 내용이 포함되어 있음")
        print("=" * 60)
        
        # 결과 확인 - 2025년 7월 노스페이스 분류 현황
        cursor.execute('''
            SELECT cl.classification_result, COUNT(*) as count
            FROM classification_logs cl
            JOIN articles a ON cl.url = a.url
            WHERE a.keyword = '노스페이스'
            AND DATE(a.pub_date) LIKE "2025-07-%"
            GROUP BY cl.classification_result
        ''')
        
        results = cursor.fetchall()
        print(f"\n📈 2025년 7월 노스페이스 분류 현황:")
        for result, count in results:
            print(f"  - {result}: {count}개")
            
        # 미분류 기사 수 확인
        cursor.execute('''
            SELECT COUNT(*) as unclassified_count
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE a.keyword = '노스페이스'
            AND DATE(a.pub_date) LIKE "2025-07-%"
            AND cl.url IS NULL
        ''')
        
        unclassified_count = cursor.fetchone()[0]
        if unclassified_count > 0:
            print(f"  - 미분류: {unclassified_count}개")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    classify_northface_lotteone_articles() 