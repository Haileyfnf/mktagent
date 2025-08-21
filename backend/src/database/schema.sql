CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    keyword TEXT NOT NULL,
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT,                    -- 수집된 키워드
    title TEXT,                      -- 기사 제목
    url TEXT UNIQUE,                -- 기사 URL
    pub_date TEXT,                  -- 발행일 (yyyy-mm-dd)
    press TEXT,                      -- 언론사
    classification TEXT,            -- 분류 결과 (자사 보도자료 등)
    classification_update TEXT,     -- 분류 일시
    class_evidence TEXT,            -- 분류 근거 문구만 저장
    ai_classification TEXT,         -- AI 분류 결과
    ai_reasoning TEXT,              -- AI 분류 이유
    ai_confidence REAL              -- AI 분류 신뢰도 (0.0-1.0)
);
