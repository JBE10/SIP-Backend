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
from app.auth import pwd_context

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
@app.get("/users/me")
def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    # Función para parsear deportes
    def parse_sports(sports_str):
        if not sports_str:
            return []
        deportes = []
        for item in sports_str.split(","):
            item = item.strip()
            if "(" in item and ")" in item:
                # Formato: "Fútbol (Avanzado)"
                nombre, nivel = item.rsplit("(", 1)
                deportes.append({
                    "sport": nombre.strip(),
                    "level": nivel.replace(")", "").strip()
                })
            elif item:
                # Formato simple: "Fútbol"
                deportes.append({"sport": item, "level": "Principiante"})
        return deportes
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "age": current_user.age,
        "location": current_user.location,
        "descripcion": current_user.descripcion or "",
        "foto_url": current_user.foto_url,
        "video_url": current_user.video_url,
        "deportes_preferidos": current_user.deportes_preferidos or "",
        "sports": parse_sports(current_user.deportes_preferidos or "")  # Formato array para el frontend
    }

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
@app.get("/matches")
async def get_matches(
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"🔍 Obteniendo matches para usuario {current_user.id}")
        
        # Buscar todos los matches donde el usuario actual participa
        matches = db.query(models.Match).filter(
            (models.Match.user1_id == current_user.id) | 
            (models.Match.user2_id == current_user.id)
        ).all()
        
        match_users = []
        for match in matches:
            # Determinar quién es el otro usuario en el match
            other_user_id = match.user2_id if match.user1_id == current_user.id else match.user1_id
            
            # Obtener información del otro usuario
            other_user = db.query(models.User).filter(models.User.id == other_user_id).first()
            
            if other_user:
                # Parsear deportes del usuario
                def parse_sports(sports_str):
                    if not sports_str:
                        return []
                    deportes = []
                    for item in sports_str.split(","):
                        item = item.strip()
                        if "(" in item and ")" in item:
                            nombre, nivel = item.rsplit("(", 1)
                            deportes.append({
                                "sport": nombre.strip(),
                                "level": nivel.replace(")", "").strip()
                            })
                        elif item:
                            deportes.append({"sport": item, "level": "Principiante"})
                    return deportes
                
                match_user = {
                    "id": other_user.id,
                    "name": other_user.username,
                    "age": other_user.age or 25,
                    "location": other_user.location or "Buenos Aires",
                    "bio": other_user.descripcion or "Amante del deporte",
                    "foto_url": other_user.foto_url or "",
                    "video_url": other_user.video_url or "",
                    "sports": parse_sports(other_user.deportes_preferidos or ""),
                    "match_date": match.created_at.isoformat()
                }
                match_users.append(match_user)
        
        print(f"✅ Encontrados {len(match_users)} matches")
        return {"matches": match_users}
        
    except Exception as e:
        print(f"❌ Error obteniendo matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para obtener usuarios compatibles
@app.get("/users/compatible")
async def get_compatible_users_route(
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    # Parámetros de filtros
    min_age: int = 18,
    max_age: int = 65,
    location: str = None,
    sports: str = None,
    distance: int = 50
):
    try:
        print(f"🔍 Buscando usuarios compatibles para: {current_user.username}")
        print(f"📊 Filtros aplicados: edad {min_age}-{max_age}, ubicación: {location}, deportes: {sports}")
        
        # Función para parsear deportes
        def parse_sports(sports_str):
            if not sports_str:
                return []
            deportes = []
            for item in sports_str.split(","):
                item = item.strip()
                if "(" in item and ")" in item:
                    # Formato: "Fútbol (Avanzado)"
                    nombre, nivel = item.rsplit("(", 1)
                    deportes.append({
                        "sport": nombre.strip(),
                        "level": nivel.replace(")", "").strip()
                    })
                elif item:
                    # Formato simple: "Fútbol"
                    deportes.append({"sport": item, "level": "Principiante"})
            return deportes
        
        # Obtener todos los usuarios excepto el actual
        users = db.query(models.User).filter(models.User.id != current_user.id).all()
        
        # Parsear deportes filtrados
        filtered_sports = []
        if sports:
            filtered_sports = parse_sports(sports)
        
        compatible_users = []
        for user in users:
            # Aplicar filtro de edad
            user_age = user.age or 25
            if user_age < min_age or user_age > max_age:
                continue
            
            # Aplicar filtro de ubicación
            if location and user.location and user.location.lower() != location.lower():
                continue
            
            # Aplicar filtro de deportes
            user_sports = parse_sports(user.deportes_preferidos or "")
            if filtered_sports:
                # Verificar si el usuario tiene al menos uno de los deportes filtrados
                user_sport_names = [s.get("sport", "").lower() for s in user_sports]
                filtered_sport_names = [s.get("sport", "").lower() for s in filtered_sports]
                
                has_matching_sport = any(
                    user_sport in filtered_sport_names or user_sport in [fs.lower() for fs in filtered_sport_names]
                    for user_sport in user_sport_names
                )
                
                if not has_matching_sport:
                    continue
            
            # Calcular score de compatibilidad basado en deportes en común
            compatibility_score = 60  # Score base
            common_sports = []
            
            if filtered_sports and user_sports:
                for user_sport in user_sports:
                    for filtered_sport in filtered_sports:
                        if user_sport.get("sport", "").lower() == filtered_sport.get("sport", "").lower():
                            common_sports.append(user_sport.get("sport"))
                            compatibility_score += 10  # +10 por deporte en común
            
            # Asegurar que el score no exceda 95
            compatibility_score = min(compatibility_score, 95)
            
            compatible_user = {
                "id": user.id,
                "name": user.username,
                "age": user_age,
                "location": user.location or "Buenos Aires",
                "bio": user.descripcion or "Amante del deporte",
                "foto_url": user.foto_url or "",
                "video_url": user.video_url or "",
                "sports": user_sports,  # Array de objetos
                "compatibility_score": compatibility_score,
                "common_sports": common_sports
            }
            compatible_users.append(compatible_user)
        
        print(f"✅ Encontrados {len(compatible_users)} usuarios compatibles después de aplicar filtros")
        return {"users": compatible_users}
        
    except Exception as e:
        print(f"❌ Error obteniendo usuarios compatibles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para dar like a un usuario
@app.post("/users/like/{user_id}")
async def like_user(
    user_id: int,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"❤️ Usuario {current_user.id} dando like a usuario {user_id}")
        
        # Verificar que el usuario objetivo existe
        target_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar que no se está dando like a sí mismo
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="No puedes darte like a ti mismo")
        
        # Verificar si ya existe un like
        existing_like = db.query(models.Like).filter(
            models.Like.user_id == current_user.id,
            models.Like.liked_user_id == user_id
        ).first()
        
        if existing_like:
            return {
                "success": True,
                "is_match": False,
                "message": "Ya le diste like a este usuario"
            }
        
        # Crear el like
        new_like = models.Like(
            user_id=current_user.id,
            liked_user_id=user_id
        )
        db.add(new_like)
        
        # Verificar si hay match (like mutuo)
        mutual_like = db.query(models.Like).filter(
            models.Like.user_id == user_id,
            models.Like.liked_user_id == current_user.id
        ).first()
        
        is_match = False
        if mutual_like:
            # Crear el match
            new_match = models.Match(
                user1_id=min(current_user.id, user_id),
                user2_id=max(current_user.id, user_id)
            )
            db.add(new_match)
            is_match = True
            print(f"🎉 ¡MATCH! Entre usuario {current_user.id} y usuario {user_id}")
        
        db.commit()
        
        return {
            "success": True,
            "is_match": is_match,
            "message": "¡Es un match! 🎉" if is_match else "Like registrado"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error procesando like: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para dar dislike a un usuario
@app.post("/users/dislike/{user_id}")
async def dislike_user(
    user_id: int,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"❌ Usuario {current_user.id} dando dislike a usuario {user_id}")
        
        # Verificar que el usuario objetivo existe
        target_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar que no se está dando dislike a sí mismo
        if current_user.id == user_id:
            raise HTTPException(status_code=400, detail="No puedes rechazarte a ti mismo")
        
        # Eliminar like si existe
        existing_like = db.query(models.Like).filter(
            models.Like.user_id == current_user.id,
            models.Like.liked_user_id == user_id
        ).first()
        
        if existing_like:
            db.delete(existing_like)
        
        db.commit()
        
        print("✅ Dislike registrado")
        
        return {
            "success": True,
            "message": "Dislike registrado"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error procesando dislike: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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
        existing_user = db.query(models.User).filter(
            (models.User.email == user_data.email) | (models.User.username == user_data.username)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Usuario o email ya existe")
        # Usar passlib para hashear la contraseña
        hashed_password = pwd_context.hash(user_data.password)
        new_user = models.User(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,
            age=user_data.age,
            location=user_data.location,
            descripcion=user_data.bio or user_data.descripcion,
            deportes_preferidos=user_data.sports or user_data.deportes_preferidos,
            foto_url=user_data.foto_url,
            video_url=user_data.video_url
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        token = create_access_token(data={"sub": new_user.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "name": new_user.username,
                "age": new_user.age,
                "location": new_user.location,
                "bio": new_user.descripcion or "",
                "foto_url": new_user.foto_url,
                "video_url": new_user.video_url,
                "sports": new_user.deportes_preferidos or ""
            }
        }
    except Exception as e:
        print(f"Error en registro: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = db.query(models.User).filter(
            (models.User.email == form_data.username) | (models.User.username == form_data.username)
        ).first()
        if not user:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        # Usar passlib para verificar la contraseña
        if not pwd_context.verify(form_data.password, user.password):
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        token = create_access_token(data={"sub": user.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "age": user.age,
                "location": user.location,
                "descripcion": user.descripcion or "",
                "foto_url": user.foto_url,
                "video_url": user.video_url,
                "deportes_preferidos": user.deportes_preferidos or ""
            }
        }
    except Exception as e:
        print(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/test-register")
async def test_register():
    try:
        # Simular datos de registro
        test_data = {
            "username": "testuser3",
            "email": "test3@test.com",
            "password": "test123",
            "name": "Test User 3",
            "age": 25,
            "location": "Palermo",
            "bio": "Test bio",
            "sports": "Fútbol,Tenis"
        }
        
        # Verificar si el usuario ya existe
        existing_user = db.query(models.User).filter(
            (models.User.email == test_data["email"]) | (models.User.username == test_data["username"])
        ).first()
        
        if existing_user:
            return {"error": "Usuario ya existe"}
        
        # Crear nuevo usuario
        hashed_password = pwd_context.hash(test_data["password"])
        
        new_user = models.User(
            username=test_data["username"],
            email=test_data["email"],
            password=hashed_password,
            name=test_data["name"],
            age=test_data["age"],
            location=test_data["location"],
            bio=test_data["bio"],
            descripcion=test_data["bio"],
            sports=test_data["sports"],
            deportes_preferidos=test_data["sports"],
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "user_id": new_user.id,
            "message": "Usuario creado exitosamente"
        }
    except Exception as e:
        print(f"Error en test-register: {e}")
        db.rollback()
        return {"error": str(e)}

# Endpoint para crear usuarios de prueba
@app.post("/test/create-test-users")
async def create_test_users(db: Session = Depends(get_db)):
    try:
        print("🧪 Creando usuarios de prueba...")
        
        # Lista de usuarios de prueba
        test_users = [
            {
                "username": "maria_garcia",
                "email": "maria@test.com",
                "password": "test123",
                "age": 24,
                "location": "Palermo",
                "descripcion": "Amante del running y el yoga. Busco compañeras para entrenar juntas.",
                "deportes_preferidos": "Running (Intermedio), Yoga (Avanzado), Pilates (Principiante)",
                "foto_url": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400",
                "video_url": ""
            },
            {
                "username": "carlos_rodriguez",
                "email": "carlos@test.com", 
                "password": "test123",
                "age": 28,
                "location": "Belgrano",
                "descripcion": "Jugador de fútbol amateur. Busco equipo para jugar los fines de semana.",
                "deportes_preferidos": "Fútbol (Avanzado), Tenis (Intermedio), Natación (Principiante)",
                "foto_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
                "video_url": ""
            },
            {
                "username": "ana_lopez",
                "email": "ana@test.com",
                "password": "test123", 
                "age": 26,
                "location": "Recoleta",
                "descripcion": "Instructora de pilates y amante del ciclismo urbano.",
                "deportes_preferidos": "Pilates (Avanzado), Ciclismo (Intermedio), Yoga (Intermedio)",
                "foto_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400",
                "video_url": ""
            },
            {
                "username": "juan_martinez",
                "email": "juan@test.com",
                "password": "test123",
                "age": 30,
                "location": "Villa Crespo", 
                "descripcion": "Entrenador personal especializado en funcional. Busco clientes y compañeros.",
                "deportes_preferidos": "Funcional (Avanzado), Crossfit (Intermedio), Gimnasio (Avanzado)",
                "foto_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
                "video_url": ""
            },
            {
                "username": "laura_fernandez",
                "email": "laura@test.com",
                "password": "test123",
                "age": 22,
                "location": "Caballito",
                "descripcion": "Estudiante de deportes. Me gusta el básquet y el vóley.",
                "deportes_preferidos": "Básquet (Intermedio), Vóley (Principiante), Running (Intermedio)",
                "foto_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400",
                "video_url": ""
            }
        ]
        
        created_users = []
        for user_data in test_users:
            # Verificar si el usuario ya existe
            existing_user = db.query(models.User).filter(
                models.User.email == user_data["email"]
            ).first()
            
            if existing_user:
                print(f"⚠️ Usuario {user_data['username']} ya existe")
                continue
            
            # Crear hash de la contraseña
            hashed_password = pwd_context.hash(user_data["password"])
            
            # Crear el usuario
            new_user = models.User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=hashed_password,
                age=user_data["age"],
                location=user_data["location"],
                descripcion=user_data["descripcion"],
                deportes_preferidos=user_data["deportes_preferidos"],
                foto_url=user_data["foto_url"],
                video_url=user_data["video_url"]
            )
            
            db.add(new_user)
            created_users.append(user_data["username"])
        
        db.commit()
        
        print(f"✅ Usuarios de prueba creados: {created_users}")
        
        return {
            "success": True,
            "message": f"Usuarios de prueba creados: {', '.join(created_users)}",
            "created_users": created_users,
            "test_accounts": [
                {"email": "maria@test.com", "password": "test123"},
                {"email": "carlos@test.com", "password": "test123"},
                {"email": "ana@test.com", "password": "test123"},
                {"email": "juan@test.com", "password": "test123"},
                {"email": "laura@test.com", "password": "test123"}
            ]
        }
        
    except Exception as e:
        print(f"❌ Error creando usuarios de prueba: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para crear tablas específicas
@app.post("/create-likes-matches-tables")
async def create_likes_matches_tables(db: Session = Depends(get_db)):
    try:
        print("🔧 Creando tablas likes y matches específicamente...")
        
        # Crear tabla likes
        create_likes_table = """
        CREATE TABLE IF NOT EXISTS likes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            liked_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (liked_user_id) REFERENCES users(id)
        );
        """
        
        # Crear tabla matches
        create_matches_table = """
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users(id),
            FOREIGN KEY (user2_id) REFERENCES users(id)
        );
        """
        
        # Ejecutar las consultas SQL
        from sqlalchemy import text
        
        db.execute(text(create_likes_table))
        db.execute(text(create_matches_table))
        db.commit()
        
        print("✅ Tablas likes y matches creadas exitosamente")
        return {"message": "Tablas likes y matches creadas exitosamente"}
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        db.rollback()
        return {"error": str(e)}

# Endpoint para obtener estadísticas de la base de datos
@app.get("/db-stats")
async def get_db_stats(db: Session = Depends(get_db)):
    try:
        from app.models import User, Like, Match
        
        user_count = db.query(User).count()
        like_count = db.query(Like).count()
        match_count = db.query(Match).count()
        
        return {
            "users": user_count,
            "likes": like_count,
            "matches": match_count
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return {
            "users": 0,
            "likes": 0,
            "matches": 0,
            "error": str(e)
        }

# Forzar reinicio de Railway - 2025-07-01

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
