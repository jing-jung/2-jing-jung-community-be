# =============================================================================
# Multi-Stage Docker Build for Production
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# 의존성 파일 복사
COPY pyproject.toml .

# 빌드 도구 설치 및 의존성 다운로드
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user .

# Stage 2: Runtime
FROM python:3.11-slim

# 보안: non-root 사용자 생성
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Builder에서 설치된 패키지 복사
COPY --from=builder /root/.local /home/appuser/.local

# 소스 코드 복사
COPY --chown=appuser:appuser . .

# 환경 변수
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=5000

# 로그 디렉토리 생성
RUN mkdir -p logs && chown appuser:appuser logs

# Static files 디렉토리
RUN mkdir -p static/images && chown -R appuser:appuser static

# 사용자 전환
USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# 포트 노출
EXPOSE 5000

# 실행 명령 (Production 최적화)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4", "--log-level", "info"]