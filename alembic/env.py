from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# === 프로젝트 패스 및 메타데이터 준비 =========================
# 프로젝트 루트 기준으로 import 가능하게 경로 추가
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # worklaw-backend
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# .env 로드 및 DATABASE_URL 적용
from dotenv import load_dotenv
load_dotenv()

# alembic.ini의 sqlalchemy.url 기본값을 .env의 DATABASE_URL로 오버라이드
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# ✅ ORM 메타데이터(Target)
from database.connection import Base
# 모델 모듈들을 import 해야 mapper가 로드됨 (autogenerate에 필수)
import models.wage  # noqa: F401
import models.law   # noqa: F401

target_metadata = Base.metadata
# ============================================================

def run_migrations_offline() -> None:
    """오프라인 모드: DB 연결 없이 스크립트 생성"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,      # 컬럼 타입 변경 감지
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드: 실제 DB 연결 후 실행"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),  # type: ignore[arg-type]
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
