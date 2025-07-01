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
        "current_base_url": os.getenv("BASE_URL", "http://localhost:8000")
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
                base_url = os.getenv("BASE_URL", "http://localhost:8000")
                
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
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
            
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
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
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
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
