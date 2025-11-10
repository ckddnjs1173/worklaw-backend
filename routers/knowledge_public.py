from typing import List, Optional, Any, Iterable
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, text, desc

# --- DB 세션 의존성 ---------------------------------------------------------
try:
    from database.connection import SessionLocal
except Exception as e:  # pragma: no cover
    raise RuntimeError("Cannot import SessionLocal from database.connection") from e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 모델 import (있으면 사용, 없으면 원시 SQL로 폴백) ------------------------
try:
    from models.knowledge_core import (
        MinimumWageHistory,
        PolicyBulletin,
        Holiday,
        AdminInterpretation,
    )
except Exception:
    # 프로젝트 구조에 따라 존재하지 않을 수 있음 → None으로 두고 SQL fallback 사용
    MinimumWageHistory = None  # type: ignore
    PolicyBulletin = None      # type: ignore
    Holiday = None             # type: ignore
    AdminInterpretation = None # type: ignore

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# --- 응답 스키마 --------------------------------------------------------------
class MinimumWageItem(BaseModel):
    year: int
    hourly: int
    monthly_209h: Optional[int] = None
    notice_no: Optional[str] = None
    notice_date: Optional[str] = None
    source_url: Optional[str] = None

class HolidayItem(BaseModel):
    date: str
    name: str
    type: Optional[str] = None
    is_public: Optional[bool] = True
    source_ref: Optional[str] = None

class PolicyBulletinItem(BaseModel):
    id: str
    title: str
    effective_date: Optional[str] = None
    audience: Optional[str] = None
    category: Optional[str] = None
    summary_md: Optional[str] = None
    law_id: Optional[str] = None
    article_no: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[str] = None

class InterpretationItem(BaseModel):
    interp_id: str
    title: str
    asked_at: Optional[str] = None
    answered_at: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    law_id: Optional[str] = None
    article_no: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[str] = None

# --- 유틸: 안전 질의(fail-soft) ----------------------------------------------
def _rows_to_list(rows: Iterable[Any]) -> list[dict]:
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(r)
        else:
            # SQLAlchemy ORM 객체 혹은 Row → dict로 추정 변환
            try:
                out.append({k: getattr(r, k) for k in dir(r) if not k.startswith("_") and not callable(getattr(r, k))})
            except Exception:
                try:
                    out.append(dict(r._mapping))  # Row
                except Exception:
                    pass
    return out

def _safe_query(db: Session, sql: str, params: dict | None = None) -> list[dict]:
    try:
        res = db.execute(text(sql), params or {})
        # sqlite일 때 Row → dict 변환
        return [dict(row._mapping) for row in res]
    except Exception:
        return []

# --- Endpoints ----------------------------------------------------------------

@router.get("/minimum_wage", response_model=List[MinimumWageItem], summary="List minimum wage rows")
def list_minimum_wage(db: Session = Depends(get_db)):
    # 1) ORM 경로(모델이 있으면)
    if MinimumWageHistory is not None:
        try:
            stmt = select(MinimumWageHistory).order_by(desc(MinimumWageHistory.year))
            rows = db.execute(stmt).scalars().all()
            return [
                MinimumWageItem(
                    year=getattr(r, "year"),
                    hourly=getattr(r, "hourly", getattr(r, "amount", 0)),
                    monthly_209h=getattr(r, "monthly_209h", None),
                    notice_no=getattr(r, "notice_no", None),
                    notice_date=getattr(r, "notice_date", None),
                    source_url=getattr(r, "source_url", None),
                ) for r in rows
            ]
        except Exception:
            pass  # 폴백으로 진행

    # 2) SQL 폴백 (테이블명/컬럼명은 기존 로그 기준으로 우선 시도)
    sql_try = [
        # knowledge_core 마이그레이션 기준
        """SELECT year, hourly, monthly_209h, notice_no, notice_date, source_url
           FROM minimum_wage_history ORDER BY year DESC""",
        # 과거 스키마(혹시 amount, unit만 있을 경우)
        """SELECT year,
                  COALESCE(hourly, amount) AS hourly,
                  monthly_209h, notice_no, notice_date, source_url
           FROM minimum_wage_history ORDER BY year DESC""",
    ]
    for s in sql_try:
        rows = _safe_query(db, s)
        if rows:
            return [
                MinimumWageItem(
                    year=int(r.get("year")),
                    hourly=int(r.get("hourly") or r.get("amount") or 0),
                    monthly_209h=(int(r["monthly_209h"]) if r.get("monthly_209h") is not None else None),
                    notice_no=r.get("notice_no"),
                    notice_date=r.get("notice_date"),
                    source_url=r.get("source_url"),
                ) for r in rows
            ]
    # 아무 것도 없으면 빈 배열(500 방지)
    return []

@router.get("/holidays/{year}", response_model=List[HolidayItem], summary="List holidays for a year")
def list_holidays(year: int, db: Session = Depends(get_db)):
    if Holiday is not None:
        try:
            # 일반적으로 date가 'YYYY-MM-DD' 문자열이라고 가정
            stmt = select(Holiday).where(Holiday.date.like(f"{year}-%")).order_by(Holiday.date.asc())
            rows = db.execute(stmt).scalars().all()
            return [
                HolidayItem(
                    date=getattr(r, "date"),
                    name=getattr(r, "name"),
                    type=getattr(r, "type", None),
                    is_public=getattr(r, "is_public", True),
                    source_ref=getattr(r, "source_ref", None),
                ) for r in rows
            ]
        except Exception:
            pass

    # SQL 폴백 (holiday / holidays 양쪽 테이블명 시도)
    sql_try = [
        """SELECT date, name, type, is_public, source_ref
           FROM holidays
           WHERE date LIKE :prefix
           ORDER BY date ASC""",
        """SELECT date, name, type, is_public, source_ref
           FROM holiday
           WHERE date LIKE :prefix
           ORDER BY date ASC""",
    ]
    for s in sql_try:
        rows = _safe_query(db, s, {"prefix": f"{year}-%"})
        if rows:
            out = []
            for r in rows:
                out.append(HolidayItem(
                    date=str(r.get("date")),
                    name=str(r.get("name")),
                    type=r.get("type"),
                    is_public=bool(r.get("is_public")) if r.get("is_public") is not None else True,
                    source_ref=r.get("source_ref"),
                ))
            return out
    return []

@router.get("/policy_bulletins", response_model=List[PolicyBulletinItem], summary="List policy bulletins")
def list_policy_bulletins(db: Session = Depends(get_db)):
    if PolicyBulletin is not None:
        try:
            stmt = select(PolicyBulletin).order_by(desc(getattr(PolicyBulletin, "effective_date", None)))
            rows = db.execute(stmt).scalars().all()
            return [
                PolicyBulletinItem(
                    id=str(getattr(r, "id")),
                    title=getattr(r, "title"),
                    effective_date=getattr(r, "effective_date", None),
                    audience=getattr(r, "audience", None),
                    category=getattr(r, "category", None),
                    summary_md=getattr(r, "summary_md", None),
                    law_id=getattr(r, "law_id", None),
                    article_no=getattr(r, "article_no", None),
                    source_url=getattr(r, "source_url", None),
                    tags=getattr(r, "tags", None),
                ) for r in rows
            ]
        except Exception:
            pass

    sql_try = [
        """SELECT id, title, effective_date, audience, category, summary_md, law_id, article_no, source_url, tags
           FROM policy_bulletin
           ORDER BY COALESCE(effective_date, '') DESC, id DESC""",
        """SELECT id, title, effective_date, audience, category, summary_md, law_id, article_no, source_url, tags
           FROM policy_bulletins
           ORDER BY COALESCE(effective_date, '') DESC, id DESC""",
    ]
    for s in sql_try:
        rows = _safe_query(db, s)
        if rows:
            return [
                PolicyBulletinItem(
                    id=str(r.get("id")),
                    title=str(r.get("title")),
                    effective_date=r.get("effective_date"),
                    audience=r.get("audience"),
                    category=r.get("category"),
                    summary_md=r.get("summary_md"),
                    law_id=r.get("law_id"),
                    article_no=r.get("article_no"),
                    source_url=r.get("source_url"),
                    tags=r.get("tags"),
                ) for r in rows
            ]
    return []

@router.get("/interpretations", response_model=List[InterpretationItem], summary="List admin interpretations")
def list_interpretations(db: Session = Depends(get_db)):
    if AdminInterpretation is not None:
        try:
            stmt = select(AdminInterpretation).order_by(desc(getattr(AdminInterpretation, "answered_at", None)))
            rows = db.execute(stmt).scalars().all()
            return [
                InterpretationItem(
                    interp_id=str(getattr(r, "interp_id")),
                    title=getattr(r, "title"),
                    asked_at=getattr(r, "asked_at", None),
                    answered_at=getattr(r, "answered_at", None),
                    question=getattr(r, "question", None),
                    answer=getattr(r, "answer", None),
                    law_id=getattr(r, "law_id", None),
                    article_no=getattr(r, "article_no", None),
                    source_url=getattr(r, "source_url", None),
                    tags=getattr(r, "tags", None),
                ) for r in rows
            ]
        except Exception:
            pass

    sql_try = [
        """SELECT interp_id, title, asked_at, answered_at, question, answer, law_id, article_no, source_url, tags
           FROM admin_interpretation
           ORDER BY COALESCE(answered_at, asked_at) DESC""",
        """SELECT interp_id, title, asked_at, answered_at, question, answer, law_id, article_no, source_url, tags
           FROM admin_interpretations
           ORDER BY COALESCE(answered_at, asked_at) DESC""",
    ]
    for s in sql_try:
        rows = _safe_query(db, s)
        if rows:
            return [
                InterpretationItem(
                    interp_id=str(r.get("interp_id")),
                    title=str(r.get("title")),
                    asked_at=r.get("asked_at"),
                    answered_at=r.get("answered_at"),
                    question=r.get("question"),
                    answer=r.get("answer"),
                    law_id=r.get("law_id"),
                    article_no=r.get("article_no"),
                    source_url=r.get("source_url"),
                    tags=r.get("tags"),
                ) for r in rows
            ]
    return []
