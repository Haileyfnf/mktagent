import sqlite3

DB_PATH = 'c:/Users/haenee/mkt_ai_agent/backend/src/database/db.sqlite'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# F&F 키워드 정보 확인
cursor.execute("SELECT keyword, group_name, is_active FROM keywords WHERE keyword = 'F&F'")
result = cursor.fetchone()

if result:
    keyword, group_name, is_active = result
    print(f"F&F 키워드 정보:")
    print(f"  - 키워드: {keyword}")
    print(f"  - 그룹: {group_name}")
    print(f"  - 활성화: {is_active}")
else:
    print("F&F 키워드를 찾을 수 없습니다.")

# 모든 활성 키워드 확인
cursor.execute("SELECT keyword, group_name FROM keywords WHERE is_active = 1")
all_keywords = cursor.fetchall()

print(f"\n모든 활성 키워드:")
for keyword, group_name in all_keywords:
    print(f"  - {keyword} → 그룹: {group_name or '없음'}")

conn.close() 