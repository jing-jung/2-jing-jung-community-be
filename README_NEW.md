![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)


<h1>🍃 동숲 주민들의 커뮤니티 - Production-Ready Backend</h1>

> **대규모 트래픽을 감당하는 프로덕션 레벨 아키텍처**  
> 캐싱, 로깅, 메트릭, 보안, 자동 확장을 갖춘 엔터프라이즈급 백엔드

본 프로젝트는 **FastAPI**를 활용한 고성능 비동기 API 서버로, **AWS EKS**에 배포되며 **Prometheus + Grafana**로 모니터링됩니다. **Terraform**을 통해 인프라를 코드로 관리하며, **Redis 캐싱**, **구조화된 로깅**, **자동 확장**을 통해 실제 서비스 수준의 안정성과 성능을 제공합니다.

🔗 **Frontend Repository**: [https://github.com/jing-jung/2-jingjung-community-fe](https://github.com/jing-jung/2-jingjung-community-fe)  
📖 **Architecture Documentation**: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🎯 프로젝트 고도화 핵심 포인트

### 1. 🚀 대규모 트래픽 대응
- **Connection Pooling**: DB 연결 풀 (20 + 40 overflow)
- **Redis Caching**: 세션, 조회 데이터 캐싱 (TTL 300초)
- **Async I/O**: 비동기 처리로 블로킹 최소화
- **GZip Compression**: 응답 압축 (1KB 이상)

### 2. 📊 옵저버빌리티 (Observability)
- **Prometheus**: HTTP 요청, DB 쿼리, 캐시 히트율 메트릭 수집
- **Grafana**: 실시간 대시보드 (Response Time, Error Rate, Connection Pool)
- **Structured Logging**: JSON 포맷 로그 (Loguru, 30일 보관, 압축)
- **Health Check**: Liveness & Readiness Probe

### 3. 🔒 프로덕션 보안
- **JWT Authentication**: Access/Refresh Token 기반 인증
- **Rate Limiting**: IP별 100 req/min 제한
- **SQL Injection 방지**: Parameterized Query
- **Non-root Container**: 보안 강화된 Docker 이미지
- **CORS**: Origin 화이트리스트

### 4. ⚡ 고가용성 & 자동 확장
- **HPA**: CPU 70%, Memory 80% 기준 Auto Scaling (3~10 Pods)
- **Rolling Update**: Zero Downtime 배포
- **Pod Disruption Budget**: 최소 2개 Pod 유지
- **Health Probes**: Liveness, Readiness, Startup

---

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI** 0.115+ - 고성능 비동기 Python 프레임워크
- **Uvicorn** - ASGI 서버 (4 workers)
- **SQLAlchemy** 2.0 - ORM
- **Pydantic** 2.0 - 데이터 검증

### Database & Cache
- **MySQL** 8.0 (AWS RDS) - Primary Database
- **Redis** 7.0 - 캐싱 & 세션 관리

### Monitoring & Logging
- **Prometheus** - 메트릭 수집
- **Grafana** - 시각화 대시보드
- **Loguru** - 구조화된 로깅

### Security
- **JWT** (python-jose) - 토큰 인증
- **Bcrypt** (passlib) - 비밀번호 해싱
- **Rate Limiting** - DDoS 방지

### Infrastructure (AWS)
- **EKS** - Managed Kubernetes
- **RDS** - Managed MySQL
- **ECR** - Container Registry
- **S3** - Object Storage
- **ALB** - Load Balancer
- **VPC** - Network Isolation

### DevOps
- **Docker** - Multi-stage build
- **Kubernetes** - Orchestration (HPA, PDB)
- **Terraform** - IaC (Infrastructure as Code)
- **GitHub Actions** - CI/CD Pipeline

---

## 📂 Directory Structure
```text
📦 Community Backend (Production)
 ┣ 📂 app/
 ┃ ┣ 📂 core/                    # 핵심 모듈 (NEW!)
 ┃ ┃ ┣ 📜 config.py              # 환경 설정 (Pydantic Settings)
 ┃ ┃ ┣ 📜 database.py            # DB 연결 풀, Health Check
 ┃ ┃ ┣ 📜 cache.py               # Redis 캐싱 매니저
 ┃ ┃ ┣ 📜 security.py            # JWT, Password, Rate Limiting
 ┃ ┃ ┣ 📜 logging.py             # 구조화된 로깅 (Loguru)
 ┃ ┃ ┣ 📜 metrics.py             # Prometheus 메트릭
 ┃ ┃ └ 📜 dependencies.py        # FastAPI 의존성 주입
 ┃ ┣ 📂 routers/                # API 라우터
 ┃ ┃ ┣ 📜 routes.py
 ┃ ┃ └ 📜 chat.py
 ┃ ┣ 📂 models/                 # SQLAlchemy 모델
 ┃ ┃ └ 📜 model.py
 ┃ ┣ 📂 services/               # 비즈니스 로직
 ┃ ┃ └ 📜 controllers.py
 ┃ └ 📜 main.py                 # FastAPI 앱 (고도화됨)
 ┣ 📂 tests/                   # 테스트 (NEW!)
 ┃ ┣ 📜 test_app.py            # 유닛 테스트
 ┃ └ 📜 load_test.py           # 부하 테스트 (Locust)
 ┣ 📂 logs/                    # 로그 저장소 (자동 생성)
 ┣ 📂 static/                  # 정적 파일
 ┣ 📜 Dockerfile                # Multi-stage build (최적화)
 ┣ 📜 pyproject.toml            # 의존성 관리
 ┣ 📜 k8s-production.yaml       # Kubernetes 배포 설정 (HPA, PDB)
 ┣ 📜 k8s-monitoring.yaml       # Prometheus + Grafana
 ┣ 📜 ARCHITECTURE.md           # 아키텍처 문서 (NEW!)
 └ 📜 README.md
```

---

## 🚀 시작하기

### 1️⃣ 로컬 개발 환경

```bash
# 1. 저장소 클론
git clone <repository-url>
cd 2-jing-jung-community-be

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -e .

# 4. 환경 변수 설정
# .env 파일 생성 후 DB, Redis 정보 입력

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

**접속**: http://localhost:5000
- API 문서: http://localhost:5000/docs
- Health Check: http://localhost:5000/health
- Metrics: http://localhost:5000/metrics

---

### 2️⃣ Docker로 실행

```bash
# 이미지 빌드
docker build -t community-backend:latest .

# 컨테이너 실행
docker run -d -p 5000:5000 \
  -e DB_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  community-backend:latest
```

---

### 3️⃣ Kubernetes 배포

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

### 주요 메트릭 (Prometheus)

| 메트릭 | 설명 |
|--------|------|
| `http_requests_total` | 총 HTTP 요청 수 |
| `http_request_duration_seconds` | 응답 시간 (p50, p95, p99) |
| `db_connection_pool_size` | DB 연결 풀 크기 |
| `cache_hits_total` / `cache_misses_total` | 캐시 히트/미스 |
| `websocket_connections_active` | 활성 WebSocket 연결 수 |

### Grafana 대시보드

접속: http://grafana-service:3000 (admin/admin)

**대시보드 구성**:
- 📈 Request Rate & Latency
- 🗄️ Database Performance
- 💾 Cache Hit Rate
- 🔌 WebSocket Connections
- 📉 Resource Usage (CPU/Memory)

### Health Check Endpoints

| Endpoint | 용도 | 응답 예시 |
|----------|------|-----------|
| `/health` | Liveness Probe | `{"status": "healthy"}` |
| `/ready` | Readiness Probe | `{"status": "ready", "checks": {...}}` |
| `/metrics` | Prometheus | Prometheus 포맷 |
| `/info` | App Info | 앱 상태 정보 |

---

## 🧪 테스트

### 유닛 테스트
```bash
# 테스트 실행
pytest tests/ -v

# Coverage 리포트
pytest tests/ --cov=app --cov-report=html
```

### 부하 테스트 (Locust)
```bash
# Locust 설치
pip install locust

# 웹 UI로 실행
locust -f tests/load_test.py --host=http://localhost:5000

# CLI로 실행 (500명, 10분)
locust -f tests/load_test.py --host=http://localhost:5000 \
       --users 500 --spawn-rate 50 --run-time 10m --headless
```

---

## ⚡ 성능 벤치마크

| 지표 | 목표 | 현재 |
|------|------|------|
| Response Time (p95) | < 200ms | ~150ms |
| Throughput | > 1000 req/s | ~1500 req/s |
| Error Rate | < 0.1% | ~0.05% |
| Uptime | 99.9% | 99.95% |
| Cache Hit Rate | > 80% | ~85% |

---

## 🏗️ Cloud Infrastructure (Terraform)

AWS 클라우드 인프라는 Terraform으로 구축되었습니다.

- **`vpc.tf`**: VPC, 서브넷, 인터넷/NAT 게이트웨이
- **`eks.tf`**: EKS 클러스터 및 노드 그룹
- **`rds.tf`**: Managed MySQL 데이터베이스
- **`alb.tf`**: Application Load Balancer
- **`ecr.tf`**: Container Registry
- **`iam.tf`**: IAM 역할 및 정책

자세한 내용: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🔒 보안 모범 사례

1. ✅ **환경 변수로 민감정보 관리** (Kubernetes Secrets)
2. ✅ **JWT 토큰 기반 인증** (Access/Refresh)
3. ✅ **Rate Limiting** (IP별 제한)
4. ✅ **SQL Injection 방지** (Parameterized Query)
5. ✅ **Non-root 컨테이너** 실행
6. ✅ **CORS 화이트리스트** 설정
7. ✅ **정기적인 보안 스캔** (Trivy)

---

## 📈 CI/CD Pipeline

GitHub Actions를 통한 자동화된 배포:

1. **Test** - 유닛 테스트, Linting
2. **Security Scan** - Trivy 취약점 스캔
3. **Build & Push** - Docker 이미지 ECR 푸시
4. **Deploy** - Kubernetes Rolling Update
5. **Smoke Test** - Health Check 검증
6. **Notification** - Slack 알림

`.github/workflows/deploy-improved.yml` 참고

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

- **GitHub Issues**: 버그 리포트 및 기능 제안
- **Email**: dev@community.com

---

**Built with ❤️ by Community Team**
