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
    # Usar deportes_preferidos (campo existente) o sports (nuevo campo)
    sports1_str = user1.sports if user1.sports else user1.deportes_preferidos
    sports2_str = user2.sports if user2.sports else user2.deportes_preferidos
    
    sports1 = []
    sports2 = []
    
    if sports1_str:
        try:
            sports1 = json.loads(sports1_str) if sports1_str.startswith('[') else sports1_str.split(',')
        except:
            sports1 = sports1_str.split(',') if sports1_str else []
    
    if sports2_str:
        try:
            sports2 = json.loads(sports2_str) if sports2_str.startswith('[') else sports2_str.split(',')
        except:
            sports2 = sports2_str.split(',') if sports2_str else []
    
    if sports1 and sports2:
        # Extraer nombres de deportes
        sports1_names = [sport.get('sport', sport) if isinstance(sport, dict) else sport.strip() for sport in sports1]
        sports2_names = [sport.get('sport', sport) if isinstance(sport, dict) else sport.strip() for sport in sports2]
        
        common_sports = set(sports1_names) & set(sports2_names)
        if common_sports:
            score += 40 * (len(common_sports) / max(len(sports1_names), len(sports2_names)))
    
    # 2. Ubicación (30 puntos)
    if user1.location and user2.location:
        if user1.location.lower() == user2.location.lower():
            score += 30
        elif any(barrio in user1.location.lower() for barrio in ['palermo', 'belgrano', 'recoleta']) and \
             any(barrio in user2.location.lower() for barrio in ['palermo', 'belgrano', 'recoleta']):
            score += 20  # Zonas cercanas
    
    # 3. Rango de edad (20 puntos)
    if user1.age and user2.age:
        age_diff = abs(user1.age - user2.age)
        if age_diff <= 5:
            score += 20
        elif age_diff <= 10:
            score += 15
        elif age_diff <= 15:
            score += 10
    
    # 4. Nivel deportivo similar (10 puntos)
    if sports1 and sports2:
        levels1 = [sport.get('level', 'Principiante') if isinstance(sport, dict) else 'Principiante' for sport in sports1]
        levels2 = [sport.get('level', 'Principiante') if isinstance(sport, dict) else 'Principiante' for sport in sports2]
        
        common_levels = set(levels1) & set(levels2)
        if common_levels:
            score += 10
    
    return min(score, 100.0)

def get_common_sports(user1: models.User, user2: models.User) -> List[str]:
    """
    Obtiene los deportes en común entre dos usuarios
    """
    # Usar deportes_preferidos (campo existente) o sports (nuevo campo)
    sports1_str = user1.sports if user1.sports else user1.deportes_preferidos
    sports2_str = user2.sports if user2.sports else user2.deportes_preferidos
    
    sports1 = []
    sports2 = []
    
    if sports1_str:
        try:
            sports1 = json.loads(sports1_str) if sports1_str.startswith('[') else sports1_str.split(',')
        except:
            sports1 = sports1_str.split(',') if sports1_str else []
    
    if sports2_str:
        try:
            sports2 = json.loads(sports2_str) if sports2_str.startswith('[') else sports2_str.split(',')
        except:
            sports2 = sports2_str.split(',') if sports2_str else []
    
    if not sports1 or not sports2:
        return []
    
    sports1_names = [sport.get('sport', sport) if isinstance(sport, dict) else sport.strip() for sport in sports1]
    sports2_names = [sport.get('sport', sport) if isinstance(sport, dict) else sport.strip() for sport in sports2]
    
    return list(set(sports1_names) & set(sports2_names))

def get_compatible_users(db: Session, current_user: models.User, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Obtiene usuarios compatibles para el usuario actual
    """
    try:
        # Verificar si las tablas de likes existen
        try:
            liked_users = db.query(models.Like.liked_id).filter(models.Like.liker_id == current_user.id).subquery()
            users_who_liked_me = db.query(models.Like.liker_id).filter(
                models.Like.liked_id == current_user.id
            ).subquery()
            
            # Query principal con filtros de likes
            compatible_users = db.query(models.User).filter(
                models.User.id != current_user.id,
                models.User.id.notin_(liked_users),
            ).all()
        except:
            # Si las tablas no existen, mostrar todos los usuarios
            compatible_users = db.query(models.User).filter(
                models.User.id != current_user.id,
            ).all()
        
        # Calcular scores y ordenar
        users_with_scores = []
        for user in compatible_users:
            score = calculate_compatibility_score(current_user, user)
            common_sports = get_common_sports(current_user, user)
            
            # Bonus para usuarios que ya le dieron like (si las tablas existen)
            try:
                if user.id in [row[0] for row in db.query(users_who_liked_me).all()]:
                    score += 20
            except:
                pass
            
            users_with_scores.append({
                "user": user,
                "compatibility_score": score,
                "common_sports": common_sports
            })
        
        # Ordenar por score descendente
        users_with_scores.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        # Limitar resultados
        return users_with_scores[:limit]
        
    except Exception as e:
        print(f"Error en get_compatible_users: {e}")
        return []

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