from sqlalchemy.orm import Session
from models.knowledge_core import AdminInterpretation

def run(db: Session):
    """
    스켈레톤: 실제로는 행정해석 OpenAPI 페이징 호출 → upsert.
    여기서는 1건 예시.
    """
    upserted = 0
    iid = "MOEL-INT-2025-0001"
    obj = db.query(AdminInterpretation).get(iid)
    if not obj:
        obj = AdminInterpretation(
            interp_id=iid,
            title="연차사용계획 통지 관련 질의",
            asked_at="2025-01-10",
            answered_at="2025-01-20",
            question="연차사용계획 통지는 어떤 방식이 적정한가?",
            answer="서면 또는 전자문서로 개별 통지하고 기록을 보관하는 것이 적정.",
            law_id="KOR_LAW_근로기준법",
            article_no="제61조",
            source_url="https://www.moel.go.kr",
            tags="연차;촉진"
        )
        db.add(obj); upserted += 1
    db.commit()
    checksum = f"interpretation-{upserted}"
    return upserted, checksum, "interpretation demo upsert"
