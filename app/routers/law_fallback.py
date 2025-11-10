import os
from fastapi import APIRouter, Query

router = APIRouter(prefix="/law", tags=["law-staging"])

@router.get("/list")
def law_list(q: str = Query(..., min_length=1)):
    """
    STAGING 전용: 외부 API/DB 장애가 있어도 200으로 안전하게 빈 배열 반환.
    운영/개발에서는 main.py에서 이 라우터를 include하지 않음.
    """
    # 원래 구현을 여기에 try/except로 감싸도 되지만,
    # 스테이징 안정화를 위해 무조건 200+빈 배열을 돌려 FE를 살려둔다.
    return {"items": []}
