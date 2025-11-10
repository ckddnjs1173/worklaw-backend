# worklaw-backend/routers/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from utils.security import authenticate_admin, create_access_token, decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginIn(BaseModel):
    username: str
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn):
    if not authenticate_admin(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=payload.username, role="admin")
    return {"access_token": token, "expires_in_minutes": 120}

# 의존성: 관리자 인증
def require_admin(token: str = Depends(lambda authorization: authorization)):
    # FastAPI에서 Authorization 헤더를 직접 받기 위한 람다
    # 실제 의존성은 아래 함수로 대체하기 위해 커스텀 처리
    return token

from fastapi import Header

def get_current_admin(authorization: str = Header(default="")):
    # Expect: "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload  # {"sub": "...", "role": "admin", ...}
