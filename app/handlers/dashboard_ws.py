"""WebSocket connection manager for dashboard broadcasts."""
import asyncio
import json
import logging
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class DashboardConnectionManager:
    """Manages dashboard WebSocket clients."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("[Dashboard] WebSocket connected (%d clients)", len(self._connections))

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("[Dashboard] WebSocket disconnected (%d clients)", len(self._connections))

    async def broadcast(self, event: str, payload: dict):
        """Broadcast an event to all connected clients."""
        async with self._lock:
            connections = list(self._connections)
        if not connections:
            return

        message = json.dumps({"event": event, "data": payload})

        async def _send(ws: WebSocket):
            try:
                await ws.send_text(message)
            except Exception as exc:  # pragma: no cover - network issues
                logger.debug("[Dashboard] Broadcast error: %s", exc)
                await self.disconnect(ws)

        await asyncio.gather(*(_send(ws) for ws in connections), return_exceptions=True)


dashboard_manager = DashboardConnectionManager()
