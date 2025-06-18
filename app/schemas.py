from pydantic import BaseModel, EmailStr
from typing import Optional

# Base común para herencia
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None  # ← Nuevo campo para nombre completo
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None

# Esquema para crear usuario (registro)
class UserCreate(BaseModel):
    username: str                     # único y obligatorio
    full_name: str                   # obligatorio
    email: EmailStr
    password: str
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None

# Esquema para login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Esquema para actualización parcial
class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None

# Esquema completo con ID
class User(UserBase):
    id: int

    class Config:
        from_attributes = True  # permite convertir desde SQLAlchemy

# Esquema de respuesta (sin password)
class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    email: EmailStr
    sports: Optional[str] = None
    description: Optional[str] = None
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True