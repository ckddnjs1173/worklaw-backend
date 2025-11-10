import os, sqlite3
from fastapi import APIRouter, Query

router = APIRouter(prefix="/metadata", tags=["metadata-staging"])

def _read_min_wage(year: int):
    # DATABASE_URL=sqlite:///./worklaw.db 만 처리(스테이징)
    db_path = "worklaw.db"
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        # 스키마: minimum_wage(year, amount, unit)
        cur.execute("SELECT year, amount, unit FROM minimum_wage WHERE year=?", (year,))
        row = cur.fetchone()
        con.close()
        if row:
            y, amount, unit = row
            return {"year": y, "hourly": int(amount), "unit": unit or "KRW_per_hour", "source": "staging-db"}
    except Exception as e:
        print("staging minimum-wage read error:", repr(e))
    # 없거나 오류면 안전한 기본값
    return {"year": year, "hourly": 0, "unit": "KRW_per_hour", "source": "staging-fallback"}

@router.get("/minimum-wage")
def get_minimum_wage(year: int = Query(..., ge=1900, le=2100)):
    # 스테이징에서만 이 오버라이드가 활성화됨( main.py에서 include )
    return _read_min_wage(year)
