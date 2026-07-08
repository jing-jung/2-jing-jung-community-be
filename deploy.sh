#!/bin/bash

# =============================================================================
# 로컬에서 AWS EKS로 직접 배포하는 스크립트
# 사용법: ./deploy.sh
# =============================================================================

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Community Backend 배포 시작${NC}"
echo "=================================================="

# =============================================================================
# 1. 환경 변수 확인
# =============================================================================
echo -e "${YELLOW}📋 환경 변수 확인 중...${NC}"

# AWS 계정 ID 자동 감지
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ AWS 자격증명을 찾을 수 없습니다.${NC}"
    echo "   aws configure를 실행하거나 AWS CLI를 설정하세요."
    exit 1
fi

echo -e "${GREEN}✅ AWS 계정: $AWS_ACCOUNT_ID${NC}"

# AWS Region (기본값: ap-southeast-2)
AWS_REGION=${AWS_REGION:-ap-southeast-2}
echo -e "${GREEN}✅ AWS Region: $AWS_REGION${NC}"

# ECR Repository
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
ECR_REPOSITORY="community-be"
IMAGE_TAG="v2.1.0-$(date +%Y%m%d-%H%M%S)"

echo -e "${GREEN}✅ ECR: $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG${NC}"

# EKS Cluster 이름 (필요시 수정)
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME:-community-eks-cluster}

# =============================================================================
# 2. Docker 이미지 빌드
# =============================================================================
echo ""
echo -e "${YELLOW}🐳 Docker 이미지 빌드 중...${NC}"

docker build -t $ECR_REPOSITORY:latest .
docker tag $ECR_REPOSITORY:latest $ECR_REGISTRY/$ECR_REPOSITORY:latest
docker tag $ECR_REPOSITORY:latest $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

echo -e "${GREEN}✅ Docker 이미지 빌드 완료${NC}"

# =============================================================================
# 3. ECR 로그인 및 푸시
# =============================================================================
echo ""
echo -e "${YELLOW}📤 ECR에 이미지 푸시 중...${NC}"

# ECR 로그인
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# ECR Repository가 없으면 생성
if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION > /dev/null 2>&1; then
    echo -e "${YELLOW}📦 ECR Repository 생성 중...${NC}"
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
fi

# 이미지 푸시
docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

echo -e "${GREEN}✅ ECR 푸시 완료${NC}"

# =============================================================================
# 4. EKS 배포 (선택 사항)
# =============================================================================
echo ""
read -p "EKS에 배포하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}☸️  EKS 배포 중...${NC}"
    
    # kubectl 설정
    aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
    
    # Kubernetes Secret 생성/업데이트 (환경변수에서 읽기)
    if [ ! -z "$DB_PASSWORD" ]; then
        echo -e "${YELLOW}🔐 Kubernetes Secret 업데이트 중...${NC}"
        kubectl create secret generic backend-secret \
          --from-literal=DB_HOST="${DB_HOST:-localhost}" \
          --from-literal=DB_USER="${DB_USER:-root}" \
          --from-literal=DB_PASSWORD="${DB_PASSWORD}" \
          --from-literal=DB_NAME="${DB_NAME:-communitydb}" \
          --from-literal=REDIS_HOST="${REDIS_HOST:-redis-service}" \
          --from-literal=REDIS_PORT="${REDIS_PORT:-6379}" \
          --from-literal=JWT_SECRET_KEY="${JWT_SECRET_KEY:-default-jwt-secret}" \
          --from-literal=SESSION_SECRET_KEY="${SESSION_SECRET_KEY:-default-session-secret}" \
          --from-literal=GROQ_API_KEY="${GROQ_API_KEY:-}" \
          --dry-run=client -o yaml | kubectl apply -f -
    else
        echo -e "${YELLOW}⚠️  환경변수가 설정되지 않았습니다. Secret은 수동으로 설정하세요.${NC}"
    fi
    
    # Deployment 업데이트
    kubectl set image deployment/backend-deployment \
      backend-container=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
      --record
    
    # Rollout 상태 확인
    echo -e "${YELLOW}⏳ Rollout 진행 중...${NC}"
    kubectl rollout status deployment/backend-deployment --timeout=5m
    
    echo -e "${GREEN}✅ EKS 배포 완료${NC}"
    
    # Pod 상태 확인
    echo ""
    echo -e "${YELLOW}📊 Pod 상태:${NC}"
    kubectl get pods -l app=backend
    
    # Service 확인
    echo ""
    echo -e "${YELLOW}🌐 Service 정보:${NC}"
    kubectl get svc backend-service
else
    echo -e "${YELLOW}⏭️  EKS 배포 건너뜀${NC}"
fi

# =============================================================================
# 5. 완료
# =============================================================================
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 배포 완료!${NC}"
echo ""
echo "배포된 이미지:"
echo "  - $ECR_REGISTRY/$ECR_REPOSITORY:latest"
echo "  - $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
echo ""
echo "다음 명령어로 확인:"
echo "  kubectl get pods"
echo "  kubectl logs -f deployment/backend-deployment"
echo "  kubectl get svc backend-service"
echo ""
