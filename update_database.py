from app.db import engine
from app.models import SQLModel, PendingQuestion

def update_database():
    print("Mise à jour de la base de données...")
    SQLModel.metadata.create_all(engine)
    print("Base de données mise à jour avec succès!")

if __name__ == "__main__":
    update_database()
