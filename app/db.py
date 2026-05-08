from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

print("--- Debugging app/db.py ---")
print(f"Current Working Directory: {os.getcwd()}")

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

# --- 로드된 값들을 상세히 출력 ---
print(f"DB_HOST: {host}")
print(f"DB_USER: {user}")
# 보안을 위해 비밀번호는 출력하지 않고, 로드되었는지 여부만 확인합니다.
print(f"DB_PASSWORD is loaded: {bool(password)}")
print(f"DB_PORT: {port}")
print(f"DB_NAME: {db_name}")
print("--------------------------")


# host, user, db_name이 하나라도 None이면 에러를 발생시키기 전에 멈추게 할 수 있습니다.
if not all([host, user, password, db_name]):
    print("CRITICAL ERROR: Database environment variables are not fully loaded.")
    # 개발 환경에서는 여기서 프로그램을 종료시키는 것도 방법입니다.
    # raise ValueError("Missing critical database environment variables.")

# URL 조합하기
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"

# 실제 연결에 사용될 URL을 (비밀번호를 가리고) 출력합니다.
print(f"SQLAlchemy Connection URL: mysql+pymysql://{user}:****@{host}:{port}/{db_name}")
print("--------------------------")


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