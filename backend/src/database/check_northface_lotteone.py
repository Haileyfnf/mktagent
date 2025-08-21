#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
노스페이스 롯데온 관련 기사 현재 상태 확인 스크립트
"""

import sqlite3

def check_northface_lotteone_articles():
    """노스페이스 롯데온 관련 기사들의 현재 상태 확인"""
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    try:
        print("🔍 노스페이스 롯데온 관련 기사 상태 확인")
        print("=" * 60)
        
        # 1. 전체 노스페이스 롯데온 기사 수
        cursor.execute('''
            SELECT COUNT(*) 
            FROM articles 
            WHERE keyword = '노스페이스' 
            AND DATE(pub_date) LIKE "2025-07-%" 
            AND title LIKE "%롯데온%"
        ''')
        total_count = cursor.fetchone()[0]
        print(f"📊 2025년 7월 노스페이스 + 롯데온 기사 총 {total_count}개")
        
        # 2. 분류된 기사들 확인
        cursor.execute('''
            SELECT a.title, cl.classification_result, cl.confidence_score, cl.reason
            FROM articles a
            LEFT JOIN classification_logs cl ON a.url = cl.url
            WHERE a.keyword = '노스페이스'
            AND DATE(a.pub_date) LIKE "2025-07-%"
            AND a.title LIKE "%롯데온%"
        ''')
        
        results = cursor.fetchall()
        
        print(f"\n📋 기사별 분류 상태:")
        print("-" * 60)
        
        classified_count = 0
        unclassified_count = 0
        
        for title, classification, confidence, reason in results:
            if classification:
                classified_count += 1
                print(f"✅ 분류됨: {title[:50]}...")
                print(f"   └ 분류: {classification} (신뢰도: {confidence})")
                print(f"   └ 사유: {reason[:50]}...")
            else:
                unclassified_count += 1
                print(f"❌ 미분류: {title[:50]}...")
            print()
        
        print("=" * 60)
        print(f"📈 분류 현황 요약:")
        print(f"  - 전체: {total_count}개")
        print(f"  - 분류됨: {classified_count}개") 
        print(f"  - 미분류: {unclassified_count}개")
        
        if unclassified_count > 0:
            print(f"\n⚠️  {unclassified_count}개 기사가 아직 미분류 상태입니다.")
        else:
            print(f"\n✅ 모든 기사가 분류 완료되었습니다!")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_northface_lotteone_articles() 