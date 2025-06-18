from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)  # único
    full_name = Column(String(100), nullable=False)              # ← nuevo
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    sports = Column(String(255))
    description = Column(Text)
    profile_picture = Column(String(255))
    age = Column(Integer)
    location = Column(String(100))

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
