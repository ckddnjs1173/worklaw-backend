from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from datetime import datetime
from database.connection import Base  # 기존 Base 사용

# --- Source & Job (수집원/작업 추적) ---
class Source(Base):
    __tablename__ = "sources"
    source_key = Column(String, primary_key=True)       # law_api / moel_notice / holiday_api / minwage / interpretation_api
    provider = Column(String, nullable=False)
    api_url = Column(String, nullable=True)
    license = Column(String, nullable=True)
    last_checked_at = Column(String, nullable=True)

class SyncJob(Base):
    __tablename__ = "sync_jobs"
    job_id = Column(String, primary_key=True)
    source_key = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")          # running/success/fail
    items_upserted = Column(Integer, default=0)
    checksum = Column(String, nullable=True)
    log = Column(Text, nullable=True)

# --- Staging (원본 저장) ---
class StagingRaw(Base):
    __tablename__ = "staging_raw"
    id = Column(String, primary_key=True)
    source_key = Column(String, nullable=False)
    natural_id = Column(String, nullable=False)         # 외부 원천의 natural key (예: notice_no, interpretation_id)
    payload = Column(Text, nullable=False)              # JSON 문자열
    checksum = Column(String, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("source_key", "natural_id", name="uq_staging_source_natural"),)

# --- Must 1: 법령/버전/조문 캐시 ---
class Law(Base):
    __tablename__ = "laws"
    law_id = Column(String, primary_key=True)           # ex) KOR_LAW_근로기준법
    law_name_kr = Column(String, nullable=False)
    law_name_en = Column(String, nullable=True)
    status = Column(String, nullable=True)              # current/obsolete

class LawVersion(Base):
    __tablename__ = "law_versions"
    id = Column(String, primary_key=True)
    law_id = Column(String, nullable=False)
    version_no = Column(String, nullable=False)         # ex) 2025-01-01
    effective_from = Column(String, nullable=True)
    effective_to = Column(String, nullable=True)
    source_ref = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint("law_id", "version_no", name="uq_law_id_version_no"),)

class LawArticle(Base):
    __tablename__ = "law_articles"
    id = Column(String, primary_key=True)
    law_id = Column(String, nullable=False)
    version_no = Column(String, nullable=False)
    article_no = Column(String, nullable=False)
    title = Column(String, nullable=True)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    updated_at = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint("law_id", "version_no", "article_no", name="uq_law_ver_article"),)

# --- Must 2: 최저임금 이력 ---
class MinimumWageHistory(Base):
    __tablename__ = "minimum_wage_history"
    __table_args__ = {"extend_existing": True}  # ← 추가
    year = Column(Integer, primary_key=True)
    hourly = Column(Integer, nullable=False)            # 원 단위
    monthly_209h = Column(Integer, nullable=True)       # 209시간 환산
    notice_no = Column(String, nullable=True)
    notice_date = Column(String, nullable=True)         # YYYY-MM-DD
    source_url = Column(String, nullable=True)

# --- Must 3: 법령해석(행정해석) ---
class AdminInterpretation(Base):
    __tablename__ = "admin_interpretations"
    interp_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    asked_at = Column(String, nullable=True)
    answered_at = Column(String, nullable=True)
    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    law_id = Column(String, nullable=True)
    article_no = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    tags = Column(String, nullable=True)

# --- Must 4: 공휴일 ---
class Holiday(Base):
    __tablename__ = "holidays"
    date = Column(String, primary_key=True)             # YYYY-MM-DD
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)                # public/anniversary
    is_public = Column(Boolean, default=True)
    source_ref = Column(String, nullable=True)

# --- Must 5: 정책 공지/고시 메타(관리 공지) ---
class PolicyBulletin(Base):
    __tablename__ = "policy_bulletins"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    effective_date = Column(String, nullable=True)
    audience = Column(String, nullable=True)            # worker/employer/both
    category = Column(String, nullable=True)
    summary_md = Column(Text, nullable=True)
    law_id = Column(String, nullable=True)
    article_no = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    tags = Column(String, nullable=True)
