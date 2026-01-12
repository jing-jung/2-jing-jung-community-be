from pydantic import BaseModel, Field
from typing import Optional, List

# ==========================
# 1. 회원 (User) 관련 모델
# ==========================

# 회원가입할 때 받는 데이터 (Body)
class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8, description="비밀번호는 최소 8자 이상")
    nickname: str
    profile_image: Optional[str] = None  # 없으면 None(null)

# 로그인할 때 받는 데이터 (Body)
class UserLogin(BaseModel):
    email: str
    password: str

# 회원정보 수정할 때 받는 데이터 (Body)
class UserUpdate(BaseModel):
    nickname: str = Field(..., max_length=10, description="닉네임은 최대 10자")

# ==========================
# 2. 게시글 (Post) 관련 모델
# ==========================

# 글 쓸 때 받는 데이터 (Body)
class PostCreate(BaseModel):
    title: str = Field(..., max_length=26, description="제목은 최대 26자")
    content: str
    image_url: Optional[str] = None

# 글 수정할 때 받는 데이터 (Body) - 제목/내용/이미지 중 일부만 보낼 수도 있음
class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=26)
    content: Optional[str] = None
    image_url: Optional[str] = None

# 글 조회할 때 돌려줄 데이터 (Response) - 강사님이 말한 "객체화"
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    writer: str
    view_count: int = 0
    like_count: int = 0
    created_at: str

# ==========================
# 3. 공통 응답 (Response)
# ==========================

class CommonResponse(BaseModel):
    message: str
    data: Optional[object] = None