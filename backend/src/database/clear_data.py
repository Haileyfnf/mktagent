import sqlite3
import os

def clear_articles():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "db.sqlite")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # articles 테이블의 모든 데이터 삭제
    c.execute("DELETE FROM classification_logs")
    conn.commit()
    
    print("articles 테이블의 모든 데이터가 삭제되었습니다.")
    
    # 삭제 확인
    c.execute("SELECT COUNT(*) FROM classification_logs")
    count = c.fetchone()[0]
    print(f"현재 classification_logs 테이블의 키워드 수: {count}")
    
    conn.close()

if __name__ == "__main__":
    clear_articles() 