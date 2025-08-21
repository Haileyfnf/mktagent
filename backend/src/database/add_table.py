import sqlite3
import os

def add_table():
    # 데이터베이스 경로 설정
    DB_PATH = "backend/src/database/db.sqlite"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # articles 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
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
    """)

    conn.commit()
    conn.close()
    
    print("테이블 추가 완료!")
    print("생성된 테이블: articles")

if __name__ == "__main__":
    add_table()
