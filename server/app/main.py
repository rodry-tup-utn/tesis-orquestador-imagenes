from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from app.core.database import create_db_and_tables, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from app.modules.medical_order.router import router as medical_router
from app.modules.triage.router import router as triage_router
from app.modules.systemsettings.router import router as settings_router
from app.modules.systemsettings.seed import seed_system_settings
from app.modules.triage.seed import seed_triage_rules
from app.modules.medical_order import notification_model  # Para registro de la metadata
from app.core.websocket import manager
import json


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await seed_system_settings(session)
        await seed_triage_rules(session)
        await session.commit()
    yield


app = FastAPI(
    title="Backend Triage Ordenes Médicas",
    lifespan=lifespan,
    description="Tesis Orquestador Imágenes",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:8080", 
        "http://localhost", 
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(medical_router)
app.include_router(triage_router)
app.include_router(settings_router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
