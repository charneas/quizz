from sqlmodel import SQLModel, create_engine, Session
import os

# SQLite database URL
DATABASE_URL = "sqlite:///./quiz.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

def init_db():
    """Initialize the database, creating all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session
