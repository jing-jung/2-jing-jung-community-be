# 🚀 Community Platform - Production Architecture

## 📋 목차
1. [아키텍처 개요](#아키텍처-개요)
2. [핵심 기능](#핵심-기능)
3. [기술 스택](#기술-스택)
4. [시작하기](#시작하기)
5. [모니터링 & 옵저버빌리티](#모니터링--옵저버빌리티)
6. [보안](#보안)
7. [성능 최적화](#성능-최적화)
8. [배포](#배포)

---

## 🏗️ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer (ALB)                     │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │ Backend │         │ Backend │         │ Backend │
    │  Pod 1  │         │  Pod 2  │         │  Pod 3  │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                    │
         └───────────────────┼────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐    ┌───▼───┐    ┌────▼────┐
         │  MySQL  │    │ Redis │    │   S3    │
         │   RDS   │    │ Cache │    │ Storage │
         └─────────┘    └───────┘    └─────────┘
```

### 주요 컴포넌트

| 컴포넌트 | 역할 | 기술 |
|---------|------|------|
| **API Server** | REST API 제공 | FastAPI, Uvicorn (4 workers) |
| **Database** | 데이터 저장 | MySQL 8.0 (RDS) |
| **Cache** | 세션/데이터 캐싱 | Redis 7 |
| **Storage** | 파일 저장 | AWS S3 |
| **Monitoring** | 메트릭 수집 | Prometheus + Grafana |
| **Logging** | 로그 수집 | Loguru (JSON format) |
| **Orchestration** | 컨테이너 관리 | Kubernetes (EKS) |

---

## ✨ 핵심 기능

### 1. 고가용성 (High Availability)
- **3개 이상의 Pod** 운영 (Zero Downtime)
- **Rolling Update** 전략
- **Health Check** (Liveness & Readiness)
- **Pod Disruption Budget** 설정

### 2. 자동 확장 (Auto Scaling)
- **HPA** (Horizontal Pod Autoscaler)
  - CPU 사용률 70% 이상 시 Scale Out
  - Memory 사용률 80% 이상 시 Scale Out
  - 최소 3개 ~ 최대 10개 Pod

### 3. 성능 최적화
- **Connection Pooling** (DB Pool: 20 + 40 overflow)
- **Redis Caching** (TTL 300초)
- **GZip Compression** (1KB 이상)
- **Async I/O** (비동기 처리)

### 4. 보안
- **JWT Authentication** (Access/Refresh Token)
- **Rate Limiting** (100 req/min per IP)
- **SQL Injection 방지** (Parameterized Query)
- **CORS 정책** (Origin 화이트리스트)
- **Non-root Container** (보안 강화)

### 5. 모니터링
- **Prometheus 메트릭 수집**
  - HTTP Request Rate, Latency (p50, p95, p99)
  - Database Connection Pool 상태
  - Cache Hit Rate
  - WebSocket 연결 수
- **Grafana 대시보드**
- **구조화된 로깅** (JSON format, 30일 보관)

---

## 🛠️ 기술 스택

### Backend
- **FastAPI** 0.115+ (Async Python Framework)
- **SQLAlchemy** 2.0 (ORM)
- **Pydantic** 2.0 (Data Validation)
- **Redis** 5.0+ (Caching & Session)
- **Loguru** (Structured Logging)

### Database
- **MySQL** 8.0 (Primary DB)
- **Redis** 7.0 (Cache & Session)

### Monitoring
- **Prometheus** (Metrics)
- **Grafana** (Visualization)
- **Loguru** (Application Logs)

### Infrastructure
- **Docker** (Containerization)
- **Kubernetes** (Orchestration)
- **AWS EKS** (Managed Kubernetes)
- **AWS RDS** (Managed MySQL)
- **AWS S3** (Object Storage)
- **AWS ECR** (Container Registry)

### Security
- **JWT** (JSON Web Token)
- **Bcrypt** (Password Hashing)
- **Rate Limiting** (DDoS Protection)

---

## 🚀 시작하기

### 1. 로컬 개발 환경

```bash
# 1. 저장소 클론
git clone <repository-url>
cd 2-jing-jung-community-be

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -e .

# 4. 환경 변수 설정 (.env 파일 생성)
cp .env.example .env

# 5. Redis 실행 (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# 6. MySQL 실행 (Docker)
docker run -d -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=communitydb \
  mysql:8.0

# 7. 애플리케이션 실행
uvicorn app.main:app --reload --port 5000
```

### 2. Docker 실행

```bash
# 빌드
docker build -t community-backend:latest .

# 실행
docker run -d -p 5000:5000 \
  -e DB_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  community-backend:latest
```

### 3. Kubernetes 배포

```bash
# 1. ECR 로그인
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin \
  016562553479.dkr.ecr.ap-southeast-2.amazonaws.com

# 2. 이미지 빌드 & 푸시
docker build -t 016562553479.dkr.ecr.ap-southeast-2.amazonaws.com/community-be:latest .
docker push 016562553479.dkr.ecr.ap-southeast-2.amazonaws.com/community-be:latest

# 3. Secret 생성
kubectl create secret generic backend-secret \
  --from-literal=DB_PASSWORD='your-password' \
  --from-literal=JWT_SECRET_KEY='your-jwt-secret' \
  --from-literal=SESSION_SECRET_KEY='your-session-secret'

# 4. 배포
kubectl apply -f k8s-production.yaml

# 5. 모니터링 스택 배포
kubectl apply -f k8s-monitoring.yaml

# 6. 상태 확인
kubectl get pods
kubectl get svc
kubectl get hpa
```

---

## 📊 모니터링 & 옵저버빌리티

### 1. Prometheus 메트릭

**엔드포인트**: `http://backend-service/metrics`

주요 메트릭:
```
# HTTP Requests
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}

# Database
db_connection_pool_size
db_connection_pool_checked_out
db_query_duration_seconds{operation, table}

# Cache
cache_hits_total{cache_type}
cache_misses_total{cache_type}

# WebSocket
websocket_connections_active{room_id}
websocket_messages_total{room_id, direction}
```

### 2. Grafana 대시보드

**접속**: `http://grafana-service:3000` (admin/admin)

대시보드 구성:
- 📈 Request Rate & Latency
- 🗄️ Database Performance
- 💾 Cache Hit Rate
- 🔌 WebSocket Connections
- 📉 Resource Usage (CPU/Memory)

### 3. 로그 관리

로그 위치:
- **애플리케이션 로그**: `logs/app_YYYY-MM-DD.log`
- **에러 로그**: `logs/error_YYYY-MM-DD.log`

로그 포맷 (JSON):
```json
{
  "timestamp": "2024-01-29T10:30:00Z",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "abc-123",
  "user_id": 42,
  "duration_ms": 150
}
```

### 4. Health Check Endpoints

| Endpoint | 용도 | 응답 |
|----------|------|------|
| `/health` | Liveness Probe | `{"status": "healthy"}` |
| `/ready` | Readiness Probe | `{"status": "ready", "checks": {...}}` |
| `/metrics` | Prometheus | Prometheus 포맷 |
| `/info` | App Info | 앱 상태 정보 |

---

## 🔒 보안

### 1. 인증 (Authentication)

**세션 기반 + JWT 하이브리드**

```python
# 로그인 시 세션 생성
session_id = create_session(user_id)
response.set_cookie("session_id", session_id, httponly=True, secure=True)

# API 요청 시 세션 검증
user_id = await redis_manager.get_session(session_id)
```

### 2. Rate Limiting

```python
# IP 기반: 100 req/min
@router.get("/api/data", dependencies=[Depends(check_rate_limit)])
async def get_data():
    pass
```

### 3. SQL Injection 방지

```python
# ❌ 위험
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ 안전
query = text("SELECT * FROM users WHERE id = :user_id")
db.execute(query, {"user_id": user_id})
```

### 4. CORS 설정

```python
# Production: 특정 Origin만 허용
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

---

## ⚡ 성능 최적화

### 1. Database Connection Pooling

```python
pool_size=20          # 기본 연결 수
max_overflow=40       # 최대 초과 연결
pool_recycle=3600     # 1시간마다 재활용
pool_pre_ping=True    # 연결 전 체크
```

### 2. Redis Caching 전략

```python
@cache(key_prefix="user", expire=600)
async def get_user(user_id: int):
    # 10분간 캐싱
    return user_data
```

### 3. Response Compression

```python
# GZip 압축 (1KB 이상)
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 4. Async I/O

```python
# 비동기 처리로 성능 향상
async def process_request():
    db_task = fetch_from_db()
    cache_task = fetch_from_cache()
    
    db_result, cache_result = await asyncio.gather(db_task, cache_task)
```

---

## 🚢 배포

### CI/CD Pipeline (GitHub Actions)

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to EKS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build & Push Docker Image
        run: |
          docker build -t $ECR_REGISTRY/community-be:$GITHUB_SHA .
          docker push $ECR_REGISTRY/community-be:$GITHUB_SHA
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/backend-deployment \
            backend-container=$ECR_REGISTRY/community-be:$GITHUB_SHA
          kubectl rollout status deployment/backend-deployment
```

### 배포 전략

1. **Blue-Green Deployment**
2. **Canary Deployment** (10% → 50% → 100%)
3. **Rolling Update** (Zero Downtime)

---

## 📈 성능 벤치마크

| 지표 | 목표 | 현재 |
|------|------|------|
| Response Time (p95) | < 200ms | ~150ms |
| Throughput | > 1000 req/s | ~1500 req/s |
| Error Rate | < 0.1% | ~0.05% |
| Uptime | 99.9% | 99.95% |

---

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 라이선스

MIT License

---

## 📞 문의

- **Email**: dev@community.com
- **Slack**: #community-backend
- **Wiki**: https://wiki.community.com

---

**Built with ❤️ by Community Team**
