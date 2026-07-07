"""
Dependency Injection Utilities
FastAPI Dependencies for Authentication, Rate Limiting, etc.
"""
from fastapi import Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.cache import redis_manager
from app.core.security import decode_token, check_rate_limit
from app.core.logging import log


async def get_current_user_id(
    request: Request,
    db: Session = Depends(get_db)
) -> int:
    """
    현재 로그인한 사용자 ID 조회 (세션 기반)
    쿠키에서 session_id를 읽어 검증
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        log.warning("No session_id in cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Redis에서 세션 조회
    user_id = await redis_manager.get_session(session_id)
    
    if not user_id:
        # Redis에 없으면 DB에서 조회 (fallback)
        from sqlalchemy import text
        result = db.execute(
            text("SELECT data FROM sessions WHERE session_id = :session_id"),
            {"session_id": session_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        user_id = int(result.data)
        # Redis에 캐싱
        await redis_manager.set_session(session_id, user_id)
    
    return user_id


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[int]:
    """
    선택적 인증 (로그인하지 않아도 됨)
    """
    try:
        return await get_current_user_id(request, db)
    except HTTPException:
        return None


async def get_current_user_from_token(
    authorization: Optional[str] = Header(None)
) -> int:
    """
    JWT Token 기반 인증
    Header: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return user_id


class RateLimitDependency:
    """
    Rate Limiting Dependency
    
    사용 예:
    @router.get("/api/data", dependencies=[Depends(RateLimitDependency(max_requests=10, window=60))])
    """
    
    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
    
    async def __call__(self, request: Request):
        await check_rate_limit(request)
