from fastapi import APIRouter, HTTPException, Response, Request, Depends
from app.model import UserCreate, UserLogin, PostCreate, PostUpdate, CommonResponse, PostResponse
from app.services import UserService, PostService

router = APIRouter()
user_service = UserService()
post_service = PostService()


def get_current_user(request: Request):
    user = request.cookies.get("user_id")
    if not user:
        raise HTTPException(status_code=401, detail="Log in required")
    return user


@router.post("/users/signup", status_code=201)
def signup(user: UserCreate):
    result = user_service.create_user(user)
    if not result:
        raise HTTPException(status_code=409, detail="Email already exists")

    return CommonResponse(message="signup_success", data=result)


@router.post("/users/login", status_code=200)
def login(data: UserLogin, response: Response):
    user = user_service.login(data)
    if not user:
        raise HTTPException(status_code=401, detail="Login failed")

    response.set_cookie(key="user_id", value=user["nickname"])
    return CommonResponse(message="login_success", data=None)


@router.post("/users/logout", status_code=200)
def logout(response: Response):
    response.delete_cookie("user_id")
    return CommonResponse(message="logout_success", data=None)


@router.get("/posts", status_code=200)
def get_posts(page: int = 1, size: int = 10):
    posts = post_service.get_list(page, size)
    return CommonResponse(message="get_posts_success", data=posts)


@router.post("/posts", status_code=201)
def create_post(post: PostCreate, nickname: str = Depends(get_current_user)):
    new_post = post_service.create_post(post, nickname)
    return CommonResponse(message="create_post_success", data=new_post)


@router.get("/posts/{post_id}", status_code=200)
def get_post(post_id: int):
    post = post_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return CommonResponse(message="get_post_success", data=post)


@router.patch("/posts/{post_id}", status_code=200)
def update_post(post_id: int, update_data: PostUpdate, nickname: str = Depends(get_current_user)):
    result = post_service.update_post(post_id, update_data, nickname)

    if result is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if result == "FORBIDDEN":
        raise HTTPException(status_code=403, detail="Permission denied")

    return CommonResponse(message="update_post_success", data=result)


@router.delete("/posts/{post_id}", status_code=200)
def delete_post(post_id: int, nickname: str = Depends(get_current_user)):
    result = post_service.delete_post(post_id, nickname)

    if result == False:
        # 게시글이 없거나 권한이 없어서 실패한 경우를 구분해야 하지만
        # 간단하게 여기서는 400 또는 404/403 처리 (서비스 로직 단순화로 인해 통일)
        raise HTTPException(status_code=400, detail="Delete failed")

    if result == "FORBIDDEN":
        raise HTTPException(status_code=403, detail="Permission denied")

    return CommonResponse(message="delete_post_success", data=None)