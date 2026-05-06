from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import Optional
from app.db import get_db
from app.services import controllers
from pydantic import BaseModel

router = APIRouter()

# --- Pydantic Schemas (요청 데이터 검증용) ---
class UserLoginRequest(BaseModel):
    email: str
    password: str

class CommentRequest(BaseModel):
    content: str

class PasswordRequest(BaseModel):
    password: str

class NicknameRequest(BaseModel):
    nickname: str


# --- Routes ---
@router.post("/users/signup", status_code=201)
def signup(
    email: str = Form(...),
    password: str = Form(...),
    nickname: str = Form(...),
    profile_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    return controllers.signup_controller(email, password, nickname, profile_image, db)

@router.post("/users/login")
def login(req: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    return controllers.login_controller(req.email, req.password, response, db)

@router.post("/users/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    return controllers.logout_controller(request, response, db)

@router.get("/users/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    return controllers.get_me_controller(request, db)

@router.get("/users/email")
def check_email(email: str, db: Session = Depends(get_db)):
    return controllers.check_email_controller(email, db)

@router.patch("/users/{user_id}")
def update_nickname(
    user_id: int,
    request: Request,
    nickname: str = Form(...),                                # 🚀 JSON 대신 Form 데이터로 닉네임 받기
    profile_image: Optional[UploadFile] = File(None),         # 🚀 선택적으로 사진 파일 받기
    db: Session = Depends(get_db)
):
    return controllers.update_nickname_controller(user_id, nickname, profile_image, request, db)

@router.put("/users/me/password")
def update_password(req: PasswordRequest, request: Request, db: Session = Depends(get_db)):
    return controllers.update_password_controller(req.password, request, db)

@router.delete("/users/me")
def delete_user(request: Request, response: Response, db: Session = Depends(get_db)):
    return controllers.delete_user_controller(request, response, db)

# --- Posts ---

@router.get("/posts")
def get_posts(offset: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return controllers.get_posts_list_controller(offset, limit, db)

@router.post("/posts", status_code=201) # 프론트 경로 맞춤
def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    return controllers.create_post_controller(title, content, image, request, db)

@router.get("/posts/{post_id}")
def get_post_detail(post_id: int, request: Request, db: Session = Depends(get_db)):
    return controllers.get_post_detail_controller(post_id, request, db)

@router.put("/posts/{post_id}") # 프론트 경로 맞춤
def update_post(
    post_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    return controllers.update_post_controller(post_id, title, content, image, request, db)

@router.delete("/posts/{post_id}")
def delete_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    return controllers.delete_post_controller(post_id, request, db)

@router.post("/posts/{post_id}/like")
def like_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    return controllers.like_post_controller(post_id, request, db)

# --- Comments ---

@router.get("/posts/{post_id}/comments")
def get_comments(post_id: int, request: Request, db: Session = Depends(get_db)):
    return controllers.get_comments_controller(post_id, request, db)

@router.post("/posts/{post_id}/comments")
def create_comment(post_id: int, req: CommentRequest, request: Request, db: Session = Depends(get_db)):
    return controllers.create_comment_controller(post_id, req.content, request, db)

@router.put("/comments/{comment_id}")
def update_comment(comment_id: int, req: CommentRequest, request: Request, db: Session = Depends(get_db)):
    return controllers.update_comment_controller(comment_id, req.content, request, db)

@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, request: Request, db: Session = Depends(get_db)):
    return controllers.delete_comment_controller(comment_id, request, db)

# --- Chat ---
class ChatInitiateRequest(BaseModel):
    recipient_id: int

@router.get("/chats")
def get_chat_list(request: Request, db: Session = Depends(get_db)):
    return controllers.get_chat_list_controller(request, db)

@router.post("/chats")
def initiate_chat(req: ChatInitiateRequest, request: Request, db: Session = Depends(get_db)):
    return controllers.initiate_chat_controller(req.recipient_id, request, db)

@router.get("/chats/{room_id}/messages")
def get_messages(room_id: int, request: Request, db: Session = Depends(get_db)):
    return controllers.get_messages_controller(room_id, request, db)

# --- Map & Users ---
@router.get("/users/locations")
def get_users_locations(db: Session = Depends(get_db)):
    return controllers.get_all_users_locations_controller(db)

# --- 기차 (Train) ---
@router.post("/train/reserve")
def reserve_train(train_data: dict, request: Request, db: Session = Depends(get_db)):
    return controllers.reserve_train_controller(train_data, request, db)

@router.get("/train/reservations")
def get_my_train_reservations(request: Request, db: Session = Depends(get_db)):
    return controllers.get_my_train_reservations_controller(request, db)

@router.delete("/train/reservations/{reservation_id}")
def delete_train_reservation(reservation_id: int, request: Request, db: Session = Depends(get_db)):
    return controllers.delete_train_reservation_controller(reservation_id, request, db)

# --- Matching (Bio) ---
@router.get("/users/matching")
def get_matching_users(request: Request, db: Session = Depends(get_db)):
    return controllers.get_matching_users_controller(request, db)

@router.patch("/users/me/bio")
def update_bio(data: dict, request: Request, db: Session = Depends(get_db)):
    return controllers.update_bio_controller(data, request, db)

# --- 무 주식 (Turnip Market) ---
@router.get("/turnips/price")
def get_turnip_price():
    return controllers.get_turnip_price_controller()

@router.post("/turnips/trade")
def trade_turnips(trade_data: dict, request: Request, db: Session = Depends(get_db)):
    return controllers.trade_turnip_controller(trade_data, request, db)