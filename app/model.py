from pydantic import BaseModel, Field
from typing import Optional, List


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




class CommonResponse(BaseModel):
    message: str
    data: Optional[object] = None