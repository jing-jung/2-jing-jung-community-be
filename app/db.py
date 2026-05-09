from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# .env 파일 로드를 시도하고 결과를 출력합니다.
# load_dotenv()는 .env 파일을 찾으면 True, 못 찾으면 False를 반환합니다.
found_dotenv = load_dotenv()
print(f"Did dotenv find a .env file? {found_dotenv}")

# 환경 변수에서 값을 다시 확인합니다.
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT", "3306")
db_name = os.getenv("DB_NAME")

# host, user, db_name이 하나라도 None이면 에러를 발생시키기 전에 멈추게 할 수 있습니다.
if not all([host, user, password, db_name]):
    print("CRITICAL ERROR: Database environment variables are not fully loaded.")
    # 개발 환경에서는 여기서 프로그램을 종료시키는 것도 방법입니다.
    # raise ValueError("Missing critical database environment variables.")

# URL 조합하기
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()