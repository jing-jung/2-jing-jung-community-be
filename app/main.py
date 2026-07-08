"""
Community Platform - Production Ready Backend
고도화된 아키텍처: 캐싱, 로깅, 메트릭, 보안
"""
import os
import json
from typing import Dict
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

# Core Modules
from app.core.config import settings
from app.core.logging import setup_logging, log
from app.core.database import db_manager
from app.core.cache import redis_manager
from app.core.metrics import (
    MetricsMiddleware, get_metrics, app_info, 
    update_db_pool_metrics, update_websocket_connections, record_websocket_message
)

# Routers
from app.routers.routes import router
from app.routers.chat import router as chat_router, init_recommendation_engine

# Models
from app.models import model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    - 시작 시: DB/Redis 연결, 로깅 설정
    - 종료 시: 리소스 정리
    """
    # Startup
    log.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    log.info(f"Environment: {settings.ENVIRONMENT}")
    
    # 로깅 설정
    setup_logging()
    
    # 데이터베이스 초기화
    db_manager.create_tables()
    
    # Redis 연결
    await redis_manager.connect()
    
    # 추천 엔진 초기화 (CSV 로딩)
    await init_recommendation_engine()
    
    # 애플리케이션 정보 메트릭
    app_info.info({
        'version': settings.APP_VERSION,
        'environment': settings.ENVIRONMENT
    })
    
    log.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    log.info("🛑 Shutting down application...")
    
    # Redis 연결 종료
    await redis_manager.disconnect()
    
    # DB 연결 종료
    db_manager.close()
    
    log.info("✅ Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready Community Platform API",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)


class ConnectionManager:
    """WebSocket 연결 관리 (메트릭 수집 포함)"""
    
    def __init__(self):
        self.active_connections: Dict[int, list[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        
        # 메트릭 업데이트
        update_websocket_connections(room_id, 1)
        log.info(f"WebSocket connected - Room: {room_id}, Total: {len(self.active_connections[room_id])}")

    def disconnect(self, room_id: int, websocket: WebSocket):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
            
            # 메트릭 업데이트
            update_websocket_connections(room_id, -1)
            log.info(f"WebSocket disconnected - Room: {room_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_local(self, room_id: int, message: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)
                record_websocket_message(room_id, "sent")


manager = ConnectionManager()


# =============================================================================
# Middlewares (순서 중요!)
# =============================================================================

# 1. Trusted Host (보안)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 프로덕션에서는 실제 도메인으로 제한
    )

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"]
)

# 3. GZip Compression (응답 압축)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. Prometheus Metrics
app.add_middleware(MetricsMiddleware)

# 5. Request ID & Logging
@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    """요청마다 고유 ID 부여 및 로깅"""
    import uuid
    request_id = str(uuid.uuid4())
    
    log.info(f"[{request_id}] {request.method} {request.url.path}")
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# =============================================================================
# Routers
# =============================================================================
app.include_router(router)
app.include_router(chat_router)


# =============================================================================
# WebSocket Endpoint (개선된 버전)
# =============================================================================
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    """실시간 채팅 WebSocket (메트릭 및 로깅 포함)"""
    sender_id = None
    connection_accepted = False

    try:
        # 1. 인증: 세션 토큰 확인
        token = websocket.cookies.get("session_id")

        if not token:
            log.warning(f"WebSocket connection rejected - No session token (room: {room_id})")
            await websocket.close(code=1008)
            return

        # Redis에서 세션 확인 (빠른 조회)
        sender_id = await redis_manager.get_session(token)
        
        if not sender_id:
            # Fallback to DB
            with db_manager.session_scope() as db:
                sql = text("SELECT data FROM sessions WHERE session_id = :session_id")
                result = db.execute(sql, {"session_id": token}).fetchone()

                if not result:
                    log.warning(f"WebSocket connection rejected - Invalid session (room: {room_id})")
                    await websocket.close(code=1008)
                    return

                sender_id = int(result.data)
                # 세션을 Redis에 캐싱
                await redis_manager.set_session(token, sender_id)

        # 2. 참여 권한 확인
        with db_manager.session_scope() as db:
            sql_check = text("SELECT id FROM chat_participants WHERE room_id = :room_id AND user_id = :user_id")
            if not db.execute(sql_check, {"room_id": room_id, "user_id": sender_id}).fetchone():
                log.warning(f"WebSocket connection rejected - User {sender_id} not in room {room_id}")
                await websocket.close(code=1008)
                return

        # 3. 연결 수립
        await manager.connect(room_id, websocket)
        connection_accepted = True

        # 4. 메시지 수신 및 브로드캐스트
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            content = message_data.get("content")

            if content:
                # 메시지 저장
                with db_manager.session_scope() as db:
                    insert_sql = text("""
                        INSERT INTO messages (room_id, sender_id, content, created_at, is_read)
                        VALUES (:room_id, :sender_id, :content, NOW(), 0)
                    """)
                    db.execute(insert_sql, {
                        "room_id": room_id,
                        "sender_id": sender_id,
                        "content": content
                    })

                response_message = {
                    "room_id": room_id,
                    "sender_id": sender_id,
                    "content": content,
                    "created_at": datetime.now().isoformat()
                }

                # 브로드캐스트
                await manager.broadcast_to_local(room_id, json.dumps(response_message))
                
                # 메트릭 기록
                record_websocket_message(room_id, "received")

    except WebSocketDisconnect:
        log.info(f"WebSocket disconnected - Room: {room_id}, User: {sender_id}")
    except Exception as e:
        log.error(f"WebSocket error in room {room_id}: {e}", exc_info=True)
    finally:
        if connection_accepted:
            manager.disconnect(room_id, websocket)


# =============================================================================
# Exception Handlers
# =============================================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "code": "INVALID_INPUT",
            "message": "입력값이 잘못되었습니다.",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "서버 내부 오류가 발생했습니다."
        }
    )


# =============================================================================
# Static Files
# =============================================================================
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# =============================================================================
# Health Check & Monitoring Endpoints
# =============================================================================
@app.get("/")
def read_root():
    """루트 엔드포인트"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """
    헬스 체크 (Kubernetes Liveness Probe)
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/ready")
async def readiness_check():
    """
    준비 상태 체크 (Kubernetes Readiness Probe)
    DB, Redis 연결 확인
    """
    checks = {
        "database": False,
        "redis": False
    }
    
    # DB 체크
    try:
        checks["database"] = await db_manager.health_check()
    except Exception as e:
        log.error(f"DB health check failed: {e}")
    
    # Redis 체크
    try:
        if redis_manager.redis:
            await redis_manager.redis.ping()
            checks["redis"] = True
    except Exception as e:
        log.error(f"Redis health check failed: {e}")
    
    # 모든 체크 통과 여부
    is_ready = all(checks.values())
    status_code = 200 if is_ready else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "not_ready",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """
    Prometheus 메트릭 엔드포인트
    """
    # DB Pool 메트릭 업데이트
    pool_status = db_manager.get_pool_status()
    update_db_pool_metrics(pool_status)
    
    return get_metrics()


@app.get("/info")
def app_info_endpoint():
    """
    애플리케이션 정보
    """
    pool_status = db_manager.get_pool_status()
    
    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        },
        "database": {
            "host": settings.DB_HOST,
            "name": settings.DB_NAME,
            "pool": pool_status
        },
        "redis": {
            "host": settings.REDIS_HOST,
            "connected": redis_manager.redis is not None
        },
        "websocket": {
            "active_rooms": len(manager.active_connections),
            "total_connections": sum(len(conns) for conns in manager.active_connections.values())
        }
    }
