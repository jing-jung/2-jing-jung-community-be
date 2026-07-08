# 🚀 로컬에서 AWS EKS 배포 가이드

## 📋 **사전 준비**

### 1. AWS CLI 설치 및 설정

```bash
# AWS CLI 설치 확인
aws --version

# AWS Configure 설정 (이미 되어 있음)
aws configure
# AWS Access Key ID: 입력
# AWS Secret Access Key: 입력
# Default region: ap-southeast-2
# Default output format: json

# 설정 확인
aws sts get-caller-identity
```

### 2. kubectl 설치 및 설정

```bash
# kubectl 설치 확인
kubectl version --client

# EKS 클러스터 연결
aws eks update-kubeconfig --region ap-southeast-2 --name community-eks-cluster

# 연결 확인
kubectl get nodes
```

### 3. Docker 설치 및 실행

```bash
# Docker 설치 확인
docker --version

# Docker 실행 확인
docker ps
```

---

## 🎯 **배포 방법**

### **방법 1: 자동 배포 스크립트 (권장)**

```bash
# 1. 환경 변수 설정 파일 생성
cp env.deploy.example .env.deploy

# 2. .env.deploy 파일 수정 (실제 값 입력)
nano .env.deploy
# 또는
code .env.deploy

# 3. 환경 변수 로드
source .env.deploy

# 4. 배포 스크립트 실행 권한 부여
chmod +x deploy.sh

# 5. 배포 실행
./deploy.sh
```

**스크립트가 자동으로 처리:**
- ✅ Docker 이미지 빌드
- ✅ ECR에 푸시
- ✅ EKS에 배포
- ✅ Rollout 상태 확인

---

### **방법 2: 수동 배포 (단계별)**

#### **Step 1: AWS 계정 확인**

```bash
# 현재 AWS 계정 확인
aws sts get-caller-identity

# 출력 예시:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }
```

#### **Step 2: Docker 이미지 빌드**

```bash
# 계정 ID 저장
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=ap-southeast-2
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Docker 이미지 빌드
docker build -t community-be:latest .

# 태그 지정
docker tag community-be:latest $ECR_REGISTRY/community-be:latest
docker tag community-be:latest $ECR_REGISTRY/community-be:v2.1.0
```

#### **Step 3: ECR 푸시**

```bash
# ECR 로그인
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# ECR Repository 생성 (없는 경우)
aws ecr create-repository --repository-name community-be --region $AWS_REGION

# 이미지 푸시
docker push $ECR_REGISTRY/community-be:latest
docker push $ECR_REGISTRY/community-be:v2.1.0
```

#### **Step 4: Kubernetes Secret 생성**

```bash
# 환경 변수 설정 (실제 값으로 수정)
export DB_HOST=your-rds-endpoint.rds.amazonaws.com
export DB_USER=admin
export DB_PASSWORD=your-secret-password
export DB_NAME=communitydb
export REDIS_HOST=redis-cluster.cache.amazonaws.com
export JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
export SESSION_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Secret 생성
kubectl create secret generic backend-secret \
  --from-literal=DB_HOST="$DB_HOST" \
  --from-literal=DB_USER="$DB_USER" \
  --from-literal=DB_PASSWORD="$DB_PASSWORD" \
  --from-literal=DB_NAME="$DB_NAME" \
  --from-literal=REDIS_HOST="$REDIS_HOST" \
  --from-literal=REDIS_PORT="6379" \
  --from-literal=JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  --from-literal=SESSION_SECRET_KEY="$SESSION_SECRET_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### **Step 5: Kubernetes 배포**

```bash
# EKS 연결
aws eks update-kubeconfig --region ap-southeast-2 --name community-eks-cluster

# 배포 파일 적용
kubectl apply -f k8s-production.yaml

# 이미지 업데이트 (새 버전 배포 시)
kubectl set image deployment/backend-deployment \
  backend-container=$ECR_REGISTRY/community-be:v2.1.0 \
  --record

# Rollout 상태 확인
kubectl rollout status deployment/backend-deployment

# Pod 상태 확인
kubectl get pods -l app=backend

# 로그 확인
kubectl logs -f deployment/backend-deployment
```

---

## 🔍 **배포 확인**

### 1. Pod 상태 확인

```bash
kubectl get pods -l app=backend

# 출력 예시:
# NAME                                  READY   STATUS    RESTARTS   AGE
# backend-deployment-5d7c8f9b8d-abc12   1/1     Running   0          2m
# backend-deployment-5d7c8f9b8d-def34   1/1     Running   0          2m
# backend-deployment-5d7c8f9b8d-ghi56   1/1     Running   0          2m
```

### 2. Service 확인

```bash
kubectl get svc backend-service

# 출력 예시:
# NAME              TYPE           CLUSTER-IP       EXTERNAL-IP                          PORT(S)
# backend-service   LoadBalancer   10.100.123.456   a1b2c3.ap-southeast-2.elb.amazonaws.com   80:30123/TCP
```

### 3. Health Check

```bash
# LoadBalancer URL 가져오기
SERVICE_URL=$(kubectl get svc backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Health Check
curl http://$SERVICE_URL/health
# 출력: {"status":"healthy","timestamp":"2024-01-..."}

# Ready Check
curl http://$SERVICE_URL/ready
# 출력: {"status":"ready","checks":{...}}
```

### 4. 로그 확인

```bash
# 실시간 로그
kubectl logs -f deployment/backend-deployment

# 특정 Pod 로그
kubectl logs backend-deployment-5d7c8f9b8d-abc12

# 최근 100줄
kubectl logs --tail=100 deployment/backend-deployment
```

---

## 🐛 **트러블슈팅**

### 문제 1: ECR 로그인 실패

```bash
# 에러: "no basic auth credentials"
# 해결: ECR 로그인 다시 시도
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-2.amazonaws.com
```

### 문제 2: kubectl 명령어 권한 없음

```bash
# 에러: "error: You must be logged in to the server"
# 해결: kubeconfig 업데이트
aws eks update-kubeconfig --region ap-southeast-2 --name community-eks-cluster
```

### 문제 3: Pod가 CrashLoopBackOff

```bash
# 로그 확인
kubectl logs <pod-name>

# Describe로 상세 정보 확인
kubectl describe pod <pod-name>

# 주요 원인:
# - DB 연결 실패: Secret 확인
# - Redis 연결 실패: Redis 서비스 확인
# - 환경 변수 누락: Secret 재생성
```

### 문제 4: Secret 생성 실패

```bash
# 기존 Secret 삭제 후 재생성
kubectl delete secret backend-secret

kubectl create secret generic backend-secret \
  --from-literal=DB_PASSWORD="your-password" \
  ...
```

---

## 🔄 **업데이트 배포**

### 코드 변경 후 배포

```bash
# 1. Git 커밋 & 푸시
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin main

# 2. 새 이미지 빌드 & 푸시
./deploy.sh

# 3. 배포 확인
kubectl rollout status deployment/backend-deployment
```

### 빠른 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/backend-deployment

# 특정 Revision으로 롤백
kubectl rollout history deployment/backend-deployment
kubectl rollout undo deployment/backend-deployment --to-revision=2
```

---

## 📊 **모니터링**

### Prometheus + Grafana

```bash
# Monitoring 배포
kubectl apply -f k8s-monitoring.yaml

# Grafana 접속
kubectl port-forward svc/grafana 3000:80

# 브라우저에서 접속
open http://localhost:3000
# ID: admin
# PW: admin (첫 로그인 후 변경)
```

### Metrics 확인

```bash
# Metrics 엔드포인트
curl http://$SERVICE_URL/metrics

# CPU/Memory 사용률
kubectl top pods
kubectl top nodes
```

---

## 🔐 **보안 체크리스트**

- [ ] AWS IAM 권한 최소화
- [ ] Kubernetes Secret 암호화 활성화
- [ ] RDS 보안 그룹 설정 (백엔드만 접근 가능)
- [ ] Redis 비밀번호 설정
- [ ] JWT/Session Secret 랜덤 생성
- [ ] .env.deploy 파일 .gitignore에 추가
- [ ] LoadBalancer에 SSL/TLS 인증서 설정
- [ ] Rate Limiting 활성화

---

## 📚 **참고 명령어**

```bash
# Pod 재시작
kubectl rollout restart deployment/backend-deployment

# Scale Out/In
kubectl scale deployment/backend-deployment --replicas=5

# ConfigMap 확인
kubectl get configmap

# Secret 확인 (값은 base64 인코딩)
kubectl get secret backend-secret -o yaml

# Namespace 변경
kubectl config set-context --current --namespace=production

# 전체 리소스 확인
kubectl get all
```

---

## 🎯 **다음 단계**

1. ✅ 로컬에서 배포 완료
2. 🔜 Secrets Manager 도입 (대기업 방식)
3. 🔜 CI/CD 파이프라인 구축 (OIDC)
4. 🔜 Multi-Region 배포
5. 🔜 Blue/Green 배포 전략

---

**마지막 업데이트**: 2024년 1월  
**버전**: v2.1.0
