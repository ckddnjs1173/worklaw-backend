import os
from typing import List

def get_env(key: str, default: str | None = None) -> str:
    val = os.getenv(key, default)
    if val is None:
        raise RuntimeError(f"Missing required env: {key}")
    return val

def parse_csv_env(key: str, default: str = "") -> List[str]:
    raw = os.getenv(key, default)
    return [x.strip() for x in raw.split(",") if x.strip()]

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
        self.ENV = os.getenv("ENV", "dev")
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
        self.DATABASE_URL = get_env("DATABASE_URL", "sqlite:///./worklaw.db")
        self.ADMIN_USERNAME = get_env("ADMIN_USERNAME", "admin")
        self.ADMIN_PASSWORD_HASH = get_env("ADMIN_PASSWORD_HASH", "")
        self.JWT_SECRET = get_env("JWT_SECRET", "change-me")
        self.JWT_EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MIN", "120"))
        self.CORS_ORIGINS = parse_csv_env("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        self.ENABLE_HSTS = os.getenv("ENABLE_HSTS", "false").lower() == "true"

settings = Settings()
