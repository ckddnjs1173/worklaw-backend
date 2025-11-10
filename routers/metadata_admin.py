# worklaw-backend/routers/metadata_admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from database.connection import get_db
from models.wage import MinimumWage, MinimumWageHistory
from schemas.wage_schema import (
    MinimumWageIn, MinimumWageUpdate, MinimumWageRow, MinimumWageHistoryRow
)
from routers.auth import get_current_admin  # ✅ JWT 의존성

router = APIRouter(prefix="/admin/metadata", tags=["Admin: Metadata"])

@router.get("/minimum-wage", response_model=list[MinimumWageRow])
def list_minimum_wage(_: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = db.query(MinimumWage).order_by(MinimumWage.year.asc()).all()
    return [{"year": r.year, "amount": r.amount, "unit": r.unit} for r in rows]

@router.post("/minimum-wage", response_model=MinimumWageRow, status_code=201)
def create_minimum_wage(payload: MinimumWageIn, _: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    exists = db.query(MinimumWage).filter(MinimumWage.year == payload.year).first()
    if exists:
        raise HTTPException(status_code=409, detail="Year already exists")
    row = MinimumWage(year=payload.year, amount=payload.amount, unit=payload.unit)
    db.add(row)
    db.commit()

    hist = MinimumWageHistory(
        year=payload.year, old_amount=None, new_amount=payload.amount,
        old_unit=None, new_unit=payload.unit, action="CREATE", changed_by="admin",
    )
    db.add(hist)
    db.commit()
    return {"year": row.year, "amount": row.amount, "unit": row.unit}

@router.put("/minimum-wage/{year}", response_model=MinimumWageRow)
def update_minimum_wage(
    year: int = Path(..., ge=2010, le=2100),
    payload: MinimumWageUpdate = None,
    _: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(MinimumWage).filter(MinimumWage.year == year).first()
    if not row:
        raise HTTPException(status_code=404, detail="Year not found")

    old_amount, old_unit = row.amount, row.unit
    if payload.amount is not None:
        row.amount = payload.amount
    if payload.unit is not None:
        row.unit = payload.unit
    db.commit()

    hist = MinimumWageHistory(
        year=year, old_amount=old_amount, new_amount=row.amount,
        old_unit=old_unit, new_unit=row.unit, action="UPDATE", changed_by="admin",
    )
    db.add(hist)
    db.commit()

    return {"year": row.year, "amount": row.amount, "unit": row.unit}

@router.delete("/minimum-wage/{year}", status_code=204)
def delete_minimum_wage(year: int = Path(..., ge=2010, le=2100), _: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    row = db.query(MinimumWage).filter(MinimumWage.year == year).first()
    if not row:
        raise HTTPException(status_code=404, detail="Year not found")

    hist = MinimumWageHistory(
        year=year, old_amount=row.amount, new_amount=None,
        old_unit=row.unit, new_unit=None, action="DELETE", changed_by="admin",
    )
    db.add(hist)
    db.delete(row)
    db.commit()
    return

@router.get("/minimum-wage/{year}/history", response_model=list[MinimumWageHistoryRow])
def history_minimum_wage(year: int = Path(..., ge=2010, le=2100), _: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = (
        db.query(MinimumWageHistory)
        .filter(MinimumWageHistory.year == year)
        .order_by(MinimumWageHistory.changed_at.desc())
        .all()
    )
    return [
        {
            "year": r.year,
            "old_amount": r.old_amount,
            "new_amount": r.new_amount,
            "old_unit": r.old_unit,
            "new_unit": r.new_unit,
            "action": r.action,
            "changed_by": r.changed_by,
            "changed_at": r.changed_at.isoformat(),
        }
        for r in rows
    ]
