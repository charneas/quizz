from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlmodel import Session, select
from typing import List
from app.db import get_session
from app.models import Admin
from app.auth import get_admin, get_password_hash
from pydantic import BaseModel, EmailStr

def add_security_headers(response: Response):
    """Ajoute les en-têtes de sécurité pour forcer l'authentification"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

router = APIRouter(prefix="/admins", tags=["admins"])

class AdminCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class AdminResponse(BaseModel):
    id: int
    username: str
    email: str
    is_superadmin: bool

@router.get("", response_model=List[AdminResponse])
async def list_admins(
    current_admin: Admin = Depends(get_admin),
    session: Session = Depends(get_session),
    response: Response = None
):
    """Liste tous les administrateurs (superadmin uniquement)"""
    add_security_headers(response)
    if not current_admin.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les superadmins peuvent lister les administrateurs"
        )
    
    statement = select(Admin)
    admins = session.exec(statement).all()
    return admins

@router.post("", response_model=AdminResponse)
async def create_admin(
    new_admin: AdminCreate,
    current_admin: Admin = Depends(get_admin),
    session: Session = Depends(get_session),
    response: Response = None
):
    """Crée un nouvel administrateur (superadmin uniquement)"""
    add_security_headers(response)
    if not current_admin.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les superadmins peuvent créer des administrateurs"
        )
    
    # Vérifier si le nom d'utilisateur existe déjà
    exists = session.exec(
        select(Admin).where(Admin.username == new_admin.username)
    ).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà utilisé"
        )
    
    # Créer le nouvel admin
    admin = Admin(
        username=new_admin.username,
        hashed_password=get_password_hash(new_admin.password),
        email=new_admin.email,
        is_superadmin=False  # Seul le premier admin est superadmin
    )
    
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin

@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    current_admin: Admin = Depends(get_admin),
    session: Session = Depends(get_session),
    response: Response = None
):
    """Supprime un administrateur (superadmin uniquement)"""
    add_security_headers(response)
    if not current_admin.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les superadmins peuvent supprimer des administrateurs"
        )
    
    # Empêcher l'auto-suppression
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )
    
    admin = session.get(Admin, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrateur non trouvé"
        )
    
    session.delete(admin)
    session.commit()
    return {"message": "Administrateur supprimé avec succès"}
