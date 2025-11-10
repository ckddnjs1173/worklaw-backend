import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# .env 로드
load_dotenv()

# ✅ Alembic과 공용으로 사용할 DB URL (기본: 현재 디렉터리 worklaw.db)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./worklaw.db")

# ✅ SQLite 안전 옵션
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Alembic autogenerate 타겟
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
