"""
Structured Logging Setup
로그 레벨 자동 설정 및 JSON 포맷 지원
"""
import sys
from loguru import logger
from app.core.config import settings


def setup_logging():
    """
    구조화된 로깅 설정
    - 개발: 컬러풀한 콘솔 출력
    - 프로덕션: JSON 형식으로 파일 저장
    """
    # 기본 핸들러 제거
    logger.remove()
    
    # 콘솔 로거 (개발 환경)
    if not settings.is_production:
        logger.add(
            sys.stdout,
            format=settings.LOG_FORMAT,
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # 파일 로거 (프로덕션 환경 - JSON)
    if settings.is_production:
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            format="{time} {level} {message}",
            level=settings.LOG_LEVEL,
            rotation="500 MB",  # 500MB마다 로테이션
            retention="30 days",  # 30일 보관
            compression="zip",  # 압축
            serialize=True,  # JSON 형식
            enqueue=True,  # 비동기 로깅
        )
    
    # 에러 로거 (별도 파일)
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        format=settings.LOG_FORMAT,
        level="ERROR",
        rotation="100 MB",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    
    logger.info(f"Logging initialized - Environment: {settings.ENVIRONMENT}, Level: {settings.LOG_LEVEL}")


# 로거 인스턴스 export
log = logger
