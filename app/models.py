from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    score: int = 0
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    game_id: Optional[int] = Field(default=None, foreign_key="game.id")
    team: Optional["Team"] = Relationship(back_populates="players")
    game: Optional["Game"] = Relationship(back_populates="players")

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    score: int = 0
    players: List[Player] = Relationship(back_populates="team")

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    answer: str
    theme: str
    difficulty: int
    points: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # Nom de l'utilisateur qui a créé la question

class PendingQuestion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    answer: str
    theme: str
    difficulty: int
    points: int = 10
    submitter_name: str
    submitter_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, approved, rejected
    admin_comment: Optional[str] = None  # Commentaire de l'administrateur en cas de rejet

class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mode: str
    code: str = Field(unique=True)
    state: str = "waiting"  # waiting, running, paused, finished
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_by: Optional[int] = Field(default=None, foreign_key="admin.id")
    winner_id: Optional[int] = Field(default=None, foreign_key="team.id")
    players: List[Player] = Relationship(back_populates="game")

class Bonus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    effect: str  # JSON string containing the bonus effect
    duration: Optional[int] = None  # Duration in seconds, if applicable

class Admin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    hashed_password: str
    email: Optional[str] = None
    is_superadmin: bool = False  # Seuls les superadmins peuvent gérer d'autres admins
    created_at: datetime = Field(default_factory=datetime.utcnow)
