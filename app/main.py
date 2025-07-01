from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import models
from . import schemas
from . import auth
from . import database
from .database import Base, engine
from fastapi.staticfiles import StaticFiles
import os
import uuid
import shutil
from dotenv import load_dotenv
import bcrypt
from fastapi.security import OAuth2PasswordRequestForm

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Crear las tablas en la base de datos - CON LOGGING
print("🔄 Conectando a la base de datos...")
try:
    print("📋 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente!")
except Exception as e:
    print(f"❌ Error creando tablas: {e}")

# CORS para permitir conexión desde Vercel y Railway
origins = [
    "https://sip-gray.vercel.app",
    "https://sportsmatch.vercel.app",
    "https://sip-production.up.railway.app",
    "http://localhost:3000",
    "http://localhost:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas de autenticación
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Endpoint raíz para verificar que la API funciona
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

# Endpoint de health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

# Endpoint de prueba para diagnosticar problemas
@app.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    try:
        # Intentar hacer una consulta simple
        result = db.execute("SELECT 1")
        return {"status": "success", "message": "Base de datos funcionando correctamente"}
    except Exception as e:
        return {"status": "error", "message": f"Error en base de datos: {str(e)}"}

# Endpoint para verificar variables de entorno
@app.get("/test-env")
def test_environment_variables():
    return {
        "status": "success",
        "environment_variables": {
            "BASE_URL": os.getenv("BASE_URL", "No definido"),
            "DATABASE_URL": os.getenv("DATABASE_URL", "No definido")[:20] + "..." if os.getenv("DATABASE_URL") else "No definido",
            "SECRET_KEY": "Definido" if os.getenv("SECRET_KEY") else "No definido",
            "NODE_ENV": os.getenv("NODE_ENV", "No definido"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "No definido"),
            "RAILWAY_PROJECT_ID": os.getenv("RAILWAY_PROJECT_ID", "No definido"),
        },
        "current_base_url": BASE_URL
    }

# Endpoint para verificar archivos en static
@app.get("/test-static")
def test_static_files():
    try:
        static_dir = "static"
        if not os.path.exists(static_dir):
            return {"status": "error", "message": "Carpeta static no existe"}
        
        files = []
        for filename in os.listdir(static_dir):
            file_path = os.path.join(static_dir, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                # Configuración dinámica de URL basada en el entorno
                base_url = BASE_URL
                
                files.append({
                    "name": filename,
                    "size": file_size,
                    "size_mb": round(file_size / (1024*1024), 2),
                    "url": f"{base_url}/static/{filename}"
                })
        
        return {
            "status": "success", 
            "static_dir": static_dir,
            "file_count": len(files),
            "files": files
        }
    except Exception as e:
        return {"status": "error", "message": f"Error al verificar archivos: {str(e)}"}

# Endpoint para verificar la estructura de la base de datos
@app.get("/test-db-structure")
def test_database_structure(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        
        # Verificar si la tabla users existe
        result = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"))
        table_exists = result.scalar()
        
        if not table_exists:
            return {"status": "error", "message": "La tabla 'users' no existe"}
        
        # Obtener información de las columnas
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """))
        columns = [{"name": row[0], "type": row[1], "nullable": row[2]} for row in result.fetchall()]
        
        # Verificar específicamente la columna video_url
        video_url_exists = any(col["name"] == "video_url" for col in columns)
        
        return {
            "status": "success",
            "table_exists": table_exists,
            "video_url_exists": video_url_exists,
            "columns": columns
        }
    except Exception as e:
        return {"status": "error", "message": f"Error al verificar estructura de BD: {str(e)}"}

# Endpoint de prueba para subir archivos sin autenticación
@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    print(f"🧪 Test upload: {file.filename}")
    print(f"📊 Tipo: {file.content_type}")
    
    try:
        content = await file.read()
        file_size = len(content)
        print(f"📏 Tamaño: {file_size} bytes")
        
        # Generar nombre único
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"test_{uuid.uuid4()}.{file_extension}"
        file_path = f"static/{unique_filename}"
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Verificar que se guardó
        if os.path.exists(file_path):
            actual_size = os.path.getsize(file_path)
            print(f"✅ Test file guardado: {actual_size} bytes")
            
            # Configuración dinámica de URL basada en el entorno
            base_url = BASE_URL
            
            test_url = f"{base_url}/static/{unique_filename}"
            return {
                "status": "success",
                "filename": unique_filename,
                "size": actual_size,
                "url": test_url
            }
        else:
            print(f"❌ Test file no se guardó")
            return {"status": "error", "message": "No se pudo guardar el archivo"}
            
    except Exception as e:
        print(f"❌ Error en test upload: {str(e)}")
        return {"status": "error", "message": str(e)}

# Rutas de usuarios
@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

@app.put("/users/me", response_model=schemas.User)
def update_user(
    user_update: schemas.UserUpdate,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Actualizar campos
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# Rutas de matches
@app.get("/matches", response_model=List[schemas.User])
def get_matches(
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Aquí iría la lógica para obtener los matches
    # Por ahora, devolvemos una lista vacía
    return []

# Nuevos endpoints para el sistema de matching
@app.get("/users/compatible")
def get_compatible_users(
    limit: int = 20,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene usuarios compatibles para el usuario actual
    """
    from . import matching
    
    try:
        # Obtener el usuario actual de la base de datos
        db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Obtener usuarios compatibles
        compatible_users = matching.get_compatible_users(db, db_user, limit)
        
        # Convertir a formato de respuesta
        response = []
        for item in compatible_users:
            user_data = {
                "id": item["user"].id,
                "username": item["user"].username,
                "name": item["user"].name or item["user"].username,
                "age": item["user"].age,
                "location": item["user"].location,
                "bio": item["user"].bio or item["user"].descripcion or "",
                "foto_url": item["user"].foto_url,
                "video_url": item["user"].video_url,
                "sports": item["user"].sports or item["user"].deportes_preferidos or "",
                "compatibility_score": round(item["compatibility_score"], 1),
                "common_sports": item["common_sports"]
            }
            response.append(user_data)
        
        return {
            "status": "success",
            "users": response,
            "total": len(response)
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo usuarios compatibles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/users/like/{user_id}")
def like_user(
    user_id: int,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Da like a un usuario y verifica si hay match
    """
    from . import matching
    
    try:
        # Verificar que el usuario existe
        target_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar que no se está dando like a sí mismo
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="No puedes darte like a ti mismo")
        
        # Verificar que no se le dio like antes
        existing_like = db.query(models.Like).filter(
            models.Like.liker_id == current_user.id,
            models.Like.liked_id == user_id
        ).first()
        
        if existing_like:
            raise HTTPException(status_code=400, detail="Ya le diste like a este usuario")
        
        # Crear el like
        like = matching.create_like(db, current_user.id, user_id)
        
        # Verificar si hay match
        match = db.query(models.Match).filter(
            (models.Match.user1_id == current_user.id) & (models.Match.user2_id == user_id)
        ).first()
        
        if not match:
            match = db.query(models.Match).filter(
                (models.Match.user1_id == user_id) & (models.Match.user2_id == current_user.id)
            ).first()
        
        return {
            "status": "success",
            "message": "Like registrado exitosamente",
            "is_match": match is not None,
            "match_id": match.id if match else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error dando like: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/users/dislike/{user_id}")
def dislike_user(
    user_id: int,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra un dislike (no mostrar más este usuario)
    """
    try:
        # Verificar que el usuario existe
        target_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar que no se está rechazando a sí mismo
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="No puedes rechazarte a ti mismo")
        
        # Verificar que no se le dio dislike antes
        existing_like = db.query(models.Like).filter(
            models.Like.liker_id == current_user.id,
            models.Like.liked_id == user_id
        ).first()
        
        if existing_like:
            raise HTTPException(status_code=400, detail="Ya interactuaste con este usuario")
        
        # Crear el dislike (se registra como like pero se usa para filtrar)
        like = models.Like(liker_id=current_user.id, liked_id=user_id)
        db.add(like)
        db.commit()
        
        return {
            "status": "success",
            "message": "Usuario rechazado"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error rechazando usuario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/matches/list")
def get_user_matches(
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los matches del usuario actual
    """
    from . import matching
    
    try:
        matches = matching.get_user_matches(db, current_user.id)
        
        response = []
        for match in matches:
            # Determinar quién es el otro usuario
            other_user_id = match.user2_id if match.user1_id == current_user.id else match.user1_id
            other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
            
            if other_user:
                match_data = {
                    "id": match.id,
                    "created_at": match.created_at,
                    "other_user": {
                        "id": other_user.id,
                        "username": other_user.username,
                        "name": other_user.name,
                        "age": other_user.age,
                        "location": other_user.location,
                        "bio": other_user.bio,
                        "foto_url": other_user.foto_url,
                        "video_url": other_user.video_url,
                        "sports": other_user.sports
                    }
                }
                response.append(match_data)
        
        return {
            "status": "success",
            "matches": response,
            "total": len(response)
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo matches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# Rutas de archivos
@app.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    print(f"📸 Iniciando subida de foto: {file.filename}")
    print(f"📊 Tipo de archivo: {file.content_type}")
    print(f"👤 Usuario: {current_user.username}")
    
    # Verificar que sea una imagen
    if not file.content_type.startswith("image/"):
        print(f"❌ Tipo de archivo no válido: {file.content_type}")
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de imagen")
    
    # Verificar tamaño (5MB máximo)
    content = await file.read()
    file_size = len(content)
    print(f"📏 Tamaño del archivo: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
    
    if file_size > 5 * 1024 * 1024:
        print(f"❌ Archivo demasiado grande: {file_size / (1024*1024):.2f} MB")
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 5MB")
    
    # Generar nombre único para el archivo
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"static/{unique_filename}"
    
    print(f"💾 Guardando archivo en: {file_path}")
    
    try:
        # Guardar el archivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Verificar que el archivo se guardó
        if os.path.exists(file_path):
            actual_size = os.path.getsize(file_path)
            print(f"✅ Archivo guardado exitosamente. Tamaño: {actual_size} bytes")
        else:
            print(f"❌ Error: El archivo no se guardó en {file_path}")
            raise HTTPException(status_code=500, detail="Error al guardar el archivo")
        
        # Configuración dinámica de URL basada en el entorno
        base_url = BASE_URL
        
        # Actualizar la URL de la foto en la base de datos
        foto_url = f"{base_url}/static/{unique_filename}"
        print(f"🔗 URL de la foto: {foto_url}")
        
        db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        db_user.foto_url = foto_url
        db.commit()
        db.refresh(db_user)
        
        print(f"✅ Foto subida exitosamente para usuario {current_user.username}")
        return {"message": "Foto subida exitosamente", "foto_url": foto_url}
        
    except Exception as e:
        print(f"❌ Error al procesar foto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/upload-sport-video")
async def upload_sport_video(
    file: UploadFile = File(...),
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    print(f"🎥 Iniciando subida de video: {file.filename}")
    print(f"📊 Tipo de archivo: {file.content_type}")
    print(f"👤 Usuario: {current_user.username}")
    
    # Verificar que sea un video
    if not file.content_type.startswith("video/"):
        print(f"❌ Tipo de archivo no válido: {file.content_type}")
        raise HTTPException(status_code=400, detail="Solo se permiten archivos de video")
    
    # Verificar tamaño (50MB máximo para videos)
    content = await file.read()
    file_size = len(content)
    print(f"📏 Tamaño del archivo: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
    
    if file_size > 50 * 1024 * 1024:
        print(f"❌ Archivo demasiado grande: {file_size / (1024*1024):.2f} MB")
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande. Máximo 50MB")
    
    # Generar nombre único para el archivo
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"static/{unique_filename}"
    
    print(f"💾 Guardando archivo en: {file_path}")
    
    try:
        # Guardar el archivo
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Verificar que el archivo se guardó
        if os.path.exists(file_path):
            actual_size = os.path.getsize(file_path)
            print(f"✅ Archivo guardado exitosamente. Tamaño: {actual_size} bytes")
        else:
            print(f"❌ Error: El archivo no se guardó en {file_path}")
            raise HTTPException(status_code=500, detail="Error al guardar el archivo")
        
        # Configuración dinámica de URL basada en el entorno
        base_url = BASE_URL
        
        # Actualizar la URL del video en la base de datos
        video_url = f"{base_url}/static/{unique_filename}"
        print(f"🔗 URL del video: {video_url}")
        
        db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        db_user.video_url = video_url
        db.commit()
        db.refresh(db_user)
        
        print(f"✅ Video subido exitosamente para usuario {current_user.username}")
        return {"message": "Video subido exitosamente", "video_url": video_url}
        
    except Exception as e:
        print(f"❌ Error al procesar video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# Asegúrate de que la carpeta exista
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuración dinámica de URL basada en el entorno
def get_base_url():
    # Si BASE_URL está configurada, usarla
    base_url = os.getenv("BASE_URL")
    if base_url:
        return base_url
    
    # Si estamos en Railway, usar la URL de Railway
    railway_environment = os.getenv("RAILWAY_ENVIRONMENT")
    railway_project_id = os.getenv("RAILWAY_PROJECT_ID")
    port = os.getenv("PORT")
    
    # Si hay PORT definido (Railway), estamos en producción
    if port:
        return "https://web-production-07ed64.up.railway.app"
    
    # Si estamos en Railway pero no hay PORT, usar la URL conocida
    if railway_environment and railway_project_id:
        return "https://web-production-07ed64.up.railway.app"
    
    # Por defecto, usar localhost
    return "http://localhost:8000"

# Función para obtener la URL base
BASE_URL = get_base_url()

@app.post("/auth/register")
async def register(user_data: schemas.UserCreate):
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(models.User).filter(
            (models.User.email == user_data.email) | (models.User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Usuario o email ya existe")
        
        # Crear nuevo usuario
        hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
        
        new_user = models.User(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password.decode('utf-8'),  # Usar password (campo existente)
            hashed_password=hashed_password.decode('utf-8'),  # También guardar en nuevo campo
            name=user_data.name,
            age=user_data.age,
            location=user_data.location,
            bio=user_data.bio,
            descripcion=user_data.bio,  # También guardar en campo existente
            sports=user_data.sports,
            deportes_preferidos=user_data.sports,  # También guardar en campo existente
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generar token
        token = create_access_token(data={"sub": new_user.email})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "name": new_user.name or new_user.username,
                "age": new_user.age,
                "location": new_user.location,
                "bio": new_user.bio or new_user.descripcion or "",
                "foto_url": new_user.foto_url,
                "video_url": new_user.video_url,
                "sports": new_user.sports or new_user.deportes_preferidos or ""
            }
        }
    except Exception as e:
        print(f"Error en registro: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Buscar usuario por email o username
        user = db.query(models.User).filter(
            (models.User.email == form_data.username) | (models.User.username == form_data.username)
        ).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Verificar contraseña (usar password o hashed_password)
        password_to_check = user.hashed_password if user.hashed_password else user.password
        if not bcrypt.checkpw(form_data.password.encode('utf-8'), password_to_check.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Generar token
        token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name or user.username,
                "age": user.age,
                "location": user.location,
                "bio": user.bio or user.descripcion or "",
                "foto_url": user.foto_url,
                "video_url": user.video_url,
                "sports": user.sports or user.deportes_preferidos or ""
            }
        }
    except Exception as e:
        print(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
