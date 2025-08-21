#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
데이터베이스 스키마 업데이트 스크립트
"""

import sqlite3
import os

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(__file__), 'news.db')

def update_database_schema():
    """데이터베이스 스키마 업데이트"""
    print("🔄 데이터베이스 스키마 업데이트 시작")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. keywords 테이블 업데이트
        print("📋 keywords 테이블 업데이트 중...")
        
        # group_name 컬럼 추가
        try:
            cursor.execute("ALTER TABLE keywords ADD COLUMN group_name TEXT")
            print("   ✅ group_name 컬럼 추가됨")
        except sqlite3.OperationalError:
            print("   ℹ️ group_name 컬럼이 이미 존재함")
        
        # is_active 컬럼 추가
        try:
            cursor.execute("ALTER TABLE keywords ADD COLUMN is_active INTEGER DEFAULT 1")
            print("   ✅ is_active 컬럼 추가됨")
        except sqlite3.OperationalError:
            print("   ℹ️ is_active 컬럼이 이미 존재함")
        
        # created_at 컬럼 추가
        try:
            cursor.execute("ALTER TABLE keywords ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
            print("   ✅ created_at 컬럼 추가됨")
        except sqlite3.OperationalError:
            print("   ℹ️ created_at 컬럼이 이미 존재함")
        
        # 2. articles 테이블 업데이트
        print("📰 articles 테이블 업데이트 중...")
        
        # group_name 컬럼 추가
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN group_name TEXT")
            print("   ✅ group_name 컬럼 추가됨")
        except sqlite3.OperationalError:
            print("   ℹ️ group_name 컬럼이 이미 존재함")
        
        # content 컬럼 추가
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN content TEXT")
            print("   ✅ content 컬럼 추가됨")
        except sqlite3.OperationalError:
            print("   ℹ️ content 컬럼이 이미 존재함")
        
        # is_active 컬럼 추가
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN is_active INTEGER DEFAULT 1")
            print("   ✅ is_active 컬럼 추가됨")
        except sqlite3.OperationalError:
            print("   ℹ️ is_active 컬럼이 이미 존재함")
        
        # created_at 컬럼 추가
        try:
            cursor.execute("ALTER TABLE articles ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP")
            print("   ✅ created_at 컬럼 추가됨")
        except sqlite3.OperationalError:
            print("   ℹ️ created_at 컬럼이 이미 존재함")
        
        # 3. classification_logs 테이블 생성
        print("🤖 classification_logs 테이블 생성 중...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_url TEXT NOT NULL,
                keyword TEXT NOT NULL,
                group_name TEXT,
                raw_data TEXT,
                ai_input TEXT,
                ai_output TEXT,
                classification_result TEXT,
                confidence_score TEXT,
                processing_time REAL,
                is_saved INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ classification_logs 테이블 생성됨")
        
        # 4. 기존 데이터에 기본값 설정
        print("🔄 기존 데이터 업데이트 중...")
        
        # keywords 테이블의 is_active를 모두 1로 설정
        cursor.execute("UPDATE keywords SET is_active = 1 WHERE is_active IS NULL")
        print("   ✅ keywords 테이블 is_active 기본값 설정")
        
        # articles 테이블의 is_active를 모두 1로 설정
        cursor.execute("UPDATE articles SET is_active = 1 WHERE is_active IS NULL")
        print("   ✅ articles 테이블 is_active 기본값 설정")
        
        # 변경사항 저장
        conn.commit()
        print("✅ 모든 변경사항이 저장되었습니다.")
        
        # 5. 테이블 구조 확인
        print("\n📊 테이블 구조 확인:")
        
        cursor.execute("PRAGMA table_info(keywords)")
        keywords_columns = cursor.fetchall()
        print("   keywords 테이블 컬럼:")
        for col in keywords_columns:
            print(f"     - {col[1]} ({col[2]})")
        
        cursor.execute("PRAGMA table_info(articles)")
        articles_columns = cursor.fetchall()
        print("   articles 테이블 컬럼:")
        for col in articles_columns:
            print(f"     - {col[1]} ({col[2]})")
        
        cursor.execute("PRAGMA table_info(classification_logs)")
        logs_columns = cursor.fetchall()
        print("   classification_logs 테이블 컬럼:")
        for col in logs_columns:
            print(f"     - {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"❌ 업데이트 중 오류 발생: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
    
    print("\n🎉 데이터베이스 스키마 업데이트가 완료되었습니다!")
    return True

if __name__ == "__main__":
    update_database_schema() 