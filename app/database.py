from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Obtener DATABASE_URL de las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar que DATABASE_URL esté definida
if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en las variables de entorno")

print(f"🔗 Conectando a la base de datos: {DATABASE_URL[:30]}...")

try:
    engine = create_engine(DATABASE_URL)
    # Probar la conexión
    with engine.connect() as conn:
        print("✅ Conexión a la base de datos exitosa")
except Exception as e:
    print(f"❌ Error conectando a la base de datos: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Obtener una sesión de base de datos (usado con Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
