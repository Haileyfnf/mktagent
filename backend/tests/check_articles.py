import sqlite3

def check_articles():
    conn = sqlite3.connect("db.sqlite")
    c = conn.cursor()
    
    # articles 테이블의 모든 데이터 조회
    c.execute("SELECT * FROM articles")
    articles = c.fetchall()
    
    print(f"=== 데이터베이스에 저장된 기사 수: {len(articles)} ===")
    
    if articles:
        print("\n저장된 기사 목록:")
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. 기사 정보:")
            print(f"   키워드: {article[0]}")
            print(f"   제목: {article[1]}")
            print(f"   URL: {article[2]}")
            print(f"   발행일: {article[3]}")
            print(f"   언론사: {article[4]}")
            print(f"   분류: {article[5]}")
            print(f"   분류 업데이트: {article[6]}")
            print(f"   분류 근거: {article[7]}")
    else:
        print("저장된 기사가 없습니다.")
    
    # 키워드별 기사 수 확인
    print("\n=== 키워드별 기사 수 ===")
    c.execute("SELECT keyword, COUNT(*) as count FROM articles GROUP BY keyword")
    keyword_counts = c.fetchall()
    
    for keyword, count in keyword_counts:
        print(f"{keyword}: {count}개")
    
    conn.close()

if __name__ == "__main__":
    check_articles() 