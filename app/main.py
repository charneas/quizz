from fastapi import FastAPI, WebSocket, HTTPException, Request, Depends, Cookie, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from typing import Dict, Optional
from .auth import get_admin, ensure_admin_exists
import secrets
import random
import string

from .db import init_db, engine
from .models import Player, Team, Question, Game, Admin, PendingQuestion
from .game_modes import TeamMode, FFAMode, GridMode
from .routers import questions, admins, games

app = FastAPI(title="Quiz App")

# Initialize database
def setup_database():
    from sqlmodel import SQLModel
    from .db import engine
    print("Création des tables...")
    SQLModel.metadata.create_all(engine)
    print("Tables créées avec succès")

# Initialize database at startup
setup_database()

# Error handling
from .logger import logger, log_error

@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    log_error(exc, f"Exception non gérée dans {request.url.path}")
    return {"detail": str(exc)}, 500

@app.on_event("startup")
async def startup_logging():
    logger.info("=== Démarrage de l'application Quiz ===")
    try:
        logger.info("Initialisation de la base de données...")
        init_db()
        logger.info("Base de données initialisée avec succès")
    except Exception as e:
        # Journalise l'erreur mais ne bloque pas le démarrage complet de l'application
        from .logger import log_error
        log_error(e, "Erreur lors de l'initialisation de la base de données au démarrage")
        logger.error(f"Erreur initialisation base de données: {e}")

# Include routers
app.include_router(questions.router)
app.include_router(admins.router)
app.include_router(games.router)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/submit")
async def submit_question_form(request: Request):
    """Affiche le formulaire de soumission de questions"""
    return templates.TemplateResponse("submit_question.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    admin: Admin = Depends(get_admin)
):
    """Affiche le panneau d'administration (protégé)"""
    response = templates.TemplateResponse("admin.html", {"request": request})
    # Force la demande d'authentification à chaque fois
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Créer un admin par défaut au démarrage
@app.on_event("startup")
async def startup_event():
    with Session(engine) as session:
        ensure_admin_exists(session, "admin", "admin123")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1", "http://127.0.0.1:8000", "http://127.0.0.1:8001", "http://51.159.55.57:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    init_db()

# Admin authentication
security = HTTPBasic()
admin_username = "admin"
admin_password = "admin123"  # À changer en production !

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, admin_username)
    correct_password = secrets.compare_digest(credentials.password, admin_password)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Active games management
active_games: Dict[str, dict] = {}

def generate_game_code():
    """Générer un code unique pour une partie."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Route admin déjà définie plus haut

@app.post("/games/create")
async def create_game(mode: str, admin: str = Depends(verify_admin)):
    game_code = generate_game_code()
    game_id = str(len(active_games) + 1)
    
    active_games[game_id] = {
        "code": game_code,
        "mode": mode,
        "players": [],
        "status": "waiting",
        "current_question": None
    }
    
    return {"game_id": game_id, "game_code": game_code}

@app.get("/games/{code}/join")
async def join_game(request: Request, code: str):
    from sqlmodel import Session, select
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.code == code)).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Si c'est une requête JSON (depuis l'API), retourner JSON
        if request.headers.get('accept') == 'application/json':
            return {
                "id": game.id,
                "code": game.code,
                "mode": game.mode,
                "state": game.state
            }
        
        # Sinon, retourner le template HTML
        return templates.TemplateResponse(f"game_{game.mode}.html", {
            "request": request,
            "game_code": code
        })

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, list[WebSocket]] = {}
        self.admin_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, room: str = None):
        await websocket.accept()
        if room == "admin":
            self.admin_connections.append(websocket)
        else:
            if room not in self.rooms:
                self.rooms[room] = []
            self.rooms[room].append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
        for room in self.rooms.values():
            if websocket in room:
                room.remove(websocket)

    async def broadcast_to_room(self, room: str, message: dict):
        if room in self.rooms:
            for connection in self.rooms[room]:
                await connection.send_json(message)
        # Envoyer aussi aux admins
        for admin in self.admin_connections:
            await admin.send_json({**message, "room": room})

    async def broadcast_to_admins(self, message: dict):
        for connection in self.admin_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# WebSocket endpoints
@app.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket):
    await manager.connect(websocket, "admin")
    try:
        while True:
            data = await websocket.receive_json()
            await handle_admin_message(websocket, data)
    except Exception as e:
        print(f"Admin WebSocket error: {e}")
        manager.disconnect(websocket)

@app.websocket("/ws/game/{game_code}")
async def game_websocket(websocket: WebSocket, game_code: str):
    game = next((g for g in active_games.values() if g["code"] == game_code), None)
    if not game:
        await websocket.close(code=4004)
        return
    
    await manager.connect(websocket, game_code)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_game_message(websocket, game_code, data)
    except:
        manager.disconnect(websocket)

async def handle_admin_message(websocket: WebSocket, data: dict):
    """Gérer les messages de l'interface admin."""
    if data["type"] == "create_game":
        game_code = generate_game_code()
        game_id = str(len(active_games) + 1)
        active_games[game_id] = {
            "code": game_code,
            "mode": data["mode"],
            "players": [],
            "status": "waiting",
            "current_question": None
        }
        await websocket.send_json({
            "type": "game_created",
            "gameId": game_id,
            "gameCode": game_code,
            "mode": data["mode"]
        })
    
    elif data["type"] == "start_game":
        game = active_games.get(data.get("gameId"))
        if game:
            game["status"] = "playing"
            await manager.broadcast_to_room(game["code"], {
                "type": "game_started"
            })

    elif data["type"] == "next_question":
        game = active_games.get(data.get("gameId"))
        if game:
            # Logique pour obtenir la prochaine question
            with Session(engine) as session:
                question = session.exec(
                    select(Question)
                    .where(Question.theme == game["mode"])
                    .offset(random.randint(0, 10))
                    .limit(1)
                ).first()
                
                if question:
                    game["current_question"] = question
                    await manager.broadcast_to_room(game["code"], {
                        "type": "new_question",
                        "question": question.text
                    })

async def handle_game_message(websocket: WebSocket, game_code: str, data: dict):
    """Gérer les messages des joueurs dans une partie."""
    game = next((g for g in active_games.values() if g["code"] == game_code), None)
    if not game:
        return
    
    if data["type"] == "join":
        player = {
            "name": data["name"],
            "websocket": websocket,
            "score": 0
        }
        game["players"].append(player)
        await manager.broadcast_to_room(game_code, {
            "type": "player_joined",
            "player": data["name"]
        })
    
    elif data["type"] == "answer":
        if game["current_question"]:
            is_correct = data["answer"].lower() == game["current_question"].answer.lower()
            for player in game["players"]:
                if player["websocket"] == websocket:
                    if is_correct:
                        player["score"] += game["current_question"].points
                    await websocket.send_json({
                        "type": "answer_result",
                        "correct": is_correct
                    })