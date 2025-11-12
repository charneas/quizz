from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, select
import bcrypt
from typing import Optional
from app.models import Admin
from app.db import get_session

# Configuration de la sécurité HTTP Basic
security = HTTPBasic()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def get_admin(
    credentials: HTTPBasicCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[Admin]:
    """Vérifie les identifiants admin et retourne l'admin si valide"""
    admin = session.exec(
        select(Admin).where(Admin.username == credentials.username)
    ).first()
    
    if not admin or not verify_password(credentials.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Basic"},
        )
    return admin

# Fonction utilitaire pour créer un admin si aucun n'existe
def ensure_admin_exists(session: Session, username: str, password: str, email: str = "admin@example.com"):
    """Crée un admin par défaut si aucun n'existe"""
    admin_exists = session.exec(select(Admin)).first()
    if not admin_exists:
        try:
            admin = Admin(
                username=username,
                hashed_password=get_password_hash(password),
                email=email,
                is_superadmin=True  # Le premier admin est superadmin
            )
            session.add(admin)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de la création de l'admin: {e}")
