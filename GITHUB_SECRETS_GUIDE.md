# 📝 GitHub Secrets 설정 가이드

## 🔐 필수 Secrets (Required)

GitHub Repository → Settings → Secrets and variables → Actions에서 설정하세요.

### **AWS 관련**
```
AWS_ROLE_ARN          # AWS IAM Role ARN (OIDC 인증용)
AWS_REGION            # ap-southeast-2 (또는 사용하는 리전)
AWS_ACCESS_KEY_ID     # AWS Access Key (또는 Role 사용)
AWS_SECRET_ACCESS_KEY # AWS Secret Key (또는 Role 사용)
```

### **Database 관련**
```
DB_HOST               # RDS 엔드포인트 (예: mydb.123456.ap-southeast-2.rds.amazonaws.com)
DB_USER               # admin
DB_PASSWORD           # your-secret-password
DB_NAME               # communitydb (선택적, 기본값 사용 가능)
```

### **Redis 관련 (선택적)**
```
REDIS_HOST            # redis-service (기본값: Kubernetes 내부 서비스명)
REDIS_PORT            # 6379 (기본값)
REDIS_PASSWORD        # Redis 비밀번호 (선택적)
```

### **보안 키**
```
JWT_SECRET_KEY        # JWT 토큰 서명 키 (랜덤 문자열 32자 이상)
SESSION_SECRET_KEY    # 세션 암호화 키 (랜덤 문자열 32자 이상)
```

### **AI 서비스 (선택적)**
```
GROQ_API_KEY          # Groq API Key (채팅 기능 사용 시)
```

### **Read Replica (선택적)**
```
READ_REPLICA_HOST     # Read Replica 엔드포인트
READ_REPLICA_PORT     # 3306 (기본값)
```

---

## 🚀 설정 방법

### 1. GitHub Repository 접속
```
https://github.com/jing-jung/2-jing-jung-community-be
```

### 2. Settings → Secrets and variables → Actions

### 3. "New repository secret" 클릭

### 4. 각 Secret 추가
- Name: 위의 키 이름 입력
- Secret: 실제 값 입력

---

## 🔑 Secret 생성 방법

### JWT_SECRET_KEY & SESSION_SECRET_KEY 생성
```bash
# Python으로 랜덤 키 생성
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 또는 OpenSSL로 생성
openssl rand -base64 32
```

### AWS Credentials 확인
```bash
# AWS CLI로 확인
aws sts get-caller-identity

# IAM Role ARN 확인
aws iam get-role --role-name your-role-name
```

### RDS Endpoint 확인
```bash
# AWS CLI로 RDS 엔드포인트 확인
aws rds describe-db-instances \
  --db-instance-identifier your-db-name \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

---

## ✅ 설정 확인

### Secrets가 올바르게 설정되었는지 확인:

1. **GitHub Actions 실행**
   - Push to main branch
   - Actions 탭에서 워크플로우 확인

2. **실패 시 로그 확인**
   ```
   GitHub Actions → 실패한 워크플로우 → 로그 확인
   ```

3. **Kubernetes에서 확인**
   ```bash
   # Secret 존재 확인
   kubectl get secret backend-secret
   
   # Secret 내용 확인 (base64 디코딩)
   kubectl get secret backend-secret -o json | \
     jq '.data | map_values(@base64d)'
   ```

---

## ⚠️ 보안 주의사항

1. **절대 코드에 하드코딩하지 마세요**
   ```python
   # ❌ 절대 금지
   DB_PASSWORD = "my-secret-password"
   
   # ✅ 환경 변수 사용
   DB_PASSWORD = os.getenv("DB_PASSWORD")
   ```

2. **Secret 값은 절대 로그에 출력하지 마세요**
   ```python
   # ❌ 절대 금지
   print(f"DB_PASSWORD: {DB_PASSWORD}")
   
   # ✅ 마스킹 처리
   print(f"DB_PASSWORD: {'*' * len(DB_PASSWORD)}")
   ```

3. **Secret 값은 Git에 커밋하지 마세요**
   - `.env` 파일은 `.gitignore`에 추가
   - 실수로 커밋했다면 즉시 Secret 변경

4. **주기적으로 Secret 갱신**
   - 3~6개월마다 비밀번호 변경
   - 퇴사자 발생 시 즉시 변경

---

## 🐛 트러블슈팅

### 문제: "secret not found" 에러
**해결:**
```bash
# Secret 이름 확인
kubectl get secrets

# Secret 다시 생성
kubectl delete secret backend-secret
kubectl create secret generic backend-secret --from-literal=DB_PASSWORD='new-password'
```

### 문제: GitHub Actions에서 Secrets 인식 못함
**해결:**
1. Repository Settings 확인
2. Secret 이름 대소문자 확인
3. 워크플로우 파일에서 `${{ secrets.DB_PASSWORD }}` 정확히 입력

### 문제: AWS 인증 실패
**해결:**
1. IAM Role 권한 확인
2. OIDC Provider 설정 확인
3. AWS_ROLE_ARN 정확성 확인

---

## 📋 체크리스트

배포 전 확인:

- [ ] AWS_ROLE_ARN 설정됨
- [ ] AWS_REGION 설정됨
- [ ] DB_HOST 설정됨
- [ ] DB_USER 설정됨
- [ ] DB_PASSWORD 설정됨
- [ ] JWT_SECRET_KEY 생성 및 설정됨
- [ ] SESSION_SECRET_KEY 생성 및 설정됨
- [ ] GROQ_API_KEY 설정됨 (채팅 기능 사용 시)
- [ ] All secrets는 base64 인코딩 **하지 않음** (GitHub가 자동 처리)

---

## 🔗 참고 링크

- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [AWS IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)

---

**마지막 업데이트**: 2024년 1월  
**버전**: v2.1.0
