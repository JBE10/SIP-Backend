from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Mantener para compatibilidad
    
    # Campos existentes en producción
    deportes_preferidos = Column(String(255))  # Mantener para compatibilidad
    descripcion = Column(Text)  # Mantener para compatibilidad
    foto_url = Column(String(255))
    video_url = Column(String(255))
    age = Column(Integer)
    location = Column(String(100))
    
    # Nuevos campos (opcionales para compatibilidad)
    hashed_password = Column(String, nullable=True)  # Nuevo campo
    name = Column(String, nullable=True)  # Nuevo campo
    bio = Column(Text, nullable=True)  # Nuevo campo (alias de descripcion)
    sports = Column(String, nullable=True)  # Nuevo campo (alias de deportes_preferidos)
    is_active = Column(Boolean, default=True, nullable=True)  # Nuevo campo
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)  # Nuevo campo
    
    # Relaciones (solo si las tablas existen)
    likes_given = relationship("Like", foreign_keys="Like.liker_id", back_populates="liker", cascade="all, delete-orphan")
    likes_received = relationship("Like", foreign_keys="Like.liked_id", back_populates="liked", cascade="all, delete-orphan")
    matches = relationship("Match", foreign_keys="Match.user1_id", back_populates="user1", cascade="all, delete-orphan")
    matches_received = relationship("Match", foreign_keys="Match.user2_id", back_populates="user2", cascade="all, delete-orphan")

class Like(Base):
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    liker_id = Column(Integer, ForeignKey("users.id"))
    liked_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    liker = relationship("User", foreign_keys=[liker_id], back_populates="likes_given")
    liked = relationship("User", foreign_keys=[liked_id], back_populates="likes_received")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"))
    user2_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_received")
