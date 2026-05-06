![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)


<h1>🍃 동숲 주민들의 커뮤니티 - Backend & Infra</h1>

본 프로젝트의 백엔드는 **FastAPI**를 활용하여 빠르고 효율적인 비동기 처리를 구현했으며, **Terraform**을 통해 AWS 리소스 생성을 코드로 자동화(IaC)하여 **Amazon EKS** 환경에 배포되었습니다. 

🔗 **Frontend Repository**: [https://github.com/jing-jung/2-jingjung-community-fe](https://github.com/jing-jung/2-jingjung-community-fe)

## 🛠️ Tech Stack
### Backend
- **Framework**: Python (>=3.11), FastAPI, Uvicorn
- **Database / ORM**: AWS RDS (MySQL), PyMySQL, SQLAlchemy
- **Cache / Others**: Aioredis (Redis), bcrypt, python-multipart
- **Real-time**: WebSockets

### Infrastructure & CI/CD
- **Cloud Provider**: AWS
- **IaC**: Terraform
- **Container / Orchestration**: Docker, Amazon ECR, Amazon EKS
- **Routing**: Ingress (AWS ALB Ingress Controller)

## 📂 Directory Structure
```text
📦Community_Backend
 ┣ 📂app
 ┃ ┣ 📜main.py        
 ┃ ┣ 📜database.py      
 ┃ ┣ 📂models.py        
 ┃ ┗ 📂schemas.py     
 ┣ 📜.env             
 ┣ 📜.pyproject.toml            
 ┗ 📂static
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

### 1. 🚀 FastAPI 기반 비동기 API
- 비동기 처리(Asynchronous)를 기본으로 지원하는 FastAPI를 도입하여 빠르고 가벼운 RESTful API를 구축했습니다.
- CORS 미들웨어를 통해 등록된 로드밸런서 도메인(Ingress)에서의 안전한 접근을 허용합니다.

### 2. 💬 실시간 1:1 채팅 (WebSockets)
- `ConnectionManager`를 직접 구현하여 활성화된 WebSocket 커넥션을 메모리 상에서 관리합니다.
- 쿠키(`session_id`) 기반으로 접속 유저의 권한을 검증하고, 인가된 사용자만 특정 `room_id` 소켓에 접근할 수 있도록 보안을 강화했습니다.
- 메시지 수신 즉시 **AWS RDS**에 내역을 안전하게 저장하고, 동일한 방에 있는 유저들에게 실시간으로 브로드캐스팅합니다.

### 3. 🔒 보안 및 인증 체계
- **Bcrypt 암호화**: 사용자 비밀번호 단방향 해시 암호화 처리
- **세션 관리**: 쿠키와 데이터베이스 세션 테이블을 교차 검증하여 상태를 유지하고 인가되지 않은 API 접근 및 소켓 연결을 차단(1008 에러 반환)합니다.

### 4. 🗄️ ORM 기반 클라우드 DB 연동
- `SQLAlchemy`를 활용하여 직관적인 데이터베이스 쿼리를 수행하며, AWS RDS 엔드포인트와 연결하여 안정적인 데이터 읽기/쓰기를 지원합니다.
- 서버 구동 시 `Base.metadata.create_all`을 통해 동적으로 테이블을 생성 및 동기화합니다.

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
