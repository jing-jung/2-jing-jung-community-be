from fastapi import File, UploadFile, Form, APIRouter, HTTPException, Response, Request, Depends
from app.schemas.model import (
    UserCreate, UserLogin, PostCreate, PostUpdate, CommonResponse,
    UserResponse, CommentCreate
)

from app.services.services import (
    create_user, login_user, get_user_by_id, delete_user,
    get_post_list, create_post, get_post, update_post, delete_post,
    get_comments_by_post_id, create_comment, delete_comment,
    toggle_like, check_is_liked, get_current_like_count, get_user_profile_image_by_nickname
)

router = APIRouter()


def get_current_user(request: Request):
    user_id_str = request.cookies.get("user_id")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Log in required")
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired")
    return user


# --- 회원 API ---

@router.post("/users/signup", status_code=201)
def signup_api(
        email: str = Form(...),
        password: str = Form(..., min_length=8),
        nickname: str = Form(...),
        profile_image: UploadFile = File(None)
):
    image_filename = None
    if profile_image:
        image_filename = profile_image.filename

    user_data = UserCreate(
        email=email,
        password=password,
        nickname=nickname,
        profile_image=image_filename
    )
    result = create_user(user_data)
    if not result:
        raise HTTPException(status_code=409, detail="Email already exists")
    return CommonResponse(message="User registered", data=result)


@router.post("/users/login", status_code=200)
def login_api(data: UserLogin, response: Response):
    user = login_user(data)
    if not user:
        raise HTTPException(status_code=401, detail="Login failed")
    response.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
    return CommonResponse(message="Login successful", data=None)


@router.post("/users/logout", status_code=200)
def logout_api(response: Response):
    response.delete_cookie("user_id")
    return CommonResponse(message="Logout successful", data=None)


@router.get("/users/{id}", status_code=200)
def get_user_api(id: int):
    user = get_user_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_response = UserResponse(**user)
    return CommonResponse(message="User retrieved successfully", data=user_response)


@router.delete("/users/me", status_code=200)
def delete_my_account_api(response: Response, user: dict = Depends(get_current_user)):
    result = delete_user(user)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    response.delete_cookie("user_id")
    return CommonResponse(message="User deleted successfully", data=None)


@router.delete("/users/{id}", status_code=200)
def delete_user_by_id_api(id: int):
    user = get_user_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    delete_user(user)
    return CommonResponse(message="User deleted successfully", data=None)


# --- 게시글 API ---

@router.get("/posts", status_code=200)
def get_posts_api(page: int = 1, size: int = 10):
    if page < 1 or size < 1:
        raise HTTPException(status_code=400, detail="Invalid page or size parameter")
    posts = get_post_list(page, size)
    return CommonResponse(message="Posts retrieved successfully", data=posts)


@router.post("/posts", status_code=201)
def create_post_api(post: PostCreate, user: dict = Depends(get_current_user)):
    new_post = create_post(post, user["nickname"])
    return CommonResponse(message="Post created successfully", data=new_post)


@router.get("/posts/{post_id}", status_code=200)
def get_post_api(post_id: int, user: dict = Depends(get_current_user)):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    is_liked = check_is_liked(user["id"], post_id)

    response_data = post.copy()
    response_data["is_liked"] = is_liked

    response_data["writer_profile_image"] = get_user_profile_image_by_nickname(post["writer"])

    return CommonResponse(message="Post retrieved successfully", data=response_data)


@router.patch("/posts/{post_id}", status_code=200)
def update_post_api(post_id: int, update_data: PostUpdate, user: dict = Depends(get_current_user)):
    result = update_post(post_id, update_data, user["nickname"])
    if result is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if result == "FORBIDDEN":
        raise HTTPException(status_code=403, detail="Permission denied")
    return CommonResponse(message="Post updated successfully", data=result)


@router.delete("/posts/{post_id}", status_code=200)
def delete_post_api(post_id: int, user: dict = Depends(get_current_user)):
    result = delete_post(post_id, user["nickname"])
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    if result == "FORBIDDEN":
        raise HTTPException(status_code=403, detail="Permission denied")
    return CommonResponse(message="Post deleted successfully", data=None)


@router.post("/posts/{post_id}/like", status_code=200)
def like_post_api(post_id: int, user: dict = Depends(get_current_user)):
    result = toggle_like(post_id, user["id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Post not found")

    msg = "Post liked" if result == "LIKED" else "Post unliked"

    current_count = get_current_like_count(post_id)

    return CommonResponse(message=msg, data={"current_like_count": current_count})


# --- 댓글 API  ---

@router.get("/comments/{post_id}", status_code=200)
def get_comments_api(post_id: int):
    if not get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    comments = get_comments_by_post_id(post_id)
    return CommonResponse(message="Comments retrieved successfully", data=comments)


@router.post("/comments/{post_id}", status_code=201)
def create_comment_api(post_id: int, comment: CommentCreate, user: dict = Depends(get_current_user)):
    if not get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")

    comment_data = {
        "post_id": post_id,
        "user_id": user["id"],
        "content": comment.content
    }
    result = create_comment(comment_data)
    return CommonResponse(message="Comment created", data=result)


@router.delete("/comments/{comment_id}", status_code=200)
def delete_comment_api(comment_id: int, user: dict = Depends(get_current_user)):
    result = delete_comment(comment_id, user["id"])
    if result == False:
        raise HTTPException(status_code=404, detail="Comment not found")
    if result == "FORBIDDEN":
        raise HTTPException(status_code=403, detail="Permission denied")
    return CommonResponse(message="Comment deleted", data=None)