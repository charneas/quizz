from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Optional
from ..models import Game, Admin
from ..auth import get_admin as get_current_admin
from ..db import get_session
from sqlmodel import Session
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
    game_data: dict,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Crée une nouvelle partie."""
    try:
        logger.info("=== Début création partie ===")
        logger.debug(f"Données reçues: {game_data}")
        logger.debug(f"Admin: {current_admin.dict()}")
        
        # Vérifie que les champs requis sont présents
        if "mode" not in game_data:
            logger.warning("Champs manquants dans game_data")
            raise HTTPException(
                status_code=400, 
                detail="Les champs 'name' et 'mode' sont requis"
            )
        
        # Validation des modes
        valid_modes = ["ffa", "team", "grid"]
        if game_data["mode"] not in valid_modes:
            logger.warning(f"Mode invalide reçu: {game_data['mode']}")
            raise HTTPException(
                status_code=400,
                detail=f"Mode invalide. Modes autorisés: {', '.join(valid_modes)}"
            )
        
        # Génération du code
        code = generate_game_code()
        logger.debug(f"Code généré: {code}")
        
        # Création de l'objet Game
        game = Game(
            name="name",
            mode=game_data["mode"],
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
                "name": game.name,
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
    
    return {
        "id": game.id,
        "name": game.name,
        "mode": game.mode,
        "code": game.code,
        "state": game.state
    }

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
            "name": game.name,
            "mode": game.mode,
            "code": game.code,
            "state": game.state
        }
        for game in games
    ]

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
    command_data: dict,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin)
):
    """Envoie une commande à une partie (start, pause, stop, etc.)."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie non trouvée")
    
    command = command_data["command"]
    
    if command == "start":
        if game.state == "waiting":
            game.state = "running"
            message = "Partie démarrée"
    elif command == "pause":
        if game.state == "running":
            game.state = "paused"
            message = "Partie mise en pause"
    elif command == "stop":
        if game.state in ["running", "paused"]:
            game.state = "finished"
            game.ended_at = datetime.utcnow()
            message = "Partie terminée"
    elif command == "next_question":
        if game.state == "running":
            # Logique pour passer à la question suivante
            message = "Question suivante"
    elif command == "show_answer":
        if game.state == "running":
            # Logique pour montrer la réponse
            message = "Réponse affichée"
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
