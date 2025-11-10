import json, os, hashlib
from sqlalchemy.orm import Session
from models.knowledge_core import MinimumWageHistory

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "minimum_wage_seed.json")

def run(db: Session):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)  # [{year, hourly, monthly_209h, notice_no, notice_date, source_url}]
    upserted = 0
    h = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    for r in data:
        obj = db.query(MinimumWageHistory).get(r["year"])
        if not obj:
            obj = MinimumWageHistory(year=r["year"], hourly=r["hourly"])
        obj.hourly = r["hourly"]
        obj.monthly_209h = r.get("monthly_209h")
        obj.notice_no = r.get("notice_no")
        obj.notice_date = r.get("notice_date")
        obj.source_url = r.get("source_url")
        db.merge(obj); upserted += 1
    db.commit()
    return upserted, h, f"minwage: upserted={upserted}"
