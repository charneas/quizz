"""Initial tests for the quiz application."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.models import Player, Team, Question
from app.game_modes import TeamMode, FFAMode, GridMode

# Test database
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture():
    client = TestClient(app)
    return client

def test_create_player(client):
    response = client.post(
        "/players/",
        json={"name": "Test Player", "score": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Player"
    assert data["score"] == 0

def test_team_mode():
    mode = TeamMode()
    players = [
        Player(id=i, name=f"Player {i}", score=0)
        for i in range(6)
    ]
    for player in players:
        mode.add_player(player)
    
    mode.create_teams()
    assert len(mode.teams) == 2  # 6 players should create 2 teams of 3

def test_ffa_mode():
    mode = FFAMode()
    players = [
        Player(id=i, name=f"Player {i}", score=0)
        for i in range(4)
    ]
    for player in players:
        mode.add_player(player)
    
    first_player = mode.next_player()
    assert first_player.id == 1  # Should get the next player in rotation

def test_grid_mode():
    mode = GridMode()
    player = Player(id=1, name="Test Player", score=0)
    questions = [
        Question(id=i, text=f"Question {i}", answer=f"Answer {i}",
                theme="Test", difficulty=1, points=10)
        for i in range(5)
    ]
    
    mode.initialize_grid(player, "Test", questions)
    assert len(mode.grids[player.id]) == 5  # Should have 5 questions in grid
