import sqlite3
conn = sqlite3.connect("backend/src/database/db.sqlite")
cursor = conn.cursor()

# classification_logs 테이블에 기사 제목 칼럼 추가
try:
    cursor.execute("ALTER TABLE classification_logs ADD COLUMN reason TEXT;")
    print("classification_logs 테이블에 reason 칼럼 추가 완료!")
except Exception as e:
    print("이미 칼럼이 있거나 오류:", e)

conn.commit()
conn.close()