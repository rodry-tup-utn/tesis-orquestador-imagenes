import os
from dotenv import load_dotenv
from pathlib import Path
from sqlmodel import create_engine, Session, SQLModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
dot_env_path = BASE_DIR / ".env"

# 2. Cargamos el archivo especificando la ruta exacta
load_dotenv(dotenv_path=dot_env_path)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "🚨 ¡ERROR CRITICO! La variable DATABASE_URL no fue encontrada. Revisa el archivo .env"
    )

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
