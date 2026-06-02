from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import Session
from app.core.database import create_db_and_tables, engine
from fastapi.middleware.cors import CORSMiddleware
from app.modules.medical_order.router import router as medical_router
from app.modules.triage.router import router as triage_router
from app.modules.systemsettings.router import router as settings_router
from app.modules.systemsettings.seed import seed_system_settings
from app.modules.triage.seed import seed_triage_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_system_settings(session)
        seed_triage_rules(session)
        session.commit()
    yield


app = FastAPI(
    title="Backend Triage Ordenes Médicas",
    lifespan=lifespan,
    description="Tesis Orquestador Imágenes",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medical_router)
app.include_router(triage_router)
app.include_router(settings_router)
