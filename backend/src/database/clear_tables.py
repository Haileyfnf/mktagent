import sqlite3
import os

DB_PATH = "backend/src/database/db.sqlite"

def clear_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 테이블 삭제
    cursor.execute("DROP TABLE IF EXISTS articles")
    
    conn.commit()
    conn.close()
    print("테이블이 삭제되었습니다.")

if __name__ == "__main__":
    clear_tables() 