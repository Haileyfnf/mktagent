#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F&F 아홉 관련 기사 자동 분류 스크립트
F&F 키워드로 수집된 기사 중 제목에 '아홉'이 포함된 기사들을 '보도자료'로 분류합니다.
"""

import sqlite3
from datetime import datetime

def classify_ff_ahof_articles():
    """F&F 아홉 관련 기사들을 '보도자료'로 분류"""
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    try:
        print("🚀 F&F 아홉 관련 기사 자동 분류 시작")
        print("=" * 80)
        
        # 1. F&F 키워드로 수집된 기사 중 2025-07-01 이후, 제목에 '아홉'이 포함된 미분류 기사 조회
        cursor.execute('''
            SELECT a.id, a.url, a.title, a.keyword, a.pub_date, a.group_name, a.content
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE a.keyword = 'F&F'
            AND cl.url IS NULL
            AND a.title LIKE "%아홉%"
            AND DATE(a.pub_date) >= '2025-07-01'
        ''')
        
        articles = cursor.fetchall()
        total_articles = len(articles)
        
        print(f"📊 F&F 키워드 중 '아홉' 포함 미분류 기사 (2025-07-01 이후): {total_articles}개")
        print("-" * 80)
        
        if articles:
            print("📝 분류할 기사 목록:")
            for i, article in enumerate(articles, 1):
                article_id, url, title, keyword, pub_date, group_name, content = article
                print(f"{i:2d}. {title[:60]}... ({pub_date})")
            
            print("-" * 80)
            print(f"🎯 {total_articles}개 기사를 자동으로 '보도자료'로 분류합니다...")
            
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
                        '보도자료',
                        1,
                        "'아홉' 혹은 'AHOF'은 F&F엔터테인먼트 소속의 아티스트이다. 그리고 F&F엔터테인먼트는 F&F의 자회사이다. '아홉'의 데뷔 기사가 같은 날에 비슷한 본문 내용으로 게재됨",
                        1,
                        current_time
                    ))
                    classified_count += 1
                    print(f"✅ 분류 완료: {title[:50]}...")
                    
                except sqlite3.IntegrityError as e:
                    print(f"⚠️ 중복 URL 건너뜀: {url}")
                    continue
        else:
            print("❌ 조건에 맞는 미분류 기사가 없습니다.")
        
        # 변경사항 저장
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ 작업 완료!")
        print(f"📊 신규 분류: {classified_count if 'classified_count' in locals() else 0}개")
        print(f"🔗 분류 결과: 보도자료")
        print(f"🎯 신뢰도: 1.0")
        print(f"📝 사유: '아홉' 혹은 'AHOF'은 F&F엔터테인먼트 소속의 아티스트이다. 그리고 F&F엔터테인먼트는 F&F의 자회사이다. '아홉'의 데뷔 기사가 같은 날에 비슷한 본문 내용으로 게재됨")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """메인 함수"""
    try:
        classify_ff_ahof_articles()
    except Exception as e:
        print(f"❌ 스크립트 실행 중 오류 발생: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    main() 