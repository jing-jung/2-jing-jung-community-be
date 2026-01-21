from datetime import datetime
from app.schemas.model import UserCreate, UserLogin, PostCreate, PostUpdate

users_db = []
posts_db = []
comments_db = [
    {
        "id": 1,
        "post_id": 1,
        "user_id": 1,
        "content": "댓글 목록",
        "created_at": str(datetime.now())
    }
]
likes_db = []


# --- [1] 회원(User) 관련 함수 ---

def create_user(user: UserCreate):
    for u in users_db:
        if u["email"] == user.email:
            return False
    new_user = user.dict()
    new_user["id"] = len(users_db) + 1
    new_user["created_at"] = str(datetime.now())
    users_db.append(new_user)
    return new_user


def login_user(data: UserLogin):
    for u in users_db:
        if u["email"] == data.email and u["password"] == data.password:
            return u
    return None


def get_user_by_id(user_id: int):
    for u in users_db:
        if u["id"] == user_id:
            return {
                "id": u["id"],
                "email": u["email"],
                "nickname": u["nickname"],
                "created_at": u["created_at"]
            }
    return None


def delete_user(user: dict):
    user_id = user["id"]
    nickname = user["nickname"]

    for i in range(len(posts_db) - 1, -1, -1):
        if posts_db[i]["writer"] == nickname:
            post_id = posts_db[i]["id"]
            delete_comments_by_post_id(post_id)
            delete_likes_by_post_id(post_id)
            del posts_db[i]

    delete_comments_by_user_id(user_id)

    delete_likes_by_user_id(user_id)

    for i in range(len(users_db) - 1, -1, -1):
        if users_db[i]["id"] == user_id:
            del users_db[i]
            return True
    return False



def get_user_profile_image_by_nickname(nickname: str):
    for u in users_db:
        if u["nickname"] == nickname:
            return u.get("profile_image")
    return None


def delete_likes_by_user_id(user_id: int):
    for i in range(len(likes_db) - 1, -1, -1):
        if likes_db[i]["user_id"] == user_id:
            post_id = likes_db[i]["post_id"]
            for post in posts_db:
                if post["id"] == post_id:
                    post["like_count"] = max(0, post["like_count"] - 1)
                    break
            del likes_db[i]


def delete_likes_by_post_id(post_id: int):
    for i in range(len(likes_db) - 1, -1, -1):
        if likes_db[i]["post_id"] == post_id:
            del likes_db[i]



def toggle_like(post_id: int, user_id: int):
    target_post = None
    for post in posts_db:
        if post["id"] == post_id:
            target_post = post
            break
    if not target_post:
        return None

    like_record_index = -1
    for i, record in enumerate(likes_db):
        if record["user_id"] == user_id and record["post_id"] == post_id:
            like_record_index = i
            break

    if like_record_index > -1:
        del likes_db[like_record_index]
        target_post["like_count"] -= 1
        return "UNLIKED"
    else:
        likes_db.append({"user_id": user_id, "post_id": post_id})
        target_post["like_count"] += 1
        return "LIKED"


def check_is_liked(user_id: int, post_id: int) -> bool:
    for record in likes_db:
        if record["user_id"] == user_id and record["post_id"] == post_id:
            return True
    return False


def get_current_like_count(post_id: int) -> int:
    for post in posts_db:
        if post["id"] == post_id:
            return post["like_count"]
    return 0


# --- [2] 게시글(Post) 관련 함수 ---

def get_post_list(page: int, size: int):
    if page < 1 or size < 1:
        return []
    start = (page - 1) * size
    end = start + size
    paged_posts = posts_db[start:end]

    result = []
    for post in paged_posts:
        post_data = post.copy()

        comment_count = 0
        for c in comments_db:
            if c["post_id"] == post["id"]:
                comment_count += 1
        post_data["comment_count"] = comment_count

        post_data["writer_profile_image"] = get_user_profile_image_by_nickname(post["writer"])

        result.append(post_data)
    return result


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
            if update_data.title:
                post["title"] = update_data.title
            if update_data.content:
                post["content"] = update_data.content
            if update_data.image_url is not None:
                post["image_url"] = update_data.image_url
            return post
    return None


def delete_post(post_id: int, nickname: str):
    for i in range(len(posts_db) - 1, -1, -1):
        if posts_db[i]["id"] == post_id:
            if posts_db[i]["writer"] != nickname:
                return "FORBIDDEN"
            delete_comments_by_post_id(post_id)
            delete_likes_by_post_id(post_id)
            del posts_db[i]
            return True
    return False


# --- [3] 댓글(Comment) 관련 함수 ---

def get_comments_by_post_id(post_id: int):
    result = []
    for c in comments_db:
        if c["post_id"] == post_id:
            writer_nickname = "알 수 없음"
            for u in users_db:
                if u["id"] == c["user_id"]:
                    writer_nickname = u["nickname"]
                    break
            comment_data = {
                "id": c["id"],
                "nickname": writer_nickname,
                "content": c["content"],
                "created_at": c["created_at"]
            }
            result.append(comment_data)
    return result


def create_comment(comment_data: dict):
    new_comment = comment_data.copy()
    new_comment["id"] = len(comments_db) + 1
    new_comment["created_at"] = str(datetime.now())
    comments_db.append(new_comment)
    return new_comment


def delete_comment(comment_id: int, user_id: int):
    for i, c in enumerate(comments_db):
        if c["id"] == comment_id:
            if c["user_id"] != user_id:
                return "FORBIDDEN"
            del comments_db[i]
            return True
    return False


def delete_comments_by_post_id(post_id: int):
    for i in range(len(comments_db) - 1, -1, -1):
        if comments_db[i]["post_id"] == post_id:
            del comments_db[i]


def delete_comments_by_user_id(user_id: int):
    for i in range(len(comments_db) - 1, -1, -1):
        if comments_db[i]["user_id"] == user_id:
            del comments_db[i]