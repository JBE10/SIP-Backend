from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True
