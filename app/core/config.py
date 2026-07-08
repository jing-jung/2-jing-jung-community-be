"""
Application Configuration
환경변수 관리 및 설정 중앙화
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Community Platform"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "communitydb")
    
    # Read Replica (읽기 전용) - 선택적
    READ_REPLICA_HOST: str = os.getenv("READ_REPLICA_HOST", "")
    READ_REPLICA_PORT: str = os.getenv("READ_REPLICA_PORT", "3306")
    READ_REPLICA_URL: str = os.getenv("READ_REPLICA_URL", "")  # 직접 URL 제공 가능
    
    # Database Pool Settings (대규모 트래픽 대응)
    DB_POOL_SIZE: int = 20  # 기본 연결 풀 크기
    DB_MAX_OVERFLOW: int = 40  # 초과 시 최대 연결 수
    DB_POOL_TIMEOUT: int = 30  # 연결 대기 시간
    DB_POOL_RECYCLE: int = 3600  # 연결 재활용 시간 (1시간)
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_URL: str = os.getenv(
        "REDIS_URL", 
        f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
    
    # Session
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "your-super-secret-key-change-this")
    SESSION_EXPIRE_SECONDS: int = 86400  # 24시간
    
    # JWT (새로 추가)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-change-this")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]
    
    # AWS
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-2")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100  # 100 requests
    RATE_LIMIT_PERIOD: int = 60  # per minute
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    @property
    def database_url(self) -> str:
        """주 데이터베이스 URL (Primary)"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def read_replica_url(self) -> str:
        """
        Read Replica URL
        - READ_REPLICA_URL이 설정되어 있으면 사용
        - 없으면 READ_REPLICA_HOST로 생성
        - 둘 다 없으면 Primary 사용
        """
        if self.READ_REPLICA_URL:
            return self.READ_REPLICA_URL
        elif self.READ_REPLICA_HOST:
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.READ_REPLICA_HOST}:{self.READ_REPLICA_PORT}/{self.DB_NAME}"
        else:
            return None  # Primary 사용
    
    @property
    def async_database_url(self) -> str:
        """Async SQLAlchemy Database URL (Primary)"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """싱글톤 패턴으로 설정 반환"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()
