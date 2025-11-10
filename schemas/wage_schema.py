# worklaw-backend/schemas/wage_schema.py

from pydantic import BaseModel, Field

class MinimumWageIn(BaseModel):
    year: int = Field(ge=2010, le=2100)
    amount: int = Field(ge=0)
    unit: str = "KRW/hour"

class MinimumWageUpdate(BaseModel):
    amount: int | None = Field(default=None, ge=0)
    unit: str | None = None

class MinimumWageOut(BaseModel):
    year: int
    minimum_wage: int
    unit: str = "KRW/hour"
    class Config:
        from_attributes = True

class MinimumWageRow(BaseModel):
    year: int
    amount: int
    unit: str

class MinimumWageHistoryRow(BaseModel):
    year: int
    old_amount: int | None = None
    new_amount: int | None = None
    old_unit: str | None = None
    new_unit: str | None = None
    action: str
    changed_by: str
    changed_at: str
