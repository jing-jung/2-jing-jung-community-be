from pydantic import BaseModel, Field
from typing import Optional,Any

class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8, description="비밀번호는 최소 8자 이상")
    nickname: str
    profile_image: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    nickname: str = Field(..., max_length=10, description="닉네임은 최대 10자")

class UserCheck(BaseModel):
    email: str
    nickname: str
    created_at: str
    id: int

class UserDelete(BaseModel):
    id: int

class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    created_at: str



class CommentCreate(BaseModel):
    content: str

class CommentsCheck(BaseModel):
    id: int
    nickname: str
    created_at: str
    content: str

class CommentResponse(BaseModel):
    id: int
    nickname: str
    content: str
    created_at: str



class PostCreate(BaseModel):
    title: str = Field(..., max_length=26, description="제목은 최대 26자")
    content: str
    image_url: Optional[str] = None

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=26)
    content: Optional[str] = None
    image_url: Optional[str] = None

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    writer: str
    view_count: int = 0
    like_count: int = 0
    created_at: str
    comment_count: int = 0
    writer_profile_image: Optional[str] = None



class CommonResponse(BaseModel):
    message: str
    code: Optional[str] = None
    data: Optional[Any] = None
