import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

_db_path = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "data" / "a11yfix.db"))
Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{_db_path}", echo=False, connect_args={"check_same_thread": False})


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
