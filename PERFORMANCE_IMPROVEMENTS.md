# 🚀 성능 개선 보고서

## 📋 개선 내역 요약

### ✅ **1순위: 즉시 개선한 심각한 문제**

#### **1) WebSocket DB 세션 안전성 개선** ⚠️
**문제점:**
- DB 세션을 직접 생성 후 `finally`에서 닫고 있었으나, 중간에 `return`이 있으면 실행되지 않음
- 예외 발생 시 DB 커넥션 누수 위험

**개선 내용:**
```python
# Before
db = db_manager.SessionLocal()
try:
    # ... 작업 ...
    return  # 여기서 리턴하면 finally가 실행 안 됨
finally:
    db.close()

# After
with db_manager.session_scope() as db:
    # Context Manager가 자동으로 커밋/롤백/세션 종료
```

**효과:**
- ✅ DB 커넥션 누수 방지
- ✅ 예외 안전성 향상
- ✅ 트랜잭션 자동 관리

---

#### **2) 채팅 엔진 메모리 누수 방지** ⚠️
**문제점:**
- `user_memory = {}` 전역 딕셔너리가 무한정 증가
- 유저가 많아지면 메모리 고갈 위험

**개선 내용:**
```python
# Before
user_memory = {}  # 영원히 삭제되지 않음

# After
from cachetools import TTLCache
user_memory = TTLCache(maxsize=10000, ttl=1800)  # 30분 후 자동 삭제
```

**효과:**
- ✅ 메모리 사용량 제한 (최대 10,000명)
- ✅ 비활성 유저 자동 정리 (30분 TTL)
- ✅ OOM(Out of Memory) 방지

---

#### **3) CSV 파일 로딩 최적화** ⚠️
**문제점:**
- 모듈 임포트 시마다 CSV를 동기적으로 읽음
- 서버 시작 시 블로킹 발생

**개선 내용:**
```python
# Before
engine = RecommendationEngine(shops_path, logs_path)  # 모듈 로딩 시 실행

# After
async def init_recommendation_engine():
    global engine
    engine = RecommendationEngine(shops_path, logs_path)

# FastAPI lifespan에서 호출
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_recommendation_engine()  # 서버 시작 시 한 번만
```

**효과:**
- ✅ 서버 재시작 시 빠른 초기화
- ✅ 메모리에 한 번만 로딩
- ✅ 핫 리로드 시 중복 로딩 방지

---

### 🟡 **2순위: 다음 단계에서 개선할 사항**

#### **4) Redis 캐싱 확대**
**현재 상태:**
- Redis는 연결되어 있지만, 세션 조회에만 사용 중
- 게시글, 댓글, 채팅방 목록 등은 매번 DB 조회

**개선 방안:**
```python
# 예시: 게시글 조회에 캐싱 적용
from app.core.cache import cache

@cache(key_prefix="post", expire=300)  # 5분 캐싱
async def get_post(post_id: int):
    # DB 조회
    return post_data
```

**예상 효과:**
- ⚡ 조회 API 응답 시간 50% 이상 감소
- 📉 DB 부하 70% 감소
- 💰 인프라 비용 절감

---

#### **5) DB 쿼리 최적화**
**개선 필요 항목:**
1. **N+1 쿼리 문제**
   ```sql
   -- Before: 게시글 100개 조회 시 101번의 쿼리 발생
   SELECT * FROM posts LIMIT 100;
   SELECT * FROM users WHERE id = 1;
   SELECT * FROM users WHERE id = 2;
   ...

   -- After: JOIN으로 1번의 쿼리로 해결
   SELECT p.*, u.* FROM posts p 
   LEFT JOIN users u ON p.user_id = u.id 
   LIMIT 100;
   ```

2. **인덱스 추가**
   ```sql
   -- 자주 조회되는 컬럼에 인덱스 추가
   CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
   CREATE INDEX idx_posts_user_id ON posts(user_id);
   CREATE INDEX idx_messages_room_id ON messages(room_id);
   ```

3. **페이지네이션 최적화**
   ```sql
   -- Before: OFFSET은 큰 값일수록 느림
   SELECT * FROM posts ORDER BY id DESC LIMIT 20 OFFSET 10000;

   -- After: Cursor 기반 페이지네이션
   SELECT * FROM posts WHERE id < 10000 ORDER BY id DESC LIMIT 20;
   ```

**예상 효과:**
- ⚡ 쿼리 속도 5~10배 향상
- 📉 DB CPU 사용률 60% 감소

---

### 🟢 **3순위: 확장성 개선 (스케일아웃 대비)**

#### **6) WebSocket 분산 처리**
**문제점:**
- 현재 `ConnectionManager`는 단일 서버 인스턴스에만 존재
- 서버가 2대 이상일 때, 다른 서버의 유저에게 메시지가 전달되지 않음

**개선 방안:**
```python
# Redis Pub/Sub를 사용한 브로드캐스팅
import redis.asyncio as aioredis

class DistributedConnectionManager:
    def __init__(self):
        self.local_connections = {}
        self.redis_pubsub = None

    async def broadcast_to_room(self, room_id: int, message: str):
        # 1. 로컬 연결에 전송
        await self.broadcast_to_local(room_id, message)
        
        # 2. Redis Pub/Sub으로 다른 서버에 전파
        await redis_manager.redis.publish(
            f"room:{room_id}",
            message
        )

    async def listen_to_room_messages(self, room_id: int):
        # Redis에서 메시지 수신
        pubsub = redis_manager.redis.pubsub()
        await pubsub.subscribe(f"room:{room_id}")
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                await self.broadcast_to_local(room_id, message['data'])
```

**예상 효과:**
- ✅ 무한 수평 확장 가능
- ✅ 서버 장애 시 자동 페일오버
- ✅ Load Balancer 뒤에서 정상 작동

---

## 📊 부하 테스트 계획

### **1단계: Locust 기본 테스트**
```bash
# 100명의 동시 사용자, 10초에 걸쳐 증가
locust -f tests/load_test.py \
       --host=http://localhost:5000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 5m \
       --headless \
       --html report.html
```

**측정 항목:**
- 평균 응답 시간 (Avg Response Time)
- 95th Percentile 응답 시간
- 요청 성공률 (Success Rate)
- 초당 요청 수 (RPS)

**목표:**
- 평균 응답 시간 < 200ms
- 95th Percentile < 500ms
- 성공률 > 99.9%

---

### **2단계: K6를 사용한 시나리오 테스트**
```javascript
// k6_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },  // Stay
    { duration: '2m', target: 200 },  // Spike
    { duration: '5m', target: 200 },  // Stay
    { duration: '2m', target: 0 },    // Ramp down
  ],
};

export default function () {
  // 1. 게시글 목록 조회
  let res = http.get('http://localhost:5000/posts');
  check(res, { 'status is 200': (r) => r.status === 200 });
  
  // 2. 게시글 상세 조회
  res = http.get('http://localhost:5000/posts/1');
  check(res, { 'post detail OK': (r) => r.status === 200 });
  
  sleep(1);
}
```

```bash
k6 run --out json=results.json k6_test.js
```

---

### **3단계: 모니터링 대시보드 구축**

#### **Prometheus + Grafana 설정**

**prometheus.yml**
```yaml
scrape_configs:
  - job_name: 'fastapi'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:5000']
```

**Grafana 대시보드 메트릭:**
1. **HTTP 메트릭**
   - `http_requests_total` - 총 요청 수
   - `http_request_duration_seconds` - 응답 시간 분포
   - `http_requests_in_progress` - 진행 중인 요청

2. **DB 메트릭**
   - `db_connection_pool_size` - 커넥션 풀 크기
   - `db_connection_pool_checked_out` - 사용 중인 연결
   - `db_query_duration_seconds` - 쿼리 실행 시간

3. **WebSocket 메트릭**
   - `websocket_connections_active` - 활성 연결 수
   - `websocket_messages_total` - 메시지 송수신 수

4. **시스템 메트릭**
   - CPU 사용률
   - 메모리 사용률
   - 네트워크 I/O

---

## 🎯 성능 목표

### **현재 상태 (예상)**
- 평균 응답 시간: ~500ms
- 동시 접속자: ~50명
- DB 커넥션 풀: 5개 (부족)

### **개선 후 목표**
| 메트릭 | 현재 | 목표 | 개선율 |
|--------|------|------|--------|
| 평균 응답 시간 | 500ms | 150ms | **70% ↓** |
| 95th Percentile | 1000ms | 300ms | **70% ↓** |
| 동시 접속자 | 50명 | 500명 | **10배 ↑** |
| 초당 요청 처리 | 100 RPS | 1000 RPS | **10배 ↑** |
| DB 커넥션 사용률 | 100% | 60% | **40% ↓** |

---

## 📝 다음 단계 체크리스트

### **즉시 실행 (오늘)**
- [x] WebSocket DB 세션 안전성 개선
- [x] 메모리 누수 방지 (TTL 캐시)
- [x] CSV 로딩 최적화
- [ ] `pip install cachetools` 실행

### **이번 주**
- [ ] Locust 부하 테스트 실행
- [ ] 병목 지점 파악 (프로파일링)
- [ ] Redis 캐싱 확대 (게시글, 댓글)
- [ ] DB 인덱스 추가

### **다음 주**
- [ ] N+1 쿼리 제거
- [ ] Prometheus + Grafana 대시보드 구축
- [ ] WebSocket 분산 처리 (Redis Pub/Sub)

### **이번 달**
- [ ] K6 시나리오 테스트
- [ ] Auto Scaling 설정 (Kubernetes HPA)
- [ ] CDN 도입 (정적 파일)

---

## 🔧 실행 방법

### **1. 의존성 설치**
```bash
pip install cachetools
```

### **2. 서버 재시작**
```bash
uvicorn app.main:app --reload
```

### **3. 부하 테스트 실행**
```bash
# Locust 설치
pip install locust

# 테스트 실행
locust -f tests/load_test.py --host=http://localhost:5000
```

### **4. 메트릭 확인**
```bash
# Prometheus 메트릭 조회
curl http://localhost:5000/metrics

# 애플리케이션 정보
curl http://localhost:5000/info
```

---

## 📌 참고 자료

1. **FastAPI 성능 최적화**
   - https://fastapi.tiangolo.com/advanced/async-sql-databases/
   - https://fastapi.tiangolo.com/tutorial/dependencies/

2. **SQLAlchemy Connection Pool**
   - https://docs.sqlalchemy.org/en/20/core/pooling.html

3. **Redis 분산 캐싱**
   - https://redis.io/docs/manual/pubsub/

4. **Locust 부하 테스트**
   - https://docs.locust.io/en/stable/

5. **Prometheus 메트릭**
   - https://prometheus.io/docs/practices/naming/

---

## ✅ 결론

**현재 개선한 사항:**
1. ✅ WebSocket DB 세션 안전성 향상
2. ✅ 메모리 누수 방지
3. ✅ CSV 로딩 최적화

**예상 효과:**
- 안정성 향상 (DB 커넥션 누수 방지)
- 메모리 사용량 제한 (OOM 방지)
- 서버 시작 속도 개선

**다음 단계:**
1. 부하 테스트로 실제 병목 지점 파악
2. Redis 캐싱 확대
3. DB 쿼리 최적화
4. WebSocket 분산 처리

지금까지의 개선으로 **기본적인 안정성과 리소스 관리**는 확보했습니다.  
이제 **부하 테스트를 통해 실제 병목을 찾아내고**, 데이터 기반으로 최적화하면 됩니다! 🚀
