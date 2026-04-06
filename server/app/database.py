import os
from dotenv import load_dotenv, find_dotenv
from sqlmodel import create_engine, Session, SQLModel


load_dotenv(find_dotenv())
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
