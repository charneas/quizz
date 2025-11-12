import pandas as pd
from app.db import engine
from app.models import Question, SQLModel
from sqlmodel import Session
import sys

def import_questions(excel_path):
    try:
        # Lire le fichier Excel
        df = pd.read_excel(excel_path)
        
        # Créer une session de base de données
        with Session(engine) as session:
            # Pour chaque ligne dans le fichier Excel
            for _, row in df.iterrows():
                # Créer une nouvelle question
                # Convertir la difficulté en nombre
                difficulty_map = {
                    'Facile': 1,
                    'Moyen': 2,
                    'Difficile': 3
                }
                difficulty = difficulty_map.get(str(row['Difficulté']).strip(), 2)  # 2 (moyen) par défaut
                
                question = Question(
                    text=str(row['Question']),
                    answer=str(row['Réponse']),
                    theme=str(row['Thème']),
                    difficulty=difficulty,
                    points=int(row['Points']) if 'Points' in row else 10
                )
                session.add(question)
            
            # Sauvegarder toutes les questions
            session.commit()
            print("Import terminé avec succès!")
            
    except Exception as e:
        print(f"Erreur lors de l'import: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import_questions("Questions Themes.xlsx")
