import json, os, hashlib
from sqlalchemy.orm import Session
from models.knowledge_core import Holiday

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "holidays_kr_2025.json")

def run(db: Session):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)  # [{date,name,type,is_public}]
    upserted = 0
    h = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    for r in data:
        obj = db.query(Holiday).get(r["date"])
        if not obj:
            obj = Holiday(date=r["date"], name=r["name"])
        obj.name = r["name"]
        obj.type = r.get("type", "public")
        obj.is_public = bool(r.get("is_public", True))
        obj.source_ref = r.get("source_ref")
        db.merge(obj); upserted += 1
    db.commit()
    return upserted, h, f"holidays: upserted={upserted}"
