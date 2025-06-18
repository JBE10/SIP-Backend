from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, auth, database
from .database import Base, engine
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ✅ CORS
origins = [
    "https://sip-gray.vercel.app",
    "https://sportsmatch.vercel.app",
    "https://sip-production.up.railway.app",
    "http://localhost:3000",
    "http://localhost:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔄 Crear tablas
print("🔄 Conectando a la base de datos...")
try:
    print("📋 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente!")
except Exception as e:
    print(f"❌ Error creando tablas: {e}")

# 🔗 Rutas
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {
        "message": "🏆 SportMatch API funcionando correctamente",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "register": "/auth/register",
            "login": "/auth/login",
            "me": "/users/me"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/me")
def get_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    return JSONResponse({
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "age": current_user.age,
        "location": current_user.location,
        "description": current_user.description,
        "profile_picture": current_user.profile_picture,
        "sports": current_user.sports or ""
    })

@app.put("/users/me", response_model=schemas.User)
def update_user(
        user_update: schemas.UserUpdate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/matches", response_model=List[schemas.User])
def get_matches(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    return []

@app.post("/upload-profile-picture")
async def upload_profile_picture(
        file: UploadFile = File(...),
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 5MB")

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"static/{unique_filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    profile_picture = f"https://web-production-07ed64.up.railway.app/static/{unique_filename}"
    db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
    db_user.profile_picture = profile_picture
    db.commit()
    db.refresh(db_user)

    return {"message": "Foto subida exitosamente", "profile_picture": profile_picture}

# 🖼️ Archivos estáticos
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")