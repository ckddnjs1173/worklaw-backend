import os, re, sys, sqlite3

DB = "worklaw.db"
abs_path = os.path.abspath(DB)
print(f"[i] DB: {abs_path}  exists: {os.path.exists(DB)}")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

# 모든 테이블 나열
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r["name"] for r in cur.fetchall()]
print("[i] tables:", tables)

# 'minimum' 또는 'wage'가 들어간 테이블 후보 탐지
candidates = [t for t in tables if re.search(r"(minimum|wage)", t, re.IGNORECASE)]
print("[i] minimum wage table candidates:", candidates)

def table_cols(t):
    cur.execute(f"PRAGMA table_info({t})")
    return [(r["name"], r["type"]) for r in cur.fetchall()]

target, col_year, col_amount = None, None, None

for t in candidates:
    cols = table_cols(t)
    names = [c[0].lower() for c in cols]
    # 대표적인 컬럼명 후보
    y = next((n for n in names if n in ("year","yyyy","y")), None)
    a = next((n for n in names if n in ("hourly","amount","wage","value","price","pay")), None)
    if y and a:
        target, col_year, col_amount = t, y, a
        print(f"[i] chosen table: {t}  cols={cols}  year={y}  amount={a}")
        break

if not target:
    print("[!] minimum wage table not found. Check Alembic or your schema.")
    # 힌트: 실제 테이블/컬럼명을 알려주면 맞춰서 스크립트 바로 만들어 드릴 수 있습니다.
    con.close()
    sys.exit(1)

# 2025 레코드 업서트(없으면 INSERT, 있으면 UPDATE)
cur.execute(f"SELECT 1 FROM {target} WHERE {col_year}=?", (2025,))
exists = cur.fetchone() is not None
if exists:
    cur.execute(f"UPDATE {target} SET {col_amount}=? WHERE {col_year}=?", (10000, 2025))
    print(f"[i] updated {target} 2025 -> 10000")
else:
    cur.execute(f"INSERT INTO {target} ({col_year}, {col_amount}) VALUES (?, ?)", (2025, 10000))
    print(f"[i] inserted {target} 2025 -> 10000")

con.commit()
con.close()
print("[i] seed done.")
