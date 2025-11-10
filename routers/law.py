from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from models.law import Law, LawArticle, LawArticleVersion

router = APIRouter(prefix="/law", tags=["law"])

@router.get("/list")
def list_laws(q: Optional[str] = Query(default=None, description="검색어"), db: Session = Depends(get_db)):
    query = db.query(Law)
    if q:
        like = f"%{q}%"
        # law_name 또는 name 같은 컬럼 상황을 모두 흡수
        if hasattr(Law, "law_name"):
            query = query.filter(Law.law_name.like(like))
        elif hasattr(Law, "name"):
            query = query.filter(Law.name.like(like))
    rows = query.order_by(getattr(Law, "law_name", getattr(Law, "name"))).all()
    def to_dict(l: Law):
        return {
            "id": l.id,
            "law_name": getattr(l, "law_name", getattr(l, "name", None)),
            "law_code": getattr(l, "law_code", None),
        }
    return [to_dict(l) for l in rows]

@router.get("/articles")
def list_articles(law_name: str = Query(...), db: Session = Depends(get_db)):
    # law_name/name 중 프로젝트에 있는 컬럼으로 조회
    if hasattr(Law, "law_name"):
        law = db.query(Law).filter(Law.law_name == law_name).first()
    else:
        law = db.query(Law).filter(Law.name == law_name).first()
    if not law:
        return []
    arts = db.query(LawArticle).filter(LawArticle.law_id == law.id).order_by(LawArticle.id).all()
    res = []
    for a in arts:
        # 버전 수 카운트(옵션)
        vcount = 0
        if hasattr(LawArticleVersion, "article_id"):
            vcount = db.query(LawArticleVersion).filter(LawArticleVersion.article_id == a.id).count()
        res.append({
            "id": a.id,
            "law_id": a.law_id,
            "article_no": getattr(a, "article_no", None),
            "title": getattr(a, "title", None),
            "content": getattr(a, "content", ""),
            "version_count": vcount
        })
    return res

# ✅ 신규: 조문 버전 목록 API
@router.get("/article-versions")
def list_article_versions(
    article_id: int = Query(..., description="LawArticle.id"),
    db: Session = Depends(get_db)
):
    if not hasattr(LawArticleVersion, "article_id"):
        # 모델에 버전 테이블이 없거나 매핑되지 않은 경우 빈 배열
        return []
    versions = (
        db.query(LawArticleVersion)
        .filter(LawArticleVersion.article_id == article_id)
        .order_by(getattr(LawArticleVersion, "effective_date", None).desc()
                  if hasattr(LawArticleVersion, "effective_date") else LawArticleVersion.id.desc())
        .all()
    )
    def to_dict(v: LawArticleVersion):
        return {
            "id": v.id,
            "article_id": v.article_id,
            "version_no": getattr(v, "version_no", None),
            "effective_date": getattr(v, "effective_date", None),
            "content": getattr(v, "content", ""),
        }
    return [to_dict(v) for v in versions]
