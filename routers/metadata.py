# worklaw-backend/routers/metadata.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from models.wage import MinimumWage
from schemas.wage_schema import MinimumWageOut

router = APIRouter(prefix="/metadata", tags=["Metadata"])

@router.get("/minimum-wage", response_model=MinimumWageOut)
def get_minimum_wage(
    year: int = Query(..., ge=2010, le=2100, description="기준 연도 (예: 2025)"),
    db: Session = Depends(get_db),
):
    """
    DB에서 해당 연도의 최저임금(원/시간)을 반환합니다.
    없는 연도라면, DB에 저장된 최근 연도의 값을 반환합니다.
    """
    record = db.query(MinimumWage).filter(MinimumWage.year == year).first()
    if record:
        return {"year": record.year, "minimum_wage": record.amount, "unit": record.unit}

    # 해당 연도가 없으면 최신 연도로 fallback
    latest = db.query(MinimumWage).order_by(MinimumWage.year.desc()).first()
    if latest:
        return {
            "year": latest.year,
            "minimum_wage": latest.amount,
            "unit": latest.unit,
        }

    # DB가 비어있는 경우 (이론상 시드 로직으로 거의 발생하지 않음)
    return {"year": year, "minimum_wage": 0, "unit": "KRW/hour"}
