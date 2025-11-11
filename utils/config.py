# utils/config.py
from __future__ import annotations
import os, json
from typing import List

def _require(key: str, default: str | None = None) -> str:
    val = os.getenv(key, default)
    if val is None:
        raise RuntimeError(f"Missing required env: {key}")
    return val

def _parse_cors(v: str | None, fallback: List[str]) -> List[str]:
    if not v:
        return fallback
    v = v.strip()
    # JSON 배열 문자열(["http://..."])을 우선 지원
    if v.startswith("["):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
    # 콤마로 구분된 문자열도 허용
    return [s.strip() for s in v.split(",") if s.strip()]

# ⚠️ 로컬에서만 .env 적용, 호스팅(Railway 등)에서는 절대 덮어쓰지 않음
if not os.getenv("RAILWAY_ENVIRONMENT"):
    try:
        from dotenv import load_dotenv  # 선택적 의존성
        load_dotenv(override=False)
    except Exception:
        pass

class Settings:
    ENV: str
    HOST: str
    PORT: int
    DATABASE_URL: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD_HASH: str
    JWT_SECRET: str
    JWT_EXPIRE_MIN: int
    CORS_ORIGINS: List[str]
    ENABLE_HSTS: bool

    def __init__(self) -> None:
        # Railway Variables가 있으면 그것을 신뢰(로컬 기본: dev)
        self.ENV = os.getenv("ENV") or os.getenv("APP_ENV") or "dev"
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))

        self.DATABASE_URL        = _require("DATABASE_URL", "sqlite:///./worklaw.db")
        self.ADMIN_USERNAME      = _require("ADMIN_USERNAME", "admin")
        self.ADMIN_PASSWORD_HASH = _require("ADMIN_PASSWORD_HASH", "")
        self.JWT_SECRET          = _require("JWT_SECRET", "change-me")
        self.JWT_EXPIRE_MIN      = int(os.getenv("JWT_EXPIRE_MIN", "120"))

        # JSON 배열 또는 콤마 구분 문자열 모두 지원
        cors_raw = os.getenv(
            "CORS_ORIGINS",
            '["http://localhost:3000","https://worklaw-frontend-staging.vercel.app"]'
        )
        self.CORS_ORIGINS = _parse_cors(
            cors_raw,
            ["http://localhost:3000", "https://worklaw-frontend-staging.vercel.app"],
        )

        # prod 에서만 true 권장
        self.ENABLE_HSTS = os.getenv("ENABLE_HSTS", "false").lower() == "true"

settings = Settings()
