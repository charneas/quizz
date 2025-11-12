from app.db import engine
from app.models import Question
from sqlmodel import Session, select

def check_import():
    with Session(engine) as session:
        # Compter le nombre total de questions
        statement = select(Question)
        questions = session.exec(statement).all()
        print(f"\nNombre total de questions : {len(questions)}")
        
        # Compter les questions par thème
        themes = {}
        for q in questions:
            themes[q.theme] = themes.get(q.theme, 0) + 1
        
        print("\nQuestions par thème :")
        for theme, count in themes.items():
            print(f"- {theme}: {count}")
        
        # Afficher quelques exemples de questions
        print("\nExemples de questions :")
        for i, q in enumerate(questions[:3], 1):
            print(f"\n{i}. Thème: {q.theme}")
            print(f"   Question: {q.text}")
            print(f"   Réponse: {q.answer}")
            print(f"   Difficulté: {q.difficulty}")

if __name__ == "__main__":
    check_import()
