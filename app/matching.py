import json
from sqlalchemy.orm import Session
from . import models
from typing import List, Dict, Any
import math
from datetime import datetime

def calculate_compatibility_score(user1: models.User, user2: models.User) -> float:
    """
    Calcula un score de compatibilidad entre dos usuarios (0-100)
    """
    score = 0.0
    
    # 1. Deportes en común (40 puntos)
    sports1_str = user1.deportes_preferidos
    sports2_str = user2.deportes_preferidos
    sports1 = sports1_str.split(',') if sports1_str else []
    sports2 = sports2_str.split(',') if sports2_str else []
    
    if sports1 and sports2:
        common_sports = set([s.strip() for s in sports1]) & set([s.strip() for s in sports2])
        if common_sports:
            score += 40 * (len(common_sports) / max(len(sports1), len(sports2)))
    
    # 2. Ubicación (30 puntos)
    if user1.location and user2.location:
        if user1.location.lower() == user2.location.lower():
            score += 30
    
    # 3. Rango de edad (20 puntos)
    if user1.age and user2.age:
        age_diff = abs(user1.age - user2.age)
        if age_diff <= 5:
            score += 20
        elif age_diff <= 10:
            score += 15
        elif age_diff <= 15:
            score += 10
    
    return min(score, 100.0)

def get_common_sports(user1: models.User, user2: models.User) -> List[str]:
    """
    Obtiene los deportes en común entre dos usuarios
    """
    sports1_str = user1.deportes_preferidos
    sports2_str = user2.deportes_preferidos
    sports1 = sports1_str.split(',') if sports1_str else []
    sports2 = sports2_str.split(',') if sports2_str else []
    
    if not sports1 or not sports2:
        return []
    
    return list(set([s.strip() for s in sports1]) & set([s.strip() for s in sports2]))

def get_compatible_users(db: Session, current_user: models.User, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Obtiene usuarios compatibles para el usuario actual
    """
    compatible_users = db.query(models.User).filter(models.User.id != current_user.id).all()
    users_with_scores = []
    for user in compatible_users:
        score = calculate_compatibility_score(current_user, user)
        common_sports = get_common_sports(current_user, user)
        users_with_scores.append({
            "user": user,
            "compatibility_score": score,
            "common_sports": common_sports
        })
    users_with_scores.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return users_with_scores[:limit]

def create_like(db: Session, liker_id: int, liked_id: int) -> models.Like:
    """
    Crea un like y verifica si hay match
    """
    try:
        # Crear el like
        like = models.Like(liker_id=liker_id, liked_id=liked_id)
        db.add(like)
        db.commit()
        db.refresh(like)
        
        # Verificar si hay match (si el otro usuario también le dio like)
        existing_like = db.query(models.Like).filter(
            models.Like.liker_id == liked_id,
            models.Like.liked_id == liker_id
        ).first()
        
        if existing_like:
            # ¡Hay match! Crear el match
            match = models.Match(
                user1_id=min(liker_id, liked_id),
                user2_id=max(liker_id, liked_id)
            )
            db.add(match)
            db.commit()
            db.refresh(match)
        
        return like
    except Exception as e:
        print(f"Error en create_like: {e}")
        # Si las tablas no existen, devolver un like simulado
        return models.Like(id=1, liker_id=liker_id, liked_id=liked_id, created_at=datetime.utcnow())

def get_user_matches(db: Session, user_id: int) -> List[models.Match]:
    """
    Obtiene todos los matches de un usuario
    """
    try:
        matches = db.query(models.Match).filter(
            (models.Match.user1_id == user_id) | (models.Match.user2_id == user_id)
        ).all()
        
        return matches
    except Exception as e:
        print(f"Error en get_user_matches: {e}")
        return [] 