# 🏗️ Terraform Infrastructure

AWS EKS, RDS, ElastiCache, ECR 등 전체 인프라를 자동으로 구축합니다.

## 📋 구성 요소

| 리소스 | 설명 |
|--------|------|
| **VPC** | 3개 AZ에 걸친 Private/Public 서브넷 |
| **EKS** | Kubernetes 클러스터 (1.28) |
| **RDS** | MySQL 8.0 (Primary + Read Replica) |
| **ElastiCache** | Redis 7.0 (Multi-AZ) |
| **ECR** | Docker 이미지 저장소 |
| **Security Groups** | 리소스별 네트워크 격리 |
| **IAM Roles** | IRSA (Pod별 권한 관리) |

## 🚀 배포 방법

### 1. Terraform 설치

```bash
# Windows (Chocolatey)
choco install terraform

# 또는 다운로드
# https://www.terraform.io/downloads
```

### 2. AWS 자격증명 설정

```bash
aws configure
# AWS Access Key ID: [입력]
# AWS Secret Access Key: [입력]
# Default region: ap-southeast-2
```

### 3. 변수 파일 생성

```bash
# terraform 디렉토리로 이동
cd terraform

# 예제 파일 복사
cp terraform.tfvars.example terraform.tfvars

# terraform.tfvars 수정 (DB 비밀번호 등)
code terraform.tfvars
```

### 4. Terraform 초기화

```bash
terraform init
```

### 5. 인프라 미리보기

```bash
terraform plan
```

### 6. 인프라 배포 🚀

```bash
terraform apply
```

**예상 소요 시간**: 약 15~20분

## 📊 배포 후 확인

```bash
# 배포 정보 확인
terraform output

# kubectl 설정
aws eks update-kubeconfig --region ap-southeast-2 --name community-eks-cluster

# 노드 확인
kubectl get nodes

# 네임스페이스 확인
kubectl get ns
```

## 🔐 중요한 출력 값

```bash
# RDS 엔드포인트
terraform output rds_primary_endpoint

# Redis 엔드포인트
terraform output redis_endpoint

# ECR URL
terraform output ecr_repository_url

# 모든 배포 정보
terraform output deployment_info
```

## 💾 환경 변수 설정

```bash
# Terraform output을 .env.deploy에 자동 입력
cd ..
cat > .env.deploy <<EOF
export AWS_REGION=ap-southeast-2
export EKS_CLUSTER_NAME=community-eks-cluster
export DB_HOST=$(terraform -chdir=terraform output -raw rds_primary_endpoint | cut -d':' -f1)
export READ_REPLICA_HOST=$(terraform -chdir=terraform output -raw rds_replica_endpoint | cut -d':' -f1)
export DB_USER=admin
export DB_PASSWORD=YOUR_DB_PASSWORD
export DB_NAME=communitydb
export REDIS_HOST=$(terraform -chdir=terraform output -raw redis_endpoint)
export REDIS_PORT=6379
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export GROQ_API_KEY=""
EOF

# 환경 변수 로드
source .env.deploy
```

## 🗑️ 인프라 삭제

```bash
# 주의: 모든 리소스가 삭제됩니다!
terraform destroy
```

## 💰 예상 비용

| 리소스 | 인스턴스 타입 | 월 예상 비용 (USD) |
|--------|--------------|-------------------|
| EKS Control Plane | - | $73 |
| EKS Worker Nodes | t3.medium x2 | $60 |
| RDS Primary | db.t3.micro | $15 |
| RDS Replica | db.t3.micro | $15 |
| ElastiCache | cache.t3.micro x2 | $25 |
| NAT Gateway | - | $90 |
| **합계** | | **~$278/월** |

> **비용 절감 팁**:
> - 개발/테스트 시에는 `terraform.tfvars`에서 인스턴스 크기 축소
> - 사용하지 않을 때는 `terraform destroy`로 리소스 삭제
> - NAT Gateway 대신 NAT Instance 사용 (비용 절감)

## 📁 파일 구조

```
terraform/
├── provider.tf           # AWS Provider 설정
├── variables.tf          # 변수 정의
├── terraform.tfvars      # 실제 변수 값 (gitignore)
├── vpc.tf               # VPC, 서브넷, NAT Gateway
├── security_groups.tf   # 보안 그룹
├── eks.tf               # EKS 클러스터
├── rds.tf               # RDS MySQL
├── redis.tf             # ElastiCache Redis
├── ecr.tf               # ECR Repository
├── outputs.tf           # 출력 값
└── README.md            # 이 파일
```

## 🛠️ 트러블슈팅

### 문제 1: `terraform init` 실패

```bash
# Provider 다운로드 재시도
terraform init -upgrade
```

### 문제 2: EKS 생성 실패 (권한 부족)

```bash
# IAM 권한 확인
aws iam get-user
# AdministratorAccess 또는 EKS/EC2/VPC 관련 권한 필요
```

### 문제 3: RDS 비밀번호 요구사항

비밀번호는 다음 조건을 만족해야 합니다:
- 최소 8자 이상
- 영문자, 숫자 포함
- 특수문자 권장

### 문제 4: 리소스 할당량 초과

```bash
# EC2 인스턴스 한도 확인
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A

# 한도 증가 요청 (AWS Console에서)
```

## 📚 참고 자료

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EKS Module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest)
- [VPC Module](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
