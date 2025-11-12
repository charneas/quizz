from app.db import engine, init_db
from app.models import Admin
from sqlmodel import Session
from app.auth import get_password_hash

def create_admin():
    # Initialiser la base de données
    init_db()
    
    # Créer un admin
    with Session(engine) as session:
        # Vérifier si l'admin existe déjà
        admin = Admin(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            email="admin@example.com",
            is_superadmin=True
        )
        session.add(admin)
        try:
            session.commit()
            print("Admin créé avec succès!")
            print("Username: admin")
            print("Password: admin123")
        except Exception as e:
            print(f"Erreur lors de la création de l'admin : {e}")

if __name__ == "__main__":
    create_admin()
