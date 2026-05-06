from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base # 👈 1. 여기 declarative_base 추가!
import os


# 2. 환경 변수에서 값 꺼내기
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT","3306")
db_name = os.getenv("DB_NAME")

# 3. URL 조합하기
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True  # 연결이 끊겼는지 확인 후 다시 연결하는 옵션
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()