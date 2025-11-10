from sqlalchemy.orm import Session
from models.knowledge_core import PolicyBulletin

def run(db: Session):
    """
    스켈레톤: 실제로는 MOEL 공지/고시 게시판 크롤/피드 → upsert.
    여기서는 1건 예시.
    """
    upserted = 0
    bid = "PB-2025-001"
    obj = db.query(PolicyBulletin).get(bid)
    if not obj:
        obj = PolicyBulletin(
            id=bid,
            title="2025 최저임금 고시 요약",
            effective_date="2025-01-01",
            audience="both",
            category="최저임금",
            summary_md="2025년 최저임금 **시급 10,030원** 적용.",
            law_id="KOR_LAW_최저임금법",
            article_no="제6조",
            source_url="https://www.moel.go.kr",
            tags="최저임금;고시"
        )
        db.add(obj); upserted += 1
    db.commit()
    checksum = f"notice-{upserted}"
    return upserted, checksum, "moel_notice demo upsert"
