from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models
from . import database
from . import schemas
from .models import User
from app.schemas import User as UserSchema

router = APIRouter()

# JWT Configuration
SECRET_KEY = "clave-super-secreta"  # ⚠️ Cambiar en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.email)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "description": user.description,
            "sports": user.sports,
            "profile_picture": user.profile_picture,
            "age": user.age,
            "location": user.location
        }
    }


@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    existing_user = db.query(models.User).filter(models.User.email == str(user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    hashed_pw = get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=str(user.email),
        password=hashed_pw,
        sports=user.sports,
        description=user.description,
        profile_picture=user.profile_picture,
        age=user.age,
        location=user.location
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.email)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "name": new_user.username,
            "email": new_user.email,
            "description": new_user.description,
            "sports": new_user.sports,
            "profile_picture": new_user.profile_picture,
            "age": new_user.age,
            "location": new_user.location
        }
    }


@router.put("/profile/update")
def update_profile(
        user_update: schemas.UserUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return {
        "message": "Perfil actualizado correctamente",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "age": user.age,
            "location": user.location,
            "description": user.description,
            "profile_picture": user.profile_picture,
            "sports": user.sports
        }
    }

@router.get("/users/me")
def get_user_profile(current_user: UserSchema = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "age": current_user.age,
        "location": current_user.location,
        "description": current_user.description,
        "profile_picture": current_user.profile_picture,
        "sports": current_user.sports
    }
