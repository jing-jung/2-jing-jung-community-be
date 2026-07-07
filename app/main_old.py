import os
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.routers.routes import router
from app.routers.chat import router as chat_router
from fastapi.staticfiles import StaticFiles
import json
from typing import Dict
from datetime import datetime
from app.db import SessionLocal
from sqlalchemy import text
from app.db import engine
from app.models import model

model.Base.metadata.create_all(bind=engine)

app = FastAPI()
# app = FastAPI(root_path="/api")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, list[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_local(self, room_id: int, message: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)


manager = ConnectionManager()

# --- CORS 설정 ---
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://k8s-myprojectgroup-d8b90bd933-873831510.ap-southeast-2.elb.amazonaws.com",
    "http://172.20.173.239:80",
    "http://127.0.0.1:5500",
    "http://k8s-myprojectgroup-d8b90bd933-1244394196.ap-southeast-2.elb.amazonaws.com",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(chat_router)

# --- WebSocket Endpoint ---
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    db = SessionLocal()
    sender_id = None

    try:
        # 1. 쿠키에서 세션 토큰 가져오기
        token = websocket.cookies.get("session_id")

        if not token:
            await websocket.close(code=1008)
            return

        sql = text("SELECT data FROM sessions WHERE session_id = :session_id")
        result = db.execute(sql, {"session_id": token}).fetchone()

        if not result:
            await websocket.close(code=1008)
            return

        sender_id = int(result.data)

        # 2. 참여 권한 확인
        sql_check = text("SELECT id FROM chat_participants WHERE room_id = :room_id AND user_id = :user_id")
        if not db.execute(sql_check, {"room_id": room_id, "user_id": sender_id}).fetchone():
            await websocket.close(code=1008)
            return

        # 3. 로컬 커넥션 매니저에 등록
        await manager.connect(room_id, websocket)

        # 4. 메시지 수신 및 브로드캐스트
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            content = message_data.get("content")

            if content:
                insert_sql = text("""
                    INSERT INTO messages (room_id, sender_id, content, created_at, is_read)
                    VALUES (:room_id, :sender_id, :content, NOW(), 0)
                """)
                db.execute(insert_sql, {
                    "room_id": room_id,
                    "sender_id": sender_id,
                    "content": content
                })
                db.commit()

                response_message = {
                    "room_id": room_id,
                    "sender_id": sender_id,
                    "content": content,
                    "created_at": datetime.now().isoformat()
                }

                await manager.broadcast_to_local(room_id, json.dumps(response_message))

    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422,
                        content={"code": "INVALID_INPUT", "message": "입력값이 잘못되었습니다.", "detail": exc.errors()})


os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_root():
    return {"message": "Community Backend Server is Running!"}