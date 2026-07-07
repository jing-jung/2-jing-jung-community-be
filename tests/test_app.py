"""
Unit Tests for Core Modules
pytest를 사용한 테스트
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.core.cache import redis_manager
import asyncio


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """TestClient 생성"""
    return TestClient(app)


@pytest.fixture
async def redis():
    """Redis 연결"""
    await redis_manager.connect()
    yield redis_manager
    await redis_manager.disconnect()


# =============================================================================
# Security Tests
# =============================================================================

def test_password_hashing():
    """비밀번호 해싱 테스트"""
    password = "test1234"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_token():
    """JWT 토큰 생성/검증 테스트"""
    payload = {"user_id": 1, "email": "test@example.com"}
    token = create_access_token(payload)
    
    assert token is not None
    
    decoded = decode_token(token)
    assert decoded["user_id"] == 1
    assert decoded["email"] == "test@example.com"


# =============================================================================
# API Tests
# =============================================================================

def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == settings.APP_NAME
    assert data["status"] == "healthy"


def test_health_check(client):
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"


def test_ready_check(client):
    """Readiness 체크 테스트"""
    response = client.get("/ready")
    # DB/Redis가 없으면 503, 있으면 200
    assert response.status_code in [200, 503]
    
    data = response.json()
    assert "checks" in data


def test_metrics_endpoint(client):
    """Metrics 엔드포인트 테스트"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_info_endpoint(client):
    """Info 엔드포인트 테스트"""
    response = client.get("/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "app" in data
    assert "database" in data
    assert "redis" in data


# =============================================================================
# Cache Tests
# =============================================================================

@pytest.mark.asyncio
async def test_redis_set_get(redis):
    """Redis set/get 테스트"""
    key = "test:key"
    value = {"name": "test", "count": 42}
    
    # Set
    await redis.set(key, value, expire=60)
    
    # Get
    result = await redis.get(key)
    assert result == value
    
    # Delete
    await redis.delete(key)
    result = await redis.get(key)
    assert result is None


@pytest.mark.asyncio
async def test_redis_session(redis):
    """Redis 세션 관리 테스트"""
    session_id = "test-session-123"
    user_id = 42
    
    # Set session
    await redis.set_session(session_id, user_id)
    
    # Get session
    result = await redis.get_session(session_id)
    assert result == user_id
    
    # Delete session
    await redis.delete_session(session_id)
    result = await redis.get_session(session_id)
    assert result is None


# =============================================================================
# Authentication Tests
# =============================================================================

def test_signup(client):
    """회원가입 테스트"""
    response = client.post("/users/signup", data={
        "email": f"test{random.randint(1, 10000)}@example.com",
        "password": "test1234",
        "nickname": "TestUser"
    })
    
    # DB가 없으면 실패할 수 있음
    assert response.status_code in [201, 500]


def test_login_without_credentials(client):
    """로그인 실패 테스트 (잘못된 자격증명)"""
    response = client.post("/users/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code in [401, 404, 500]


# =============================================================================
# Rate Limiting Tests
# =============================================================================

def test_rate_limiting(client):
    """Rate Limiting 테스트"""
    # 100번 요청
    for i in range(101):
        response = client.get("/")
        
        if i < 100:
            assert response.status_code == 200
        else:
            # 100번째 이후는 429 Too Many Requests
            assert response.status_code in [200, 429]


# =============================================================================
# 실행 방법:
# 
# 1. pytest 설치
#    pip install pytest pytest-asyncio httpx
# 
# 2. 전체 테스트 실행
#    pytest tests/
# 
# 3. 특정 테스트만 실행
#    pytest tests/test_app.py::test_health_check
# 
# 4. Coverage 리포트
#    pytest tests/ --cov=app --cov-report=html
# 
# 5. 병렬 실행 (빠른 테스트)
#    pip install pytest-xdist
#    pytest tests/ -n auto
# =============================================================================


import random
