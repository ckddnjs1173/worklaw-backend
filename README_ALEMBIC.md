# Alembic 마이그레이션 가이드

## 개요
- Alembic으로 DDL 스키마 버전 관리합니다.
- 모델 정의는 `models/`가 단일 `Base` (`database/connection.py`)를 사용.
- autogenerate 모드로 현재 ORM ↔ DB 차이를 자동 반영합니다.

## 필수: 환경 변수
- `DATABASE_URL` (선택): 기본값 `sqlite:///./worklaw.db`
- `.env`에 설정하면 Alembic과 앱 모두 동일한 DB를 사용합니다.

## 최초 초기화 & 초기 마이그레이션 생성
```powershell
cd worklaw-backend

# (선택) 기존 SQLite 초기화
Remove-Item .\worklaw.db -ErrorAction SilentlyContinue

# 의존성 설치
pip install -r requirements.txt

# Alembic 디렉터리 없으면(최초 한 번) 생성
if (!(Test-Path .\alembic)) { alembic init alembic }

# 초기 리비전 자동 생성 (모델 기준)
alembic revision --autogenerate -m "init schema"

# DB에 적용
alembic upgrade head
