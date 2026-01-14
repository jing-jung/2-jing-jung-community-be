from datetime import datetime
from app.model import UserCreate, UserLogin, PostCreate, PostUpdate

users_db = []
posts_db = []

# 회원(User) 관련 함수들

def create_user(user: UserCreate):
    for u in users_db:
        if u["email"] == user.email:
            return False

    new_user = user.dict()
    new_user["id"] = len(users_db) + 1
    users_db.append(new_user)
    return new_user


def login_user(data: UserLogin):
    for u in users_db:
        if u["email"] == data.email and u["password"] == data.password:
            return u
    return None


# 게시글(Post) 관련 함수들

def get_post_list(page: int, size: int):
    start = (page - 1) * size
    end = start + size
    return posts_db[start:end]


def create_post(post: PostCreate, writer: str):
    new_post = post.dict()
    new_post["id"] = len(posts_db) + 1
    new_post["writer"] = writer
    new_post["created_at"] = str(datetime.now())
    new_post["view_count"] = 0
    new_post["like_count"] = 0

    posts_db.append(new_post)
    return new_post


def get_post(post_id: int):
    for post in posts_db:
        if post["id"] == post_id:
            post["view_count"] += 1
            return post
    return None


def update_post(post_id: int, update_data: PostUpdate, nickname: str):
    for post in posts_db:
        if post["id"] == post_id:
            if post["writer"] != nickname:
                return "FORBIDDEN"

            if update_data.title: post["title"] = update_data.title
            if update_data.content: post["content"] = update_data.content
            if update_data.image_url: post["image_url"] = update_data.image_url
            return post
    return None


def delete_post(post_id: int, nickname: str):
    for i, post in enumerate(posts_db):
        if post["id"] == post_id:
            if post["writer"] != nickname:
                return "FORBIDDEN"
            del posts_db[i]
            return True
    return False