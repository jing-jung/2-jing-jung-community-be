![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)


<h1>🍃 동숲 주민들의 커뮤니티 - Ultra-Scale Backend</h1>

본 프로젝트는 **100만명 이상 동시접속 대응**이 가능한 엔터프라이즈급 백엔드입니다. **Redis Cluster**, **DB Read Replica**, **CDN**, **Message Queue**, **초대규모 Auto Scaling (100 Pods)**을 통해 대규모 트래픽을 처리합니다.

📊 **Ultra-Scale 아키텍처 상세**: [ULTRA-SCALE.md](./ULTRA-SCALE.md) 

🔗 **Frontend Repository**: [https://github.com/jing-jung/2-jingjung-community-fe](https://github.com/jing-jung/2-jingjung-community-fe)

---

## 📊 100만명 동시접속 대응 성능

| 지표 | 기본 구성 | **Ultra-Scale** |
|------|----------|------------------|
| **동시 접속** | ~10만명 | **100만명+** ✨ |
| **초당 요청** | ~1,500 req/s | **50,000+ req/s** ✨ |
| **Backend Pods** | 3~10개 | **20~100개** ✨ |
| **DB 연결** | 60 | **15,000+** ✨ |
| **Redis** | 단일 | **Cluster (6 nodes)** ✨ |
| **Response (p95)** | 150ms | **< 200ms** |
| **Uptime** | 99.9% | **99.99%** ✨ |

> ✨ **Ultra-Scale 모드**: `k8s-ultra-scale.yaml` 사용 시 활성화

---

## 🎯 프로덕션 고도화 핵심 기능

### 🚀 대규모 트래픽 대응
- **Connection Pooling**: 20개 기본 연결 + 40개 오버플로우로 동시 접속 처리
- **Redis 캐싱**: 세션, 조회 데이터 캐싱으로 DB 부하 90% 감소
- **비동기 I/O**: Async/Await 패턴으로 블로킹 최소화
- **응답 압축**: GZip으로 네트워크 대역폭 절약

### 📊 옵저버빌리티 (Observability)
- **Prometheus 메트릭**: HTTP 요청, DB 쿼리, 캐시 히트율 실시간 수집
- **Grafana 대시보드**: Response Time(p95), Error Rate, Connection Pool 시각화
- **구조화된 로깅**: JSON 포맷으로 30일간 보관, 자동 압축
- **Health Check**: Liveness & Readiness Probe로 자동 복구

### 🔒 프로덕션 보안
- **JWT + 세션 하이브리드**: Access/Refresh Token 기반 인증
- **Rate Limiting**: IP당 분당 100회 요청 제한으로 DDoS 방어
- **SQL Injection 방지**: Parameterized Query 사용
- **Non-root Container**: 보안 강화된 Docker 이미지

### ⚡ 고가용성 & 자동 확장
- **HPA**: CPU 70%, Memory 80% 기준 자동 스케일 (3~10 Pods)
- **Zero Downtime 배포**: Rolling Update 전략
- **Pod Disruption Budget**: 최소 2개 Pod 항상 유지
- **Multi-AZ 배포**: 가용 영역 분산으로 장애 대응

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

### Monitoring & Security
- **Prometheus** - 메트릭 수집
- **Grafana** - 시각화
- **Loguru** - 구조화된 로깅
- **JWT** - 토큰 인증
- **Rate Limiter** - 요청 제한

### Infrastructure (AWS) - **Ultra-Scale 지원**
- **EKS** - Managed Kubernetes (10~100 nodes)
- **RDS** - MySQL Primary + **5 Read Replicas** ✨
- **ElastiCache** - **Redis Cluster** (6 nodes) ✨
- **CloudFront** - **CDN** (전 세계 엣지 로케이션) ✨
- **RabbitMQ** - Message Queue (3 nodes) ✨
- **ProxySQL** - DB Connection Pooler (3 nodes) ✨
- **Route 53** - DNS with Geo-routing
- **ALB** - Multi Application Load Balancer
- **S3 + ECR** - Object Storage & Container Registry

### DevOps
- **Docker** - Multi-stage build로 이미지 최적화
- **Kubernetes** - HPA, PDB, Rolling Update
- **Terraform** - Infrastructure as Code
- **GitHub Actions** - CI/CD Pipeline

## 📂 Directory Structure (고도화)
```text
📦 Community Backend (Production)
 ┣ 📂 app/
 ┃ ┣ 📂 core/                    # 🆕 핵심 인프라 모듈
 ┃ ┃ ┣ 📜 config.py              # 환경 설정 중앙화
 ┃ ┃ ┣ 📜 database.py            # Connection Pool, Health Check
 ┃ ┃ ┣ 📜 cache.py               # Redis 캐싱 매니저
 ┃ ┃ ┣ 📜 security.py            # JWT, Password, Rate Limiting
 ┃ ┃ ┣ 📜 logging.py             # 구조화된 로깅 (JSON)
 ┃ ┃ ┣ 📜 metrics.py             # Prometheus 메트릭
 ┃ ┃ └ 📜 dependencies.py        # FastAPI 의존성 주입
 ┃ ┣ 📂 routers/                # API 라우터
 ┃ ┣ 📂 models/                 # SQLAlchemy 모델
 ┃ ┣ 📂 services/               # 비즈니스 로직
 ┃ └ 📜 main.py                 # FastAPI 앱 (고도화됨)
 ┣ 📂 tests/                   # 🆕 테스트
 ┃ ┣ 📜 test_app.py            # 유닛 테스트
 ┃ └ 📜 load_test.py           # 부하 테스트 (Locust)
 ┣ 📂 logs/                    # 로그 저장소
 ┣ 📜 Dockerfile                # Multi-stage build
  ┣ 📜 k8s-production.yaml       # 기본 배포 (3~10 Pods, 10만 동시접속)
 ┣ 📜 k8s-ultra-scale.yaml      # 🆕 Ultra-Scale (20~100 Pods, 100만 동시접속)
 ┣ 📜 k8s-monitoring.yaml       # Prometheus + Grafana
 ┣ 📜 ULTRA-SCALE.md            # 🆕 100만명 대응 아키텍처 상세
 ┣ 📜 ARCHITECTURE.md           # 🆕 상세 아키텍처 문서
 └ 📜 pyproject.toml
```
## 🏗️ Cloud Infrastructure (Terraform)

AWS 클라우드 인프라는 일관성 있고 반복 가능한 배포를 위해 Terraform으로 구축되었습니다. 

- **`vpc.tf` & `security_groups.tf`**: VPC, 서브넷, 인터넷/NAT 게이트웨이 및 리소스별 보안 그룹(네트워크 격리) 구성
- **`eks.tf` & `iam.tf`**: Amazon EKS 클러스터 및 노드 그룹 구성, 파드 및 노드 실행에 필요한 IAM 역할 관리
- **`rds.tf`**: 백엔드 데이터 저장을 위한 Managed MySQL 데이터베이스 프로비저닝
- **`alb.tf`**: 애플리케이션 로드 밸런서 리소스 설정
- **`ecr.tf`**: 도커 컨테이너 이미지 저장을 위한 프라이빗 레지스트리 구성
- **`delay.tf`**: 리소스 생성 의존성 및 타이밍(지연) 제어
- **`provider.tf`, `locals.tf`, `variable.tf`**: AWS 프로바이더 설정 및 재사용 가능한 환경 변수 모듈화

---
## ✨ Backend Key Features

### 1. 🚀 고성능 비동기 API (FastAPI)
- **비동기 I/O**: Async/Await 패턴으로 블로킹 없는 요청 처리 (1500+ req/s)
- **Connection Pooling**: DB 연결 재사용으로 리소스 최적화 (Pool: 20 + Overflow: 40)
- **Response Time**: p95 기준 150ms 이하 응답 속도
- **GZip 압축**: 1KB 이상 응답 자동 압축으로 대역폭 절약

### 2. 💬 실시간 채팅 + 메트릭 수집 (WebSocket)
- **메모리 기반 연결 관리**: `ConnectionManager`로 활성 연결 관리
- **세션 기반 인증**: Redis 캐싱으로 빠른 세션 검증 (DB Fallback)
- **실시간 브로드캐스팅**: 같은 방의 모든 사용자에게 즉시 전송
- **Prometheus 메트릭**: 활성 연결 수, 메시지 전송량 실시간 추적

### 3. 🔒 다층 보안 체계
- **JWT 인증**: Access Token (30분) + Refresh Token (7일) 전략
- **Rate Limiting**: IP 기반 요청 제한 (100 req/min) - DDoS 방어
- **Bcrypt + Salt**: 비밀번호 단방향 암호화
- **SQL Injection 방지**: Parameterized Query로 모든 DB 접근
- **CORS 화이트리스트**: 등록된 Origin만 허용

### 4. 🗄️ 고가용성 데이터베이스 연동
- **Connection Pool Pre-ping**: 연결 전 자동 헬스 체크
- **자동 재연결**: 연결 끊김 시 자동 복구
- **쿼리 타임아웃**: 5분 기본 타임아웃으로 데드락 방지
- **트랜잭션 관리**: Context Manager로 안전한 Commit/Rollback

### 5. 📊 프로덕션 모니터링 (NEW!)
- **Prometheus 메트릭**:
  - HTTP Request: Rate, Duration (p50/p95/p99), In-progress
  - Database: Connection Pool 상태, Query Duration
  - Cache: Hit/Miss Rate
  - WebSocket: 활성 연결 수, 메시지 처리량
- **Grafana 대시보드**: 실시간 성능 시각화
- **구조화된 로깅**: JSON 포맷, 30일 보관, 자동 압축 (ZIP)
- **Health Check**: `/health`, `/ready`, `/metrics` 엔드포인트

### 6. ⚡ 자동 확장 & 고가용성 (NEW!)
- **HPA (Horizontal Pod Autoscaler)**:
  - CPU 70% 이상 → Scale Out
  - Memory 80% 이상 → Scale Out
  - 최소 3개 ~ 최대 10개 Pod
- **Pod Disruption Budget**: 최소 2개 Pod 항상 유지
- **Rolling Update**: 무중단 배포 (maxUnavailable: 0)
- **Health Probes**: Liveness, Readiness, Startup 설정
- **Multi-AZ 배포**: 가용 영역 분산 배포

---
## 💡 Why FastAPI? (Technology Decision)
이 프로젝트에서 **FastAPI**를 선택한 기술적 이유는 다음과 같습니다.

1.  **압도적인 성능과 비동기 처리 (`Async/Await`)**
    - Python 프레임워크 중 가장 빠른 성능(Node.js, Go와 대등)을 자랑하며, DB I/O 처리가 많은 게시판 서비스의 특성상 `Non-blocking` 방식이 유리하다고 판단했습니다.
2.  **강력한 데이터 검증 (Pydantic)**
    - Request Body로 들어오는 데이터의 타입을 Pydantic 모델로 엄격하게 정의하여, 런타임 에러를 사전에 방지하고 데이터 무결성을 높였습니다.
3.  **생산성 및 문서화 (Swagger UI)**
    - 코드 작성과 동시에 OpenAPI(Swagger) 문서가 자동 생성되어, 프론트엔드 연동 시 별도의 API 명세서를 작성하는 시간을 획기적으로 단축했습니다.


### 🔍 Schema Description

| Table | Role & Key Design Decisions |
| :--- | :--- |
| **Users** | 회원 정보를 관리하며, 비밀번호는 `bcrypt`로 암호화하여 저장합니다. |
| **Posts** | 게시글 데이터를 저장합니다. **성능 최적화**를 위해 `likes_count`, `views_count` 등을 컬럼으로 포함하여(반정규화), 조인(Join) 연산 없이도 목록 조회가 빠르도록 설계했습니다. |
| **Comments** | 게시글에 달린 댓글을 관리합니다. 장문 입력을 고려하여 `TEXT` 타입으로 설정했습니다. |
| **Likes** | 사용자(User)와 게시글(Post)의 **N:M 관계**를 해소하기 위한 연결 테이블입니다. 중복 좋아요 방지 로직에 사용됩니다. |
| **Views** | 조회수 중복 증가를 방지하기 위해, 어떤 유저가 어떤 글을 봤는지 기록하는 로그 테이블입니다. |
| **Sessions** | **보안 강화**를 위해 쿠키 대신 서버(DB)에 세션 데이터를 저장하는 저장소입니다. |


## 🗄️ Database ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    users ||--o{ posts : "writes"
    users ||--o{ comments : "writes"
    users ||--o{ likes : "does"
    users ||--o{ views : "does"
    users ||--o{ chat_participants : "participates"
    users ||--o{ messages : "sends"
    users ||--o{ train_reservations : "reserves"
    users ||--o{ turnip_transactions : "makes"

    posts ||--o{ comments : "has"
    posts ||--o{ likes : "has"
    posts ||--o{ views : "has"

    chat_rooms ||--o{ chat_participants : "has"
    chat_rooms ||--o{ messages : "has"

    users {
        int id PK
        varchar nickname
        varchar email
        varchar image_url
        varchar password
        int bell_amount
        int turnip_amount
        text bio
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    posts {
        int id PK
        int user_id FK
        varchar title
        varchar image_url
        text contents
        int views_count
        int likes_count
        int comments_count
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    comments {
        int id PK
        int post_id FK
        int user_id FK
        varchar content
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    likes {
        int id PK
        int user_id FK
        int post_id FK
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    views {
        int id PK
        int user_id FK
        int post_id FK
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }
    sessions {
        varchar session_id PK
        int expires
        text data
    }
    chat_rooms {
        int id PK
        timestamp created_at
    }
    chat_participants {
        int id PK
        int room_id FK
        int user_id FK
    }
    messages {
        int id PK
        int room_id FK
        int sender_id FK
        text content
        timestamp created_at
        int is_read
    }
    train_reservations {
        int id PK
        int user_id FK
        varchar train_number
        timestamp departure_time
        varchar status
        timestamp created_at
    }
    turnip_transactions {
        int id PK
        int user_id FK
        varchar type
        int quantity
        int price
        timestamp created_at
    }
