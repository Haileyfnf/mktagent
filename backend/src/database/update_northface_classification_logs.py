#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 classification_logs에 있는 노스페이스 데이터의 누락된 필드 업데이트 스크립트
group_name, title, content, is_saved 필드를 articles 테이블에서 가져와서 업데이트합니다.
"""

import sqlite3
from datetime import datetime

def update_northface_classification_logs():
    """기존 노스페이스 classification_logs 데이터에 누락된 필드들 업데이트"""
    
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    try:
        print("🔧 노스페이스 classification_logs 데이터 업데이트 시작")
        print("=" * 60)
        
        # 1. 업데이트가 필요한 노스페이스 분류 로그 조회
        cursor.execute('''
            SELECT cl.url, cl.keyword, a.group_name, a.title, a.content
            FROM classification_logs cl
            JOIN articles a ON cl.url = a.url
            WHERE cl.keyword = '노스페이스'
            AND DATE(a.pub_date) LIKE "2025-07-%"
            AND (cl.group_name IS NULL OR cl.title IS NULL OR cl.content IS NULL OR cl.is_saved IS NULL)
        ''')
        
        logs_to_update = cursor.fetchall()
        total_count = len(logs_to_update)
        
        print(f"📊 업데이트가 필요한 노스페이스 분류 로그: {total_count}개")
        print("-" * 60)
        
        if not logs_to_update:
            print("✅ 업데이트가 필요한 데이터가 없습니다.")
            return
        
        # 2. 각 로그 업데이트
        updated_count = 0
        
        for log in logs_to_update:
            url, keyword, group_name, title, content = log
            
            try:
                cursor.execute('''
                    UPDATE classification_logs 
                    SET group_name = ?, title = ?, content = ?, is_saved = 1
                    WHERE url = ? AND keyword = ?
                ''', (group_name, title, content, url, keyword))
                
                updated_count += 1
                print(f"✅ 업데이트 완료: {title[:50]}...")
                
            except Exception as e:
                print(f"⚠️ 업데이트 실패: {url} - {str(e)}")
                continue
        
        # 3. 변경사항 저장
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ 업데이트 작업 완료!")
        print(f"📊 총 {updated_count}개의 분류 로그를 업데이트했습니다.")
        print("=" * 60)
        
        # 4. 업데이트 결과 확인
        cursor.execute('''
            SELECT COUNT(*) 
            FROM classification_logs cl
            JOIN articles a ON cl.url = a.url
            WHERE cl.keyword = '노스페이스'
            AND DATE(a.pub_date) LIKE "2025-07-%"
            AND cl.group_name IS NOT NULL 
            AND cl.title IS NOT NULL 
            AND cl.content IS NOT NULL 
            AND cl.is_saved = 1
        ''')
        
        complete_count = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM classification_logs cl
            JOIN articles a ON cl.url = a.url
            WHERE cl.keyword = '노스페이스'
            AND DATE(a.pub_date) LIKE "2025-07-%"
        ''')
        
        total_logs = cursor.fetchone()[0]
        
        print(f"\n📈 업데이트 결과:")
        print(f"  - 전체 노스페이스 분류 로그: {total_logs}개")
        print(f"  - 완전한 데이터를 가진 로그: {complete_count}개")
        
        if complete_count == total_logs:
            print(f"\n🎉 모든 노스페이스 분류 로그가 완전한 데이터를 가지고 있습니다!")
        else:
            incomplete_count = total_logs - complete_count
            print(f"\n⚠️  {incomplete_count}개의 로그에 여전히 누락된 데이터가 있습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    update_northface_classification_logs() 