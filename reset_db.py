import os
import sqlite3
from sqlmodel import SQLModel, Session
from app.db import engine
from app.models import Admin, Game, Player, Team, Question, PendingQuestion, Bonus
from app.auth import get_password_hash

def reset_database():
    """Réinitialise complètement la base de données"""
    db_path = "quiz.db"
    
    # 1. Ferme toutes les connexions à la base de données
    print("Fermeture des connexions...")
    try:
        engine.dispose()
    except:
        pass
    
    # 2. Supprime physiquement le fichier de la base de données
    print("Suppression de la base de données existante...")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("Base de données supprimée")
        except Exception as e:
            print(f"Erreur lors de la suppression: {e}")
            return False
    
    # 3. Crée une nouvelle base de données vide
    print("Création d'une nouvelle base de données...")
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
        print("Nouvelle base de données créée")
    except Exception as e:
        print(f"Erreur lors de la création: {e}")
        return False
    
    # 4. Crée toutes les tables
    print("Création des tables...")
    try:
        SQLModel.metadata.create_all(engine)
        print("Tables créées avec succès")
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")
        return False
    
    # 5. Crée l'admin par défaut
    print("Création de l'admin par défaut...")
    try:
        with Session(engine) as session:
            admin = Admin(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                email="admin@example.com",
                is_superadmin=True
            )
            session.add(admin)
            session.commit()
            print("Admin créé avec succès")
    except Exception as e:
        print(f"Erreur lors de la création de l'admin: {e}")
        return False
    
    print("Réinitialisation terminée avec succès!")
    return True

if __name__ == "__main__":
    if reset_database():
        print("\nLa base de données a été réinitialisée avec succès!")
        print("Vous pouvez maintenant vous connecter avec:")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("\nErreur lors de la réinitialisation de la base de données")
