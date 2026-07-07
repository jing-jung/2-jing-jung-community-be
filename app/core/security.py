"""
Security Utilities
JWT, Password Hashing, Rate Limiting
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Request
from app.core.config import settings
from app.core.logging import log
import time
from collections import defaultdict
import threading


# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT Token
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """JWT Access Token 생성"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """JWT Refresh Token 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """JWT Token 디코드"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        log.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Rate Limiting (In-Memory)
class RateLimiter:
    """
    간단한 In-Memory Rate Limiter
    프로덕션에서는 Redis 기반으로 교체 권장
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_PERIOD
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Rate limit 체크
        :param identifier: IP 주소 또는 User ID
        :return: 허용 여부
        """
        now = time.time()
        
        with self.lock:
            # 만료된 요청 제거
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < self.window
            ]
            
            # 요청 수 체크
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # 새 요청 추가
            self.requests[identifier].append(now)
            return True
    
    def get_remaining(self, identifier: str) -> int:
        """남은 요청 수 반환"""
        now = time.time()
        
        with self.lock:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < self.window
            ]
            
            return max(0, self.max_requests - len(self.requests[identifier]))


# 전역 Rate Limiter 인스턴스
rate_limiter = RateLimiter()


async def check_rate_limit(request: Request):
    """
    Rate Limit 미들웨어
    FastAPI Dependency로 사용
    """
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        log.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    
    return True


# CORS 설정 검증
def validate_origin(origin: str) -> bool:
    """CORS Origin 검증"""
    if settings.ENVIRONMENT == "development":
        return True
    
    return origin in settings.CORS_ORIGINS
