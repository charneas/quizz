import random
from typing import List, Dict
from .models import Player, Team, Question, Game

def generate_game_code(length: int = 6) -> str:
    """Génère un code unique pour une partie."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    code = ''.join(random.choices(chars, k=length))
    return code

class GameMode:
    def __init__(self):
        self.players: List[Player] = []
        self.current_question: Question = None
        self.game: Game = None

    def add_player(self, player: Player):
        self.players.append(player)

    def remove_player(self, player: Player):
        self.players.remove(player)

class TeamMode(GameMode):
    def __init__(self):
        super().__init__()
        self.teams: List[Team] = []
        self.bonuses: Dict[int, List[str]] = {}  # team_id -> list of active bonuses

    def create_teams(self, team_size: int = 3):
        """Create random teams of specified size from available players."""
        random.shuffle(self.players)
        num_teams = len(self.players) // team_size
        
        for i in range(num_teams):
            team = Team(name=f"Team {i+1}")
            team_players = self.players[i*team_size:(i+1)*team_size]
            for player in team_players:
                player.team = team
            self.teams.append(team)

    def apply_bonus(self, from_team: Team, to_team: Team, bonus_type: str):
        """Apply a bonus/malus from one team to another."""
        if bonus_type not in self.bonuses.get(to_team.id, []):
            self.bonuses.setdefault(to_team.id, []).append(bonus_type)

class FFAMode(GameMode):
    def __init__(self):
        super().__init__()
        self.theme: str = ""
        self.current_player_index: int = 0
        self.rounds: int = 2

    def next_player(self) -> Player:
        """Get the next player in the rotation."""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        return self.players[self.current_player_index]

class GridMode(GameMode):
    def __init__(self):
        super().__init__()
        self.grid_size = 25  # 5x5 grid
        self.player_questions = 5
        self.grids: Dict[int, Dict[int, Question]] = {}  # player_id -> {position: question}

    def initialize_grid(self, player: Player, theme: str, questions: List[Question]):
        """Initialize a player's grid with their themed questions and difficult questions."""
        positions = random.sample(range(self.grid_size), self.player_questions)
        self.grids[player.id] = {pos: question for pos, question in zip(positions, questions)}
