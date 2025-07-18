from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str
    deportes_preferidos: Optional[str] = None
    descripcion: Optional[str] = None
    foto_url: Optional[str] = None
    video_url: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    sports: Optional[str] = None
    whatsapp: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    deportes_preferidos: Optional[str] = None
    descripcion: Optional[str] = None
    foto_url: Optional[str] = None
    video_url: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    sports: Optional[str] = None
    whatsapp: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    deportes_preferidos: Optional[str] = None
    descripcion: Optional[str] = None
    foto_url: Optional[str] = None
    video_url: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    profilePicture: Optional[str] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    sports: Optional[str] = None
    whatsapp: Optional[str] = None
    phone: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    deportes_preferidos: Optional[str] = None
    descripcion: Optional[str] = None
    foto_url: Optional[str] = None
    video_url: Optional[str] = None

    class Config:
        from_attributes = True

class UserCompatible(User):
    compatibility_score: Optional[float] = None
    common_sports: Optional[List[str]] = None

class LikeCreate(BaseModel):
    liked_user_id: int

class LikeResponse(BaseModel):
    id: int
    liker_id: int
    liked_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    other_user: User

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
