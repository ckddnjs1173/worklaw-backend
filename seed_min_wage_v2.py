import sqlite3, os

DB = "worklaw.db"
abs_path = os.path.abspath(DB)
print(f"[i] DB: {abs_path}  exists: {os.path.exists(DB)}")

con = sqlite3.connect(DB)
cur = con.cursor()

TARGET_TABLE = "minimum_wage"
COL_YEAR = "year"
COL_AMOUNT = "amount"
COL_UNIT = "unit"

YEAR = 2025
AMOUNT = 10000         # 예시 시드값 (원/시)
UNIT = "KRW_per_hour"  # NOT NULL 충족용 단위 문자열 (원/시간)

# 1) 먼저 UPDATE 시도(있으면 갱신)
cur.execute(
    f"UPDATE {TARGET_TABLE} SET {COL_AMOUNT}=?, {COL_UNIT}=? WHERE {COL_YEAR}=?",
    (AMOUNT, UNIT, YEAR),
)
if cur.rowcount:
    print(f"[i] updated {TARGET_TABLE} {YEAR} -> amount={AMOUNT}, unit={UNIT}")
else:
    # 2) 없으면 INSERT
    cur.execute(
        f"INSERT INTO {TARGET_TABLE} ({COL_YEAR}, {COL_AMOUNT}, {COL_UNIT}) VALUES (?,?,?)",
        (YEAR, AMOUNT, UNIT),
    )
    print(f"[i] inserted {TARGET_TABLE} {YEAR} -> amount={AMOUNT}, unit={UNIT}")

con.commit()
# 확인 출력
cur.execute(
    f"SELECT {COL_YEAR}, {COL_AMOUNT}, {COL_UNIT} FROM {TARGET_TABLE} WHERE {COL_YEAR}=?",
    (YEAR,),
)
print("[i] row:", cur.fetchone())
con.close()
