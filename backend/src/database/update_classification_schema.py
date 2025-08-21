import sqlite3
import os

def update_classification_schema():
    """classification_logs 테이블의 칼럼명을 변경합니다."""
    # 데이터베이스 경로 설정
    DB_PATH = "db.sqlite" if os.path.exists("db.sqlite") else "backend/src/database/db.sqlite"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 기존 테이블 삭제 (데이터가 없으므로 안전)
        cursor.execute("DROP TABLE IF EXISTS classification_logs")
        
        # 새로운 칼럼명으로 테이블 생성
        cursor.execute("""
            CREATE TABLE classification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                group_name TEXT,
                title TEXT,
                content TEXT,
                url TEXT NOT NULL,
                classification_result TEXT,
                confidence_score REAL,
                reason TEXT,
                processing_time REAL,
                is_saved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ classification_logs 테이블 칼럼명 변경 완료!")
        print("변경된 칼럼:")
        print("- article_url → url")
        print("- raw_data → content")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_classification_schema() 