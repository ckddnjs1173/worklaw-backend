from sqlalchemy.orm import Session
from models.knowledge_core import Law, LawVersion, LawArticle
from datetime import datetime

def run(db: Session):
    """
    스켈레톤: 실제로는 국가법령정보 OpenAPI를 호출해 laws/versions/articles를 적재.
    여기서는 예시 1건을 더미로 채움.
    """
    upserted = 0
    # Law
    law_id = "KOR_LAW_근로기준법"
    law = db.query(Law).get(law_id)
    if not law:
        law = Law(law_id=law_id, law_name_kr="근로기준법", law_name_en="Labor Standards Act", status="current")
        db.add(law); upserted += 1
    else:
        law.status = "current"

    # Version
    version_no = "2025-01-01"
    from models.knowledge_core import LawVersion
    ver = db.query(LawVersion).filter_by(law_id=law_id, version_no=version_no).first()
    if not ver:
        ver = LawVersion(id=f"{law_id}_{version_no}", law_id=law_id, version_no=version_no,
                         effective_from="2025-01-01", effective_to=None, source_ref="demo")
        db.add(ver); upserted += 1

    # Article
    art_id = f"{law_id}_{version_no}_제17조"
    art = db.query(LawArticle).get(art_id)
    if not art:
        art = LawArticle(
            id=art_id, law_id=law_id, version_no=version_no, article_no="제17조",
            title="(근로조건의 명시)", body_text="사용자는 근로계약을 체결할 때 임금 등 근로조건을 명시하여야 한다.",
            body_html="<p>사용자는 근로계약을 체결할 때 임금 등 근로조건을 명시하여야 한다.</p>",
            updated_at=str(datetime.utcnow().date())
        )
        db.add(art); upserted += 1
    db.commit()
    checksum = f"{law_id}-{version_no}-{upserted}"
    return upserted, checksum, "law_api demo upsert"
