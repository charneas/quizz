from sqlmodel import SQLModel, create_engine
from app.models import Game, Admin, Player, Team, Question, PendingQuestion

# Création du moteur de base de données
engine = create_engine("sqlite:///quiz.db", echo=True)

# Création des tables
print("Création/mise à jour des tables...")
SQLModel.metadata.create_all(engine)
