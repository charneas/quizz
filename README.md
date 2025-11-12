# Quiz App

Application de quiz en temps réel avec trois modes de jeu différents.

## Modes de jeu

1. **Mode Équipes**
   - Équipes de 3 joueurs tirés au sort
   - Réponses simultanées
   - Système de bonus/malus entre équipes

2. **Mode FFA (Free-For-All)**
   - Thème spécifique
   - Tour par tour
   - Deux tours par joueur

3. **Mode Grille Personnalisée**
   - 4 joueurs
   - Chaque joueur a une grille avec 5 cases de sa couleur
   - Questions personnalisées dans les cases colorées
   - Questions difficiles dans les autres cases

## Installation

1. Créer un environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancer le serveur :
```bash
uvicorn app.main:app --reload
```

## Structure du projet

```
quiz/
├── app/
│   ├── __init__.py
│   ├── main.py          # Application FastAPI
│   ├── db.py            # Configuration base de données
│   ├── models.py        # Modèles SQLModel
│   ├── game_modes.py    # Logique des modes de jeu
│   ├── websocket.py     # Gestion des WebSockets
│   └── utils.py         # Fonctions utilitaires
├── tests/
│   └── __init__.py
├── requirements.txt
└── README.md
```
