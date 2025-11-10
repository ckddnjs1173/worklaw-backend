from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status, Depends

router = APIRouter(prefix="/admin/sync", tags=["admin:sync"])

# --- 간단 관리자 인증 (헤더만 확인; 프로젝트 보안 규칙에 맞게 강화 가능) ----
def require_admin(authorization: Optional[str] = Header(None)):
    # FastAPI가 호출 시점에 문자열로 주입해줍니다.
    if not authorization or not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: missing or invalid Authorization header",
        )
    # TODO: JWT 서명/만료 검증 등 실제 로직 연결
    return True

# --- 공통 응답 포맷 -----------------------------------------------------------
def ok(job: str, items_upserted: int = 0, note: str = "noop"):
    return {
        "job": job,
        "status": "ok",
        "items_upserted": items_upserted,
        "finished_at": datetime.utcnow().isoformat() + "Z",
        "note": note,
    }

# --- 동기화 엔드포인트 (스텁 / 이후 실제 ETL로 교체) -------------------------
# 의존성은 반드시 Depends(require_admin) 로 주입하세요.
@router.post("/minwage", summary="Sync minimum wage (stub)")
def sync_minwage(_: bool = Depends(require_admin)):
    # TODO: 실제 ETL 로직으로 교체
    return ok("minwage", items_upserted=0, note="stub")

@router.post("/holiday_api", summary="Sync holidays (stub)")
def sync_holiday(_: bool = Depends(require_admin)):
    # TODO: 실제 공휴일 API 연동
    return ok("holiday_api", items_upserted=0, note="stub")

@router.post("/law_api", summary="Sync laws (stub)")
def sync_law(_: bool = Depends(require_admin)):
    # TODO: 국가법령정보센터 OpenAPI 연동
    return ok("law_api", items_upserted=0, note="stub")

@router.post("/interpretation_api", summary="Sync admin interpretations (stub)")
def sync_interpretation(_: bool = Depends(require_admin)):
    # TODO: 행정해석 수집 연동
    return ok("interpretation_api", items_upserted=0, note="stub")

@router.post("/moel_notice", summary="Sync MOEL notices (stub)")
def sync_moel_notice(_: bool = Depends(require_admin)):
    # TODO: 고용노동부 공지/보도자료 수집
    return ok("moel_notice", items_upserted=0, note="stub")
