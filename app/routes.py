from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, Depends
from app.model import UserCreate, UserLogin, PostCreate, PostUpdate, CommonResponse

from app.services import (
    create_user, login_user,
    get_post_list, create_post, get_post, update_post, delete_post
)

router = APIRouter()


def get_current_user(request: Request):
    user = request.cookies.get("user_id")
    if not user:
        raise HTTPException(status_code=401, detail="Log in required")
    return user


# API 목록

@router.post("/users/signup", status_code=201)
def signup_api(user: UserCreate):
    result = create_user(user)
    if not result:
        raise HTTPException(status_code=409, detail="Email already exists")
    return CommonResponse(message="signup_success", data=result)


@router.post("/users/login", status_code=200)
def login_api(data: UserLogin, response: Response):
    user = login_user(data)  # 함수 바로 호출!
    if not user:
        raise HTTPException(status_code=401, detail="Login failed")

    response.set_cookie(key="user_id", value=user["nickname"])
    return CommonResponse(message="login_success", data=None)


@router.post("/users/logout", status_code=200)
def logout_api(response: Response):
    response.delete_cookie("user_id")
    return CommonResponse(message="logout_success", data=None)


@router.get("/posts", status_code=200)
def get_posts_api(page: int = 1, size: int = 10):
    posts = get_post_list(page, size)
    return CommonResponse(message="get_posts_success", data=posts)


@router.post("/posts", status_code=201)
def create_post_api(post: PostCreate, nickname: str = Depends(get_current_user)):
    new_post = create_post(post, nickname)
    return CommonResponse(message="create_post_success", data=new_post)


@router.get("/posts/{post_id}", status_code=200)
def get_post_api(post_id: int):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return CommonResponse(message="get_post_success", data=post)


@router.patch("/posts/{post_id}", status_code=200)
def update_post_api(post_id: int, update_data: PostUpdate, nickname: str = Depends(get_current_user)):
    result = update_post(post_id, update_data, nickname)
    if result is None: raise HTTPException(status_code=404, detail="Post not found")
    if result == "FORBIDDEN": raise HTTPException(status_code=403, detail="Permission denied")
    return CommonResponse(message="update_post_success", data=result)


@router.delete("/posts/{post_id}", status_code=200)
def delete_post_api(post_id: int, nickname: str = Depends(get_current_user)):
    result = delete_post(post_id, nickname)
    if result == False: raise HTTPException(status_code=404, detail="Post not found")
    if result == "FORBIDDEN": raise HTTPException(status_code=403, detail="Permission denied")
    return CommonResponse(message="delete_post_success", data=None)