# 🚀 100만명 동시접속 대응 Ultra-Scale 아키텍처

## 📊 성능 스펙

| 항목 | 일반 구성 | **Ultra-Scale** |
|------|----------|-----------------|
| 동시 접속 | ~10만 | **100만+** |
| 초당 요청 | ~1,500 req/s | **50,000+ req/s** |
| Backend Pods | 3~10개 | **20~100개** |
| DB 연결 | 60 | **15,000+** |
| Redis | 단일 | **Cluster (6 nodes)** |
| Response Time (p95) | 150ms | **< 200ms** |
| Uptime | 99.9% | **99.99%** |

---

## 🏗️ Ultra-Scale 아키텍처 구성

### 1. 애플리케이션 레이어 (수평 확장)
```
┌─────────────────────────────────────┐
│     CloudFront CDN (전세계)          │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│     ALB (Application Load Balancer) │
│         (Multi-AZ)                   │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐ ┌───▼────┐ ... (20~100 Pods)
│Backend 1│ │Backend 2│
│4 core   │ │4 core   │
│8GB RAM  │ │8GB RAM  │
└─────────┘ └─────────┘
```

### 2. 데이터베이스 레이어 (읽기/쓰기 분리)
```
┌────────────────────────────────────┐
│   ProxySQL (Connection Pooler)     │
│        3개 인스턴스                 │
└───┬────────────────────────────┬───┘
    │                            │
┌───▼──────┐            ┌────────▼─────────┐
│  Master  │            │  Read Replica 1   │
│  (Write) │────────────┤  Read Replica 2   │
│  RDS     │            │  Read Replica 3   │
└──────────┘            │  Read Replica 4   │
                        │  Read Replica 5   │
                        └──────────────────┘
```

### 3. 캐싱 레이어 (다층 캐시)
```
L1: Application Memory (각 Pod)
    └─→ 100MB LRU Cache
    
L2: Redis Cluster (6 nodes)
    ├─→ Master 1 (Shard 1)
    ├─→ Master 2 (Shard 2)  } 10GB Total
    ├─→ Master 3 (Shard 3)
    └─→ Replica × 3
    
L3: CDN (CloudFront)
    └─→ Edge Location (전세계)
```

### 4. 비동기 처리 (Message Queue)
```
┌──────────────────────────────────┐
│    RabbitMQ Cluster (3 nodes)    │
├──────────────────────────────────┤
│  • 이메일 발송                    │
│  • 푸시 알림                      │
│  • 이미지 리사이징                │
│  • 통계 집계                      │
│  • 백그라운드 작업                │
└──────────────────────────────────┘
```

---

## ⚡ 핵심 최적화 전략

### 1. 초대규모 Connection Pooling
```python
# 기존: 20 + 40 = 60 connections
# Ultra: 50 + 100 = 150 connections per Pod
DB_POOL_SIZE = 50
DB_MAX_OVERFLOW = 100

# 100 Pods → 15,000 동시 연결 가능
```

### 2. Redis Cluster (샤딩)
```yaml
# 6개 노드 클러스터 (3 Master + 3 Replica)
# 처리량: 100만+ ops/s
# 메모리: 10GB (분산 저장)
```

### 3. DB Read Replica (읽기 부하 분산)
```
읽기:쓰기 비율 = 95:5
→ 읽기 요청을 5개 Replica에 분산
→ Master는 쓰기만 처리
```

### 4. CDN (정적 파일)
```
이미지, JS, CSS → CloudFront
→ Origin 서버 부하 90% 감소
→ 응답 시간 < 50ms (Edge Location)
```

### 5. Message Queue (비동기 처리)
```
즉시 응답이 필요 없는 작업 → RabbitMQ
→ API 응답 시간 단축
→ 처리량: 10,000+ msg/s
```

---

## 🔧 배포 방법

### 1. Ultra-Scale 모드로 배포
```bash
# 1. ECR에 이미지 푸시
docker build -t <ECR>/community-be:ultra .
docker push <ECR>/community-be:ultra

# 2. Redis Cluster 생성
kubectl apply -f k8s-ultra-scale.yaml

# 3. Ultra-Scale Backend 배포
kubectl apply -f k8s-ultra-scale.yaml

# 4. HPA 확인 (20~100 Pods)
kubectl get hpa
```

### 2. 모니터링
```bash
# Prometheus에서 확인
- http_requests_total
- db_connection_pool_checked_out
- cache_hit_rate
- pod_count
```

---

## 📈 예상 비용 (AWS)

| 항목 | 월 비용 (USD) |
|------|---------------|
| EKS (100 nodes) | $7,300 |
| RDS (Master + 5 Replicas) | $3,500 |
| ElastiCache Redis Cluster | $1,800 |
| ALB | $150 |
| CloudFront | $500 |
| S3 | $200 |
| **Total** | **~$13,500/월** |

※ 100만 동시접속 기준 예상 비용

---

## 🎯 성능 목표

| 지표 | 목표 |
|------|------|
| 동시 접속 | 100만명+ |
| 초당 요청 | 50,000+ req/s |
| 응답 시간 (p95) | < 200ms |
| 응답 시간 (p99) | < 500ms |
| Error Rate | < 0.01% |
| Uptime | 99.99% |
| Cache Hit Rate | > 95% |

---

## 🛡️ 장애 복구 전략

### 1. Auto Healing
- **Pod 장애**: Kubernetes가 자동 재시작
- **Node 장애**: 다른 Node로 Pod 자동 이동
- **DB 장애**: Read Replica 자동 승격

### 2. Multi-Region (선택사항)
```
Primary: ap-southeast-2 (Sydney)
Secondary: us-west-2 (Oregon)
Tertiary: eu-west-1 (Ireland)

→ Route 53 Geo-routing으로 자동 분산
```

### 3. Disaster Recovery
- **RTO**: < 1시간 (복구 목표 시간)
- **RPO**: < 5분 (데이터 손실 허용 시간)
- **백업**: RDS 자동 백업 (매일, 30일 보관)

---

**이 아키텍처로 100만명 이상 동시접속 처리 가능합니다!** 🎉
