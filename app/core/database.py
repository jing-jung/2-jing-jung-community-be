"""
Database Connection with Advanced Features
- Connection Pooling
- Retry Logic
- Health Check
"""
from sqlalchemy import create_engine, event, exc, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import time
from app.core.config import settings
from app.core.logging import log


# SQLAlchemy Base
Base = declarative_base()


class DatabaseManager:
    """데이터베이스 연결 관리"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """
        데이터베이스 엔진 설정
        - Connection Pooling 최적화
        - 자동 재연결
        """
        try:
            self.engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=settings.DB_POOL_SIZE,  # 기본 연결 수
                max_overflow=settings.DB_MAX_OVERFLOW,  # 최대 초과 연결
                pool_timeout=settings.DB_POOL_TIMEOUT,  # 연결 대기 시간
                pool_recycle=settings.DB_POOL_RECYCLE,  # 연결 재활용 (1시간)
                pool_pre_ping=True,  # 연결 전 ping 테스트
                echo=settings.DEBUG,  # SQL 로깅
                connect_args={
                    "connect_timeout": 10,
                    "charset": "utf8mb4"
                }
            )
            
            # 연결 풀 이벤트 리스너
            @event.listens_for(self.engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                log.debug("Database connection established")
            
            @event.listens_for(self.engine, "checkout")
            def receive_checkout(dbapi_conn, connection_record, connection_proxy):
                # 연결 체크아웃 시 타임아웃 설정
                cursor = dbapi_conn.cursor()
                cursor.execute("SET SESSION wait_timeout=300")  # 5분
                cursor.execute("SET SESSION interactive_timeout=300")
                cursor.close()
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            log.info(f"✅ Database engine created - Pool size: {settings.DB_POOL_SIZE}, Max overflow: {settings.DB_MAX_OVERFLOW}")
            
        except Exception as e:
            log.error(f"❌ Database engine creation failed: {e}")
            raise
    
    def create_tables(self):
        """테이블 생성"""
        try:
            Base.metadata.create_all(bind=self.engine)
            log.info("✅ Database tables created/verified")
        except Exception as e:
            log.error(f"❌ Table creation failed: {e}")
            raise
    
    def get_db(self) -> Generator[Session, None, None]:
        """
        데이터베이스 세션 생성 (FastAPI Dependency)
        """
        db = self.SessionLocal()
        try:
            yield db
        except exc.SQLAlchemyError as e:
            log.error(f"Database session error: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    @contextmanager
    def session_scope(self):
        """
        Context Manager로 세션 관리
        
        사용 예:
        with db_manager.session_scope() as session:
            user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            log.error(f"Session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    async def health_check(self) -> bool:
        """
        데이터베이스 헬스 체크
        """
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            log.error(f"Database health check failed: {e}")
            return False
    
    def get_pool_status(self) -> dict:
        """커넥션 풀 상태 조회"""
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "max_overflow": settings.DB_MAX_OVERFLOW
        }
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            log.info("Database connections closed")


# 전역 데이터베이스 매니저
db_manager = DatabaseManager()


# FastAPI Dependency
def get_db() -> Generator[Session, None, None]:
    """FastAPI에서 사용할 DB 세션 의존성"""
    return db_manager.get_db()


# 재시도 로직을 가진 DB 작업 실행
def execute_with_retry(func, max_retries=3, delay=1):
    """
    데이터베이스 작업 재시도
    
    :param func: 실행할 함수
    :param max_retries: 최대 재시도 횟수
    :param delay: 재시도 간격(초)
    """
    for attempt in range(max_retries):
        try:
            return func()
        except exc.OperationalError as e:
            if attempt < max_retries - 1:
                log.warning(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay * (attempt + 1))  # 지수 백오프
            else:
                log.error(f"Database operation failed after {max_retries} attempts")
                raise
        except Exception as e:
            log.error(f"Unexpected error in database operation: {e}")
            raise
