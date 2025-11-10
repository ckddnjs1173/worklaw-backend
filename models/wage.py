# worklaw-backend/models/wage.py

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime
from datetime import datetime
from database.connection import Base

class MinimumWage(Base):
    __tablename__ = "minimum_wage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 원/시간
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="KRW/hour")

class MinimumWageHistory(Base):
    __tablename__ = "minimum_wage_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    old_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    old_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    action: Mapped[str] = mapped_column(String(20))  # CREATE / UPDATE / DELETE
    changed_by: Mapped[str] = mapped_column(String(100), default="admin")
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
