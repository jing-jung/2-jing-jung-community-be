from fastapi import FastAPI
from app.routes import router

app = FastAPI()

# 아까 만든 routes.py의 기능들을 메인 앱에 등록
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Community Backend Server is Running!"}
