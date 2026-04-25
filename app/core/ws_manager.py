"""
WebSocket Connection Manager.
Mengelola active WebSocket connections per device.
"""

import logging
from typing import Dict, Set
from uuid import UUID
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Mengelola WebSocket connections.
    Setiap device bisa punya banyak subscriber (browser tabs).
    """

    def __init__(self):
        # device_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, device_id: str, websocket: WebSocket):
        """Accept dan register WebSocket connection untuk device tertentu."""
        await websocket.accept()
        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()
        self.active_connections[device_id].add(websocket)
        logger.debug(f"WS connected: device {device_id} (total: {len(self.active_connections[device_id])})")

    def disconnect(self, device_id: str, websocket: WebSocket):
        """Remove WebSocket connection."""
        if device_id in self.active_connections:
            self.active_connections[device_id].discard(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
        logger.debug(f"WS disconnected: device {device_id}")

    async def broadcast(self, device_id: str, data: dict):
        """Kirim data ke semua subscriber device tertentu."""
        if device_id not in self.active_connections:
            return

        dead_connections = set()
        for ws in self.active_connections[device_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead_connections.add(ws)

        # Cleanup dead connections
        for ws in dead_connections:
            self.active_connections[device_id].discard(ws)

    def get_subscriber_count(self, device_id: str) -> int:
        """Jumlah subscriber aktif untuk device tertentu."""
        return len(self.active_connections.get(device_id, set()))

    def get_total_connections(self) -> int:
        """Total semua active connections."""
        return sum(len(conns) for conns in self.active_connections.values())


# Singleton instance
ws_manager = ConnectionManager()
