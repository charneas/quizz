from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Body
from typing import List, Optional
from ..models import Game, Admin, GameCreateRequest
from ..auth import get_admin as get_current_admin
from ..db import get_session
from sqlmodel import Session, select
from ..logger import logger, log_error
import random
import string
from datetime import datetime

router = APIRouter()

def generate_game_code(length: int = 6) -> str:
    """Génère un code unique pour une partie."""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=length))
    return code

@router.post("/games")
def create_game(
    game_data: GameCreateRequest,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Crée une nouvelle partie."""
    try:
        logger.info("=== Début création partie ===")
        logger.debug(f"Données reçues: mode={game_data.mode}")
        logger.debug(f"Admin: {current_admin.dict()}")
        
        # Validation des modes
        valid_modes = ["ffa", "team", "grid"]
        if game_data.mode not in valid_modes:
            logger.warning(f"Mode invalide reçu: {game_data.mode}")
            raise HTTPException(
                status_code=400,
                detail=f"Mode invalide. Modes autorisés: {', '.join(valid_modes)}"
            )
        
        # Génération du code
        code = generate_game_code()
        logger.debug(f"Code généré: {code}")
        
        # Création de l'objet Game
        game = Game(
            mode=game_data.mode,
            code=code,
            state="waiting",
            created_by=current_admin.id
        )
        
        logger.debug(f"État de l'objet Game avant commit: {game.dict()}")
        
        try:
            logger.debug("Tentative de commit")
            session.add(game)
            session.commit()
            logger.debug("Commit réussi")
            
            session.refresh(game)
            logger.debug("Refresh réussi")
            
            result = {
                "id": game.id,
                "mode": game.mode,
                "code": game.code,
                "state": game.state
            }
            logger.info(f"Partie créée avec succès: {result}")
            return result
            
        except Exception as db_error:
            session.rollback()
            log_error(db_error, "Erreur lors du commit de la nouvelle partie")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur base de données: {str(db_error)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "Erreur inattendue lors de la création de partie")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/games/active")
def list_active_games(
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Liste les parties actives."""
    statement = select(Game).where(Game.state.in_(["waiting", "running", "paused"]))
    games = session.exec(statement).all()
    
    return [
        {
            "id": game.id,
            "mode": game.mode,
            "code": game.code,
            "state": game.state
        }
        for game in games
    ]

@router.get("/games/{game_id}")
def get_game(
    game_id: int,
    session: Session = Depends(get_session)
):
    """Récupère les infos d'une partie (public, pas d'authentification requise)."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    return {
        "id": game.id,
        "mode": game.mode,
        "code": game.code,
        "state": game.state,
        "current_question_id": game.current_question_id,
        "current_answer": game.current_answer
    }

@router.get("/games/{game_id}/players")
def list_game_players(
    game_id: int,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Liste les joueurs d'une partie."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    return [
        {
            "id": player.id,
            "name": player.name
        }
        for player in game.players
    ]

@router.post("/games/{game_id}/command")
def send_game_command(
    game_id: int,
    command_data: dict = Body(...),
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Envoie une commande à une partie (start, pause, stop, etc.)."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    command = command_data.get("command", "")
    message = "Commande exécutée"  # Initialiser par défaut
    
    if command == "start":
        if game.state == "waiting":
            game.state = "running"
            message = "Partie démarrée"
        else:
            message = "Partie ne peut pas être démarrée (état: {})".format(game.state)
    elif command == "pause":
        if game.state == "running":
            game.state = "paused"
            message = "Partie mise en pause"
        else:
            message = "Partie ne peut pas être mise en pause (état: {})".format(game.state)
    elif command == "stop":
        if game.state in ["running", "paused"]:
            game.state = "finished"
            game.ended_at = datetime.utcnow()
            message = "Partie terminée"
        else:
            message = "Partie ne peut pas être arrêtée (état: {})".format(game.state)
    elif command == "next_question":
        if game.state == "running":
            # Logique pour passer à la question suivante
            from ..models import Question
            import random
            
            # Obtenir une question aléatoire
            questions = session.exec(select(Question)).all()
            if questions:
                question = random.choice(questions)
                game.current_question_id = question.id
                message = f"Question: {question.text}"
            else:
                message = "Aucune question disponible"
        else:
            message = "Impossible de passer à la question suivante"
    elif command == "show_answer":
        if game.state == "running":
            # Get the current question and store its answer
            if game.current_question_id:
                from ..models import Question
                question = session.get(Question, game.current_question_id)
                if question:
                    game.current_answer = question.answer
                    message = f"Réponse: {question.answer}"
                else:
                    message = "Question non trouvée"
            else:
                message = "Aucune question en cours"
        else:
            message = "Impossible de montrer la réponse"
    else:
        raise HTTPException(status_code=400, detail="Commande invalide")
    
    session.add(game)
    session.commit()
    return {"message": message}

@router.delete("/games/{game_id}")
def delete_game(
    game_id: int,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Supprime une partie."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    session.delete(game)
    session.commit()
    return {"message": "Partie supprimée"}

@router.delete("/games/{game_id}/players/{player_id}")
def kick_player(
    game_id: int,
    player_id: int,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Exclut un joueur d'une partie."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    player = next((p for p in game.players if p.id == player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Joueur non trouvé")
    
    game.players.remove(player)
    session.add(game)
    session.commit()
    return {"message": "Joueur exclu de la partie"}

@router.get("/games/{game_id}/question/random")
def get_random_question(
    game_id: int,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Retourne une question aléatoire pour le jeu."""
    from ..models import Question
    import random
    
    # Obtenir le jeu
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    # Obtenir toutes les questions
    questions = session.exec(select(Question)).all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="Aucune question disponible")
    
    # Choisir une question aléatoire
    question = random.choice(questions)
    
    return {
        "id": question.id,
        "text": question.text,
        "answer": question.answer,
        "theme": question.theme,
        "difficulty": question.difficulty,
        "points": question.points
    }

@router.get("/games/{game_id}/question/current")
def get_current_question(
    game_id: int,
    session: Session = Depends(get_session)
):
    """Retourne la question actuellement affichée pour le jeu."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    if not game.current_question_id:
        raise HTTPException(status_code=404, detail="Aucune question en cours")
    
    from ..models import Question
    question = session.get(Question, game.current_question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question non trouvée")
    
    return {
        "id": question.id,
        "text": question.text,
        "answer": question.answer,
        "theme": question.theme,
        "difficulty": question.difficulty,
        "points": question.points
    }

@router.post("/games/{game_id}/players")
def add_player(
    game_id: int,
    player_data: dict = Body(...),
    session: Session = Depends(get_session),
):
    """Ajoute un joueur à une partie."""
    from ..models import Player
    
    # Récupérer la partie
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    # Créer le joueur
    player_name = player_data.get("name", "")
    if not player_name:
        raise HTTPException(status_code=400, detail="Le nom du joueur est requis")
    
    player = Player(
        name=player_name,
        score=0,
        game_id=game_id
    )
    
    try:
        session.add(player)
        session.commit()
        session.refresh(player)
        
        return {
            "id": player.id,
            "name": player.name,
            "score": player.score
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du joueur: {str(e)}")
