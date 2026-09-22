from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from backend.app.core.config import settings
from backend.app.core.logging import configure_logging, get_logger
from backend.app.database.session import init_db, close_db, engine
from backend.app.api.routes import (
    auth,
    trains,
    stations,
    predictions,
    weather,
    alerts,
    congestion,
    simulation,
    copilot,
)
from backend.app.realtime.websocket_manager import manager, websocket_endpoint
from backend.app.simulation.engine import simulation_engine
from backend.app.schemas.common import HealthResponse, ErrorResponse
from backend.app.core.security import get_current_active_user
from backend.app.models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger = get_logger(__name__)

    await init_db()

    simulation_engine.add_callback(on_simulation_update)

    logger.info("Application startup complete")
    yield

    await simulation_engine.stop()
    await close_db()
    logger.info("Application shutdown complete")


def on_simulation_update(status: dict):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(manager.broadcast_simulation_status(status))
    except Exception:
        pass


app = FastAPI(
    title="RAILPULSE AI",
    description="RailPulse AI - Real-Time Dynamic ETA Prediction, Train Tracking and Railway Operations Intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logger = get_logger(__name__)
    logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": str(exc), "traceback": tb[-2000:]},
    )


app.include_router(auth.router)
app.include_router(trains.router)
app.include_router(stations.router)
app.include_router(predictions.router)
app.include_router(weather.router)
app.include_router(alerts.router)
app.include_router(congestion.router)
app.include_router(simulation.router)
app.include_router(copilot.router)


@app.get("/")
async def root():
    return {
        "name": "RAILPULSE AI",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.environment,
        database="connected",
        redis="connected",
    )


@app.websocket("/ws/trains")
async def websocket_trains(websocket: WebSocket):
    await websocket_endpoint(websocket, "trains")


@app.websocket("/ws/train/{train_id}")
async def websocket_train(websocket: WebSocket, train_id: int):
    await websocket_endpoint(websocket, "train", train_id)


@app.websocket("/ws/control-room")
async def websocket_control_room(websocket: WebSocket):
    await websocket_endpoint(websocket, "control-room")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)