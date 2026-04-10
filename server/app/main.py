from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware
from app.medicalorder.router import router as medical_router
from app.systemsettings.router import router as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
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
app.include_router(settings_router)
