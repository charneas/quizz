from sqlmodel import Session, select
from app.models import Game
from app.db import engine

# Vérifie la structure de la table Game
print("Structure de la table Game :")
with Session(engine) as session:
    # Récupère la première ligne de la table (même si elle est vide)
    statement = select(Game)
    game = session.exec(statement).first()
    
    # Affiche tous les champs disponibles
    if game is None:
        # Crée un jeu temporaire pour voir sa structure
        game = Game(
            name="Test",
            mode="ffa",
            code="TEST123",
            state="waiting",
            created_by=1
        )
    
    print("\nChamps disponibles :")
    for field in game.__fields__.keys():
        print(f"- {field}")
        
print("\nFin de la vérification")
