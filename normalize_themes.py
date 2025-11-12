from app.db import engine
from app.models import Question
from sqlmodel import Session, select

def normalize_themes():
    # Définir les corrections de noms
    theme_corrections = {
        'Jeux vidéos': 'Jeux Vidéos',
        'Mario kart': 'Mario Kart',
        'Musique ': 'Musique'  # Supprime l'espace à la fin
    }
    
    try:
        with Session(engine) as session:
            # Récupérer toutes les questions
            statement = select(Question)
            questions = session.exec(statement).all()
            
            # Compter le nombre de modifications
            changes = 0
            
            # Mettre à jour les thèmes
            for question in questions:
                if question.theme in theme_corrections:
                    old_theme = question.theme
                    question.theme = theme_corrections[old_theme]
                    changes += 1
            
            # Sauvegarder les modifications
            session.commit()
            
            print(f"Normalisation terminée ! {changes} thèmes ont été mis à jour.")
            
            # Afficher les thèmes uniques après la normalisation
            statement = select(Question.theme).distinct()
            themes = session.exec(statement).all()
            print("\nListe des thèmes après normalisation :")
            for theme in sorted(themes):
                statement = select(Question).where(Question.theme == theme)
                count = len(session.exec(statement).all())
                print(f"- {theme}: {count} questions")
                
    except Exception as e:
        print(f"Erreur lors de la normalisation : {e}")

if __name__ == "__main__":
    normalize_themes()
