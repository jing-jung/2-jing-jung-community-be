"""
Prometheus Metrics for Monitoring
애플리케이션 성능 메트릭 수집
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.core.logging import log


# Request 메트릭
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint']
)

# Database 메트릭
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_connection_pool_checked_out = Gauge(
    'db_connection_pool_checked_out',
    'Database connections currently checked out'
)

# Cache 메트릭
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# WebSocket 메트릭
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections',
    ['room_id']
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['room_id', 'direction']  # sent/received
)

# Application 정보
app_info = Info('app', 'Application information')


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Prometheus 메트릭 수집 미들웨어
    """
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        
        # 메트릭 엔드포인트는 제외
        if endpoint == "/metrics":
            return await call_next(request)
        
        # 진행 중인 요청 수 증가
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # 요청 시작 시간
        start_time = time.time()
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 응답 시간 기록
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # 요청 카운트 증가
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            return response
            
        except Exception as e:
            log.error(f"Request error: {e}")
            
            # 에러 카운트
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()
            
            raise
        
        finally:
            # 진행 중인 요청 수 감소
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


def update_db_pool_metrics(pool_status: dict):
    """데이터베이스 풀 상태 메트릭 업데이트"""
    db_connection_pool_size.set(pool_status.get("pool_size", 0))
    db_connection_pool_checked_out.set(pool_status.get("checked_out", 0))


def record_db_query(operation: str, table: str, duration: float):
    """데이터베이스 쿼리 메트릭 기록"""
    db_queries_total.labels(operation=operation, table=table).inc()
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def record_cache_hit(cache_type: str = "redis"):
    """캐시 히트 기록"""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = "redis"):
    """캐시 미스 기록"""
    cache_misses_total.labels(cache_type=cache_type).inc()


def update_websocket_connections(room_id: int, delta: int):
    """WebSocket 연결 수 업데이트"""
    current = websocket_connections_active.labels(room_id=str(room_id))._value.get()
    websocket_connections_active.labels(room_id=str(room_id)).set(max(0, current + delta))


def record_websocket_message(room_id: int, direction: str):
    """WebSocket 메시지 기록"""
    websocket_messages_total.labels(room_id=str(room_id), direction=direction).inc()


def get_metrics():
    """메트릭 데이터 반환 (Prometheus 포맷)"""
    return generate_latest(REGISTRY)
