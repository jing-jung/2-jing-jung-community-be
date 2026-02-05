![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)



<h2>🦁 Community Board - Backend Server</h2>

커뮤니티 게시판 프로젝트의 **REST API 서버** 리포지토리입니다.  
FastAPI와 MySQL을 기반으로 구축했습니다.

🔗 **Frontend Repository**: [https://github.com/jing-jung/2-jingjung-community-fe]

## 🛠️ Tech Stack
- **Framework**: FastAPI
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy
- **Security**: Passlib (Bcrypt), Python-multipart, PyMySQL

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

## ✨ Key Features (Backend)
1.  **RESTful API 설계**: 사용자, 게시글, 댓글, 좋아요 기능 API 구현
2.  **보안 강화 (Security)**
    - **SQL Injection 방지**: SQLAlchemy ORM을 사용하여 쿼리 주입 공격 차단
    - **비밀번호 암호화**: `bcrypt` 알고리즘을 이용한 단방향 해싱 저장
    - **입력 데이터 검증**: Pydantic을 활용한 Request Body 유효성 체크 (길이 제한 등)
3.  **예외 처리**: `400`, `404`, `500` 등 상황별 명확한 HTTP Status Code 및 에러 메시지 응답

## 💡 Why FastAPI? (Technology Decision)
이 프로젝트에서 **FastAPI**를 선택한 기술적 이유는 다음과 같습니다.

1.  **압도적인 성능과 비동기 처리 (`Async/Await`)**
    - Python 프레임워크 중 가장 빠른 성능(Node.js, Go와 대등)을 자랑하며, DB I/O 처리가 많은 게시판 서비스의 특성상 `Non-blocking` 방식이 유리하다고 판단했습니다.
2.  **강력한 데이터 검증 (Pydantic)**
    - Request Body로 들어오는 데이터의 타입을 Pydantic 모델로 엄격하게 정의하여, 런타임 에러를 사전에 방지하고 데이터 무결성을 높였습니다.
3.  **생산성 및 문서화 (Swagger UI)**
    - 코드 작성과 동시에 OpenAPI(Swagger) 문서가 자동 생성되어, 프론트엔드 연동 시 별도의 API 명세서를 작성하는 시간을 획기적으로 단축했습니다.

## 🛡️ Trouble Shooting & Security (핵심 문제 해결)

프로젝트 개발 과정에서 발생한 보안 취약점과 데이터 처리 문제를 해결한 과정입니다.

### 1. CORS 및 Cookie 인증 이슈 (Network)
- **문제 상황**: 프론트엔드와 백엔드 연동 시, 로그인 성공 후에도 브라우저에 쿠키(Session ID)가 저장되지 않거나 API 요청이 거절되는 현상.
- **원인 분석**: 브라우저의 보안 정책상 `localhost`와 `127.0.0.1`을 다른 도메인으로 인식하여 **Same-Origin Policy** 위반 발생.
- **해결**:
  - 백엔드 CORS 설정의 `allow_origins`와 프론트엔드 API 호출 URL을 `http://localhost:8000`으로 통일.
  - `allow_credentials=True` 옵션을 활성화하여 쿠키 공유 허용.

### 2. MVC 패턴 위반 및 아키텍처 개선 (Refactoring)
- **문제 상황**: 초기 개발 시 `routers.py` 파일에 비즈니스 로직(이메일 중복 체크 등)이 혼재되어 코드 가독성이 떨어지고 유지보수가 어려움.
- **해결**:
  - **Layered Architecture 적용**: 라우터는 "요청 분배"만 담당하고, 실제 로직은 `controllers.py`로 완전히 분리.
  - **Import 순환 참조 방지**: 절대 경로(`from app.models...`)를 사용하여 모듈 간 의존성 정리.


### 3. 대용량 데이터 처리 및 예외 핸들링
- **문제 상황**: 장문의 텍스트 입력 시 `400 Bad Request` 발생 및 서버 연결 끊김 현상.
- **해결**:
  - **Backend**: DB 컬럼 타입을 `VARCHAR(255)`에서 `TEXT`로 변경하여 저장 용량 확보.
  - **Frontend**: API 요청 전 `length` 체크 로직을 추가하여 1,000자 초과 시 즉시 차단(Early Return).
  - **Exception**: JSON 파싱 실패 시 `try-catch`로 감싸 `response.text()`를 확인하여 사용자에게 정확한 에러 원인 알림.

### 4. Windows 실행 권한 및 환경 이슈
- **문제 상황**: Windows 환경에서 `uvicorn` 명령어 직접 실행 시 보안 정책(Execution Policy)으로 인한 차단 발생.
- **해결**: 파이썬 모듈 실행 방식인 `python -m uvicorn ...` 명령어를 사용하여 실행 환경에 구애받지 않도록 개선.

### 5. RESTful API 아키텍처 재설계 및 리팩토링
- **문제 상황**: 
  - 초기 기획 단계의 URL이 `/get_posts`, `/update_user`와 같이 **행위(Action)** 중심으로 설계되어 있어 REST 원칙에 위배됨.
  - 수정 로직에 `POST`를 사용하는 등 HTTP Method의 의미가 불명확하고, 비즈니스 로직이 라우터에 혼재되어 유지보수가 어려움.
- **해결 (Refactoring)**:
  - **Resource-Oriented URL**: URL을 행위가 아닌 **리소스(명사)** 중심으로 재정의 (예: `/get_posts` → `GET /posts`, `/delete_comment` → `DELETE /comments/{id}`).
  - **HTTP Method 교정**: 리소스의 상태 변경 목적에 맞춰 메서드를 명확히 구분.
    - 데이터 생성: `POST`
    - 데이터 조회: `GET`
    - 전체 수정: `PUT` / 부분 수정: `PATCH`
    - 삭제: `DELETE`
  - **Layered Architecture 적용**: 라우터(`routes`)는 요청 수신만 담당하고, 실제 비즈니스 로직은 컨트롤러(`controllers`)로 분리하여 **책임의 분리(Separation of Concerns)** 실현.


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
    USERS ||--o{ POSTS : "writes"
    USERS ||--o{ COMMENTS : "writes"
    USERS ||--o{ LIKES : "clicks"
    USERS ||--o{ VIEWS : "logs"
    POSTS ||--o{ COMMENTS : "has"
    POSTS ||--o{ LIKES : "receives"
    POSTS ||--o{ VIEWS : "counts"

    USERS {
        int id PK
        string nickname
        string email
        string image_url
        string password
        timestamp created_at
    }
    POSTS {
        int id PK
        int user_id FK
        string title
        string image_url
        text contents
        int views_count
        int likes_count
        int comments_count
        timestamp created_at
    }
    COMMENTS {
        int id PK
        int post_id FK
        int user_id FK
        text content
        timestamp created_at
    }
    LIKES {
        int id PK
        int user_id FK
        int post_id FK
        timestamp created_at
    }
    VIEWS {
        int id PK
        int user_id FK
        int post_id FK
        timestamp created_at
    }
    SESSIONS {
        string session_id PK
        int expires
        text data
        timestamp created_at
    }
