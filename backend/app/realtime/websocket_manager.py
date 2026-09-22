import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class WSMessage(BaseModel):
    type: str
    data: dict
    timestamp: str = datetime.now(timezone.utc).isoformat()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.train_subscriptions: Dict[int, Set[WebSocket]] = {}
        self.control_room_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, channel: str = "general", user_id: Optional[int] = None, train_id: Optional[int] = None):
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)

        if train_id:
            if train_id not in self.train_subscriptions:
                self.train_subscriptions[train_id] = set()
            self.train_subscriptions[train_id].add(websocket)

        if channel == "control-room":
            self.control_room_connections.add(websocket)

        logger.info("WebSocket connected", channel=channel, user_id=user_id, train_id=train_id)

    def disconnect(self, websocket: WebSocket, channel: str = "general", user_id: Optional[int] = None, train_id: Optional[int] = None):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)

        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)

        if train_id and train_id in self.train_subscriptions:
            self.train_subscriptions[train_id].discard(websocket)

        self.control_room_connections.discard(websocket)

        logger.info("WebSocket disconnected", channel=channel, user_id=user_id, train_id=train_id)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Failed to send personal message", error=str(e))

    async def broadcast_to_channel(self, channel: str, message: dict):
        if channel not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[channel]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            self.active_connections[channel].discard(ws)

    async def broadcast_to_train(self, train_id: int, message: dict):
        if train_id not in self.train_subscriptions:
            return

        disconnected = set()
        for websocket in self.train_subscriptions[train_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            self.train_subscriptions[train_id].discard(ws)

    async def broadcast_to_user(self, user_id: int, message: dict):
        if user_id not in self.user_connections:
            return

        disconnected = set()
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            self.user_connections[user_id].discard(ws)

    async def broadcast_to_control_room(self, message: dict):
        disconnected = set()
        for websocket in self.control_room_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            self.control_room_connections.discard(ws)

    async def broadcast_train_update(self, train_id: int, data: dict):
        message = WSMessage(type="train_update", data=data).model_dump()
        await self.broadcast_to_train(train_id, message)
        await self.broadcast_to_control_room(message)

    async def broadcast_train_position(self, train_id: int, position: dict):
        message = WSMessage(type="train_position", data={"train_id": train_id, **position}).model_dump()
        await self.broadcast_to_train(train_id, message)
        await self.broadcast_to_control_room(message)

    async def broadcast_eta_update(self, train_id: int, eta_data: dict):
        message = WSMessage(type="eta_update", data={"train_id": train_id, **eta_data}).model_dump()
        await self.broadcast_to_train(train_id, message)
        await self.broadcast_to_control_room(message)

    async def broadcast_alert(self, alert: dict):
        message = WSMessage(type="alert", data=alert).model_dump()
        await self.broadcast_to_control_room(message)
        if alert.get("train_id"):
            await self.broadcast_to_train(alert["train_id"], message)

    async def broadcast_congestion_update(self, congestion_data: dict):
        message = WSMessage(type="congestion_update", data=congestion_data).model_dump()
        await self.broadcast_to_control_room(message)

    async def broadcast_weather_update(self, weather_data: dict):
        message = WSMessage(type="weather_update", data=weather_data).model_dump()
        await self.broadcast_to_control_room(message)

    async def broadcast_station_event(self, event: dict):
        message = WSMessage(type="station_event", data=event).model_dump()
        await self.broadcast_to_control_room(message)
        if event.get("train_id"):
            await self.broadcast_to_train(event["train_id"], message)

    async def broadcast_simulation_status(self, status: dict):
        message = WSMessage(type="simulation_status", data=status).model_dump()
        await self.broadcast_to_control_room(message)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, channel: str = "general", train_id: Optional[int] = None):
    user_id = None
    try:
        await manager.connect(websocket, channel, user_id, train_id)
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "subscribe_train":
                    train_id = msg.get("train_id")
                    if train_id:
                        if train_id not in manager.train_subscriptions:
                            manager.train_subscriptions[train_id] = set()
                        manager.train_subscriptions[train_id].add(websocket)
                elif msg.get("type") == "unsubscribe_train":
                    train_id = msg.get("train_id")
                    if train_id and train_id in manager.train_subscriptions:
                        manager.train_subscriptions[train_id].discard(websocket)
                elif msg.get("type") == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        manager.disconnect(websocket, channel, user_id, train_id)