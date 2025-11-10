from pydantic import BaseModel
from typing import Optional, Literal, List, Dict, Any

Audience = Literal["worker","employer","both"]

class MinimumWageRow(BaseModel):
    year: int
    hourly: int
    monthly_209h: Optional[int] = None
    notice_no: Optional[str] = None
    notice_date: Optional[str] = None
    source_url: Optional[str] = None

class PolicyBulletinIn(BaseModel):
    id: str
    title: str
    effective_date: Optional[str] = None
    audience: Optional[Audience] = None
    category: Optional[str] = None
    summary_md: Optional[str] = None
    law_id: Optional[str] = None
    article_no: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[str] = None

class HolidayRow(BaseModel):
    date: str
    name: str
    type: Optional[str] = "public"
    is_public: Optional[bool] = True
    source_ref: Optional[str] = None

class InterpretationRow(BaseModel):
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

class UploadPayload(BaseModel):
    rows: List[Dict[str, Any]]
