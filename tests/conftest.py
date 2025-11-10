# -*- coding: utf-8 -*-
"""
테스트 공용 설정:
- 프로젝트 루트(sys.path) 주입 → 'database', 'models', 'main' 임포트 가능
- 테스트 전용 DB (sqlite:///./test_worklaw.db) 사용
- 관리자 계정 환경변수 주입 (bcrypt로 해시 생성; passlib 미사용)
"""
import os
import sys
import asyncio
import pytest
import bcrypt

# ---- 1) 프로젝트 루트를 sys.path에 추가 ----
# tests/ 기준 상위가 worklaw-backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ---- 2) 테스트용 환경변수 (가장 먼저 설정) ----
os.environ["DATABASE_URL"] = "sqlite:///./test_worklaw.db"
os.environ["ADMIN_USERNAME"] = "admin"

# 관리자 비번: admin123!  → bcrypt 표준으로 해시 생성 (passlib 사용 안 함)
_admin_pw = "admin123!".encode("utf-8")
_admin_hash = bcrypt.hashpw(_admin_pw, bcrypt.gensalt(rounds=12)).decode("utf-8")
os.environ["ADMIN_PASSWORD_HASH"] = _admin_hash

# JWT 환경 (앱에서 읽어 사용)
os.environ["JWT_SECRET"] = "test-secret"
os.environ["JWT_EXPIRE_MIN"] = "60"

# ---- 3) 이제 애플리케이션 모듈들을 import ----
from database.connection import Base, engine, SessionLocal  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from main import app as fastapi_app  # noqa: E402

# (선택) 필요 시 모델 직접 접근
# from models.wage import MinimumWage  # noqa: E402
# from models.law import Law, LawArticle  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """pytest-asyncio: 세션 스코프 이벤트루프"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def _prepare_db():
    """테스트 세션 시작 시 깨끗한 테스트 DB를 만들고, 끝에 제거."""
    try:
        if os.path.exists("test_worklaw.db"):
            os.remove("test_worklaw.db")
    except Exception:
        pass

    # ORM 스키마 생성
    Base.metadata.create_all(bind=engine)

    yield

    # 종료 시 테스트 DB 제거
    try:
        if os.path.exists("test_worklaw.db"):
            os.remove("test_worklaw.db")
    except Exception:
        pass


@pytest.fixture
def app() -> FastAPI:
    """FastAPI 앱 인스턴스 반환"""
    return fastapi_app


@pytest.fixture
def db():
    """직접 DB 작업이 필요할 때 사용할 세션"""
    _db = SessionLocal()
    try:
        yield _db
    finally:
        _db.close()
