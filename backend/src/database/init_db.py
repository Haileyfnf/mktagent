import sqlite3
import os

def init_database():
    # 데이터베이스 경로 설정
    DB_PATH = "db.sqlite" if os.path.exists("db.sqlite") else "backend/src/database/db.sqlite"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # keywords 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            keyword TEXT NOT NULL,
            group_name TEXT,
            type TEXT DEFAULT '자사',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # articles 테이블 생성
    cursor.execute("""
        CREATE TABLE articles (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       keyword TEXT NOT NULL,
       group_name TEXT,
       title TEXT,
       content TEXT,
       press TEXT,
       pub_date TEXT,
       url TEXT UNIQUE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
        )
    """)
    
    # classification_logs 테이블 생성
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
            confidence_score REAL,
            processing_time REAL,
            is_saved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("데이터베이스 초기화 완료!")
    print("생성된 테이블:")
    print("- keywords: 키워드 저장 테이블")
    print("- articles: 크롤링된 기사 저장 테이블")
    print("- classification_logs: 분류 로그 저장 테이블")

if __name__ == "__main__":
    init_database()
