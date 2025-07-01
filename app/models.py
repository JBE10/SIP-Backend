from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    deportes_preferidos = Column(String(255))
    descripcion = Column(Text)
    foto_url = Column(String(255))
    video_url = Column(String(255))
    age = Column(Integer)
    location = Column(String(100))

# Las tablas Like y Match pueden quedarse si existen en Railway, si no, comentarlas o eliminarlas temporalmente.
