# worklaw-backend/models/law.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, JSON
from datetime import datetime
from database.connection import Base

class Law(Base):
    __tablename__ = "law"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True, unique=True)  # 법령명(예: 근로기준법)
    mst: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)  # 법령 master seq (있으면 저장)
    law_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)  # 법령ID
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # 현행/폐지 등
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    articles: Mapped[list["LawArticle"]] = relationship("LawArticle", back_populates="law", cascade="all, delete-orphan")

class LawArticle(Base):
    __tablename__ = "law_article"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    law_id_fk: Mapped[int] = mapped_column(Integer, ForeignKey("law.id"), index=True)
    article_no: Mapped[str] = mapped_column(String(50), index=True)  # 제1조, 제2조 등 조문 번호 문자열
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 조문 표제
    current_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # 현행 조문 본문 (가공 텍스트)
    current_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 원본 JSON 보존
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    law: Mapped["Law"] = relationship("Law", back_populates="articles")
    versions: Mapped[list["LawArticleVersion"]] = relationship("LawArticleVersion", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("law_id_fk", "article_no", name="uq_law_article_unique"),
    )

class LawArticleVersion(Base):
    __tablename__ = "law_article_version"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id_fk: Mapped[int] = mapped_column(Integer, ForeignKey("law_article.id"), index=True)
    effective_date: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 시행일(YYYYMMDD)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    article: Mapped["LawArticle"] = relationship("LawArticle", back_populates="versions")
