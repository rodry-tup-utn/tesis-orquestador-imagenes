from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from app.core.database import create_db_and_tables, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware
from app.modules.medical_order.router import router as medical_router
from app.modules.auth.router import router as auth_router
from app.modules.triage.router import router as triage_router
from app.modules.systemsettings.router import router as settings_router
from app.modules.systemsettings.seed import seed_system_settings
from app.modules.triage.seed import seed_triage_rules
from app.modules.medical_order import notification_model  # Para registro de la metadata
from app.core.websocket import manager
from app.core.security import decode_access_token
import asyncio
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

app.include_router(auth_router)
app.include_router(medical_router)
app.include_router(triage_router)
app.include_router(settings_router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # La primera trama es obligatoriamente de autenticacion para no exponer el
    # canal de eventos a clientes anonimos. El token no viaja en la URL.
    await websocket.accept()
    try:
        raw_auth = await asyncio.wait_for(websocket.receive_text(), timeout=5)
        message = json.loads(raw_auth)
        token = message.get("token") if message.get("type") == "auth" else None
        if not token or decode_access_token(token) is None:
            await websocket.close(code=1008, reason="No autorizado")
            return

        manager.active_connections.append(websocket)
        await websocket.send_text("authenticated")
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, asyncio.TimeoutError, json.JSONDecodeError):
        manager.disconnect(websocket)
