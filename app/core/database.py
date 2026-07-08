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
    """
    데이터베이스 연결 관리 (Primary + Read Replica)
    - Primary: 쓰기 전용
    - Read Replica: 읽기 전용 (부하 분산)
    """
    
    def __init__(self):
        self.primary_engine = None
        self.read_replica_engine = None
        self.PrimarySession = None
        self.ReplicaSession = None
        self._setup_engines()
    
    def _setup_engines(self):
        """
        Primary 및 Read Replica 엔진 설정
        """
        try:
            # Primary DB (쓰기용)
            self.primary_engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE,
                pool_pre_ping=True,
                echo=settings.DEBUG,
                connect_args={
                    "connect_timeout": 10,
                    "charset": "utf8mb4"
                }
            )
            
            # Read Replica (읽기용) - 환경변수가 있으면 사용
            read_replica_url = settings.read_replica_url
            if read_replica_url:
                self.read_replica_engine = create_engine(
                    read_replica_url,
                    poolclass=QueuePool,
                    pool_size=settings.DB_POOL_SIZE * 2,  # 읽기가 많으므로 2배
                    max_overflow=settings.DB_MAX_OVERFLOW * 2,
                    pool_timeout=settings.DB_POOL_TIMEOUT,
                    pool_recycle=settings.DB_POOL_RECYCLE,
                    pool_pre_ping=True,
                    echo=settings.DEBUG,
                    connect_args={
                        "connect_timeout": 10,
                        "charset": "utf8mb4"
                    }
                )
                log.info(f"✅ Read Replica engine created - Pool size: {settings.DB_POOL_SIZE * 2}")
            else:
                # Read Replica가 없으면 Primary 사용
                self.read_replica_engine = self.primary_engine
                log.warning("⚠️ Read Replica not configured, using Primary for reads")
            
            # 연결 풀 이벤트 리스너
            @event.listens_for(self.primary_engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                log.debug("Primary DB connection established")
            
            @event.listens_for(self.primary_engine, "checkout")
            def receive_checkout(dbapi_conn, connection_record, connection_proxy):
                cursor = dbapi_conn.cursor()
                cursor.execute("SET SESSION wait_timeout=300")
                cursor.execute("SET SESSION interactive_timeout=300")
                cursor.close()
            
            # Session Factory
            self.PrimarySession = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.primary_engine
            )
            
            self.ReplicaSession = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.read_replica_engine
            )
            
            # 호환성을 위해 SessionLocal도 유지
            self.SessionLocal = self.PrimarySession
            self.engine = self.primary_engine
            
            log.info(f"✅ Database engines created - Primary pool: {settings.DB_POOL_SIZE}, Replica pool: {settings.DB_POOL_SIZE * 2}")
            
        except Exception as e:
            log.error(f"❌ Database engine creation failed: {e}")
            raise
    
    def get_session(self, read_only: bool = False) -> Session:
        """
        세션 생성 (읽기/쓰기 분리)
        :param read_only: True면 Read Replica 사용, False면 Primary 사용
        """
        if read_only:
            return self.ReplicaSession()
        else:
            return self.PrimarySession()
    
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
    def session_scope(self, read_only: bool = False):
        """
        Context Manager로 세션 관리 (Read/Write 분리)
        
        사용 예:
        # 읽기 전용 (Replica)
        with db_manager.session_scope(read_only=True) as session:
            posts = session.query(Post).all()
        
        # 쓰기 (Primary)
        with db_manager.session_scope() as session:
            session.add(new_post)
        """
        session = self.get_session(read_only=read_only)
        try:
            yield session
            if not read_only:
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
        """커넥션 풀 상태 조회 (Primary + Replica)"""
        primary_pool = self.primary_engine.pool
        replica_pool = self.read_replica_engine.pool
        
        return {
            "primary": {
                "pool_size": primary_pool.size(),
                "checked_in": primary_pool.checkedin(),
                "checked_out": primary_pool.checkedout(),
                "overflow": primary_pool.overflow(),
            },
            "replica": {
                "pool_size": replica_pool.size(),
                "checked_in": replica_pool.checkedin(),
                "checked_out": replica_pool.checkedout(),
                "overflow": replica_pool.overflow(),
            } if self.read_replica_engine != self.primary_engine else "same_as_primary"
        }
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.primary_engine:
            self.primary_engine.dispose()
        if self.read_replica_engine and self.read_replica_engine != self.primary_engine:
            self.read_replica_engine.dispose()
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
