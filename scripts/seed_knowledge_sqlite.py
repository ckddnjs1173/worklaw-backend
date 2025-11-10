import sqlite3
from pathlib import Path
from typing import List, Tuple

DB_PATH = Path(__file__).resolve().parents[1] / "worklaw.db"


def table_exists(cur: sqlite3.Cursor, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None


def table_columns(cur: sqlite3.Cursor, name: str) -> List[str]:
    cur.execute(f"PRAGMA table_info({name});")
    return [row[1] for row in cur.fetchall()]  # cid, name, type, notnull, dflt_value, pk


def ensure_table(cur: sqlite3.Cursor, create_sql: str):
    cur.execute(create_sql)


def upsert_minwage(cur: sqlite3.Cursor, rows: List[Tuple[int, int, int, str, str, str]]):
    """
    rows: (year, hourly, monthly_209h, notice_no, notice_date, source_url)
    스키마 자동 감지:
      - hourly 컬럼이 있으면 hourly 사용
      - 없고 amount, unit이 있으면 amount=hourly, unit='KRW/hour'
      - monthly_209h/notice_* 컬럼이 없으면 해당 컬럼은 생략
    """
    if not table_exists(cur, "minimum_wage_history"):
        # 표준 스키마 생성
        ensure_table(
            cur,
            """
            CREATE TABLE IF NOT EXISTS minimum_wage_history (
              year INTEGER PRIMARY KEY,
              hourly INTEGER NOT NULL,
              monthly_209h INTEGER,
              notice_no TEXT,
              notice_date TEXT,
              source_url TEXT
            );
            """,
        )

    cols = set(table_columns(cur, "minimum_wage_history"))
    has_hourly = "hourly" in cols
    has_amount = "amount" in cols
    has_unit = "unit" in cols
    has_monthly = "monthly_209h" in cols
    has_notice_no = "notice_no" in cols
    has_notice_date = "notice_date" in cols
    has_source_url = "source_url" in cols

    # 컬럼이 부족하지만 운영 DB를 바꾸기 어렵다면 ALTER로 보완
    # (원치 않으면 주석처리 가능)
    # 안전하게 추가 시도 (이미 있으면 무시되거나 에러 -> try/except)
    def try_add(col_def: str):
        try:
            cur.execute(f"ALTER TABLE minimum_wage_history ADD COLUMN {col_def};")
        except Exception:
            pass

    # 최소한 참조용 메타 컬럼들도 있으면 좋다
    if not has_monthly:
        try_add("monthly_209h INTEGER")
        has_monthly = True
    if not has_notice_no:
        try_add("notice_no TEXT")
        has_notice_no = True
    if not has_notice_date:
        try_add("notice_date TEXT")
        has_notice_date = True
    if not has_source_url:
        try_add("source_url TEXT")
        has_source_url = True

    # upsert 분기
    for year, hourly, monthly_209h, notice_no, notice_date, source_url in rows:
        if has_hourly:
            # hourly 사용
            sql = f"""
                INSERT INTO minimum_wage_history
                    (year, hourly{', monthly_209h' if has_monthly else ''}{', notice_no' if has_notice_no else ''}{', notice_date' if has_notice_date else ''}{', source_url' if has_source_url else ''})
                VALUES
                    (? ,   ?    {', ?' if has_monthly else ''}{', ?' if has_notice_no else ''}{', ?' if has_notice_date else ''}{', ?' if has_source_url else ''})
                ON CONFLICT(year) DO UPDATE SET
                    hourly=excluded.hourly
                    {', monthly_209h=excluded.monthly_209h' if has_monthly else ''}
                    {', notice_no=excluded.notice_no' if has_notice_no else ''}
                    {', notice_date=excluded.notice_date' if has_notice_date else ''}
                    {', source_url=excluded.source_url' if has_source_url else ''};
            """
            params = [year, hourly]
            if has_monthly:
                params.append(monthly_209h)
            if has_notice_no:
                params.append(notice_no)
            if has_notice_date:
                params.append(notice_date)
            if has_source_url:
                params.append(source_url)
            cur.execute(sql, params)

        elif has_amount and has_unit:
            # amount/unit 스키마 사용 (amount=hourly, unit='KRW/hour')
            # 필요한 보조 컬럼은 존재 여부에 따라 선택
            placeholders = ["?", "?", "?", "?", "?", "?"]  # year, amount, unit, monthly_209h, notice_no, notice_date, source_url (유동)
            cols_insert = ["year", "amount", "unit"]
            vals = [year, hourly, "KRW/hour"]

            if has_monthly:
                cols_insert.append("monthly_209h")
                vals.append(monthly_209h)
            if has_notice_no:
                cols_insert.append("notice_no")
                vals.append(notice_no)
            if has_notice_date:
                cols_insert.append("notice_date")
                vals.append(notice_date)
            if has_source_url:
                cols_insert.append("source_url")
                vals.append(source_url)

            columns_sql = ", ".join(cols_insert)
            qmarks_sql = ", ".join(["?"] * len(vals))
            set_sql_parts = ["amount=excluded.amount", "unit=excluded.unit"]
            if has_monthly:
                set_sql_parts.append("monthly_209h=excluded.monthly_209h")
            if has_notice_no:
                set_sql_parts.append("notice_no=excluded.notice_no")
            if has_notice_date:
                set_sql_parts.append("notice_date=excluded.notice_date")
            if has_source_url:
                set_sql_parts.append("source_url=excluded.source_url")

            sql = f"""
                INSERT INTO minimum_wage_history ({columns_sql})
                VALUES ({qmarks_sql})
                ON CONFLICT(year) DO UPDATE SET {", ".join(set_sql_parts)};
            """
            cur.execute(sql, vals)

        else:
            # 스키마가 특이하면 최소한 year만 보존
            cur.execute(
                "INSERT OR IGNORE INTO minimum_wage_history (year) VALUES (?);",
                (year,),
            )


def upsert_holidays(cur: sqlite3.Cursor, rows: List[Tuple[str, str, str, int, str]]):
    """
    rows: (date 'YYYY-MM-DD', name, type, is_public(0/1), source_ref)
    """
    if not table_exists(cur, "holidays"):
        ensure_table(
            cur,
            """
            CREATE TABLE IF NOT EXISTS holidays (
              date TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              type TEXT,
              is_public INTEGER DEFAULT 1,
              source_ref TEXT
            );
            """,
        )

    for r in rows:
        cur.execute(
            """
            INSERT INTO holidays (date, name, type, is_public, source_ref)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
              name=excluded.name,
              type=excluded.type,
              is_public=excluded.is_public,
              source_ref=excluded.source_ref;
            """,
            r,
        )


def upsert_policy_bulletins(cur: sqlite3.Cursor, rows: List[Tuple[str, str, str, str, str, str, str, str]]):
    """
    rows: (title, effective_date, audience, category, summary_md, law_id, article_no, source_url, tags)
    """
    if not table_exists(cur, "policy_bulletin"):
        ensure_table(
            cur,
            """
            CREATE TABLE IF NOT EXISTS policy_bulletin (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              effective_date TEXT,
              audience TEXT,
              category TEXT,
              summary_md TEXT,
              law_id TEXT,
              article_no TEXT,
              source_url TEXT,
              tags TEXT
            );
            """,
        )

    for r in rows:
        cur.execute(
            """
            INSERT INTO policy_bulletin (title, effective_date, audience, category, summary_md, law_id, article_no, source_url, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            r,
        )


def upsert_interpretations(cur: sqlite3.Cursor, rows: List[Tuple[str, str, str, str, str, str, str, str]]):
    """
    rows: (title, asked_at, answered_at, question, answer, law_id, article_no, source_url, tags)
    """
    if not table_exists(cur, "admin_interpretation"):
        ensure_table(
            cur,
            """
            CREATE TABLE IF NOT EXISTS admin_interpretation (
              interp_id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              asked_at TEXT,
              answered_at TEXT,
              question TEXT,
              answer TEXT,
              law_id TEXT,
              article_no TEXT,
              source_url TEXT,
              tags TEXT
            );
            """,
        )

    for r in rows:
        cur.execute(
            """
            INSERT INTO admin_interpretation (title, asked_at, answered_at, question, answer, law_id, article_no, source_url, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            r,
        )


def main():
    print(f"[i] DB: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # --- Minimum Wage ---
    minwage_rows = [
        # year, hourly, monthly_209h, notice_no, notice_date, source_url
        (2024, 9860, 9860 * 209, "고시 제2023-1호", "2023-08-04", "https://www.moel.go.kr/"),
        (2025, 10030, 10030 * 209, "고시 제2024-1호", "2024-08-05", "https://www.moel.go.kr/"),
    ]
    upsert_minwage(cur, minwage_rows)

    # --- Holidays ---
    holidays_rows = [
        ("2025-01-01", "신정", "legal", 1, "MOIS"),
        ("2025-03-01", "삼일절", "legal", 1, "MOIS"),
        ("2025-05-05", "어린이날", "legal", 1, "MOIS"),
    ]
    upsert_holidays(cur, holidays_rows)

    # --- Policy Bulletins ---
    pb_rows = [
        ("주52시간제 점검 가이드", "2025-01-15", "employer", "worktime",
         "주요 점검 항목과 Q&A를 정리했습니다.", "근로기준법", "50", "https://moel.go.kr/", "가이드,근로시간"),
        ("연차촉진 절차 안내", "2025-02-01", "employer", "leave",
         "연차촉진 서식과 기한 일정을 안내합니다.", "근로기준법", "61", "https://moel.go.kr/", "연차,촉진"),
    ]
    upsert_policy_bulletins(cur, pb_rows)

    # --- Admin Interpretations ---
    interp_rows = [
        ("연장근로수당 기준", "2024-05-01", "2024-05-10",
         "연장근로수당 산정시 포함 항목은?", "통상임금 산입범위에 따라 판단합니다.", "근로기준법", "56", "https://moel.go.kr/", "연장근로,임금"),
    ]
    upsert_interpretations(cur, interp_rows)

    conn.commit()
    conn.close()
    print("[✓] seed done.")


if __name__ == "__main__":
    main()
