"""
WebSocket Connection Manager.
Mengelola active WebSocket connections per device.
Dirancang untuk single asyncio event loop (bukan multi-threaded).
"""

import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Mengelola WebSocket connections.
    Setiap device bisa punya banyak subscriber (browser tabs).
    """

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    def register(self, device_id: str, websocket: WebSocket):
        """Register WebSocket connection (accept sudah dilakukan di caller)."""
        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()
        self.active_connections[device_id].add(websocket)
        logger.debug(f"WS registered: device {device_id} (total: {len(self.active_connections[device_id])})")

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

        # Copy set sebelum iterasi untuk menghindari RuntimeError
        # jika disconnect() dipanggil dari thread lain saat iterasi
        connections = self.active_connections[device_id].copy()

        dead_connections = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead_connections.append(ws)

        # Cleanup dead connections
        for ws in dead_connections:
            self.active_connections.get(device_id, set()).discard(ws)

    def get_subscriber_count(self, device_id: str) -> int:
        """Jumlah subscriber aktif untuk device tertentu."""
        return len(self.active_connections.get(device_id, set()))

    def get_total_connections(self) -> int:
        """Total semua active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    async def close_device_connections(self, device_id: str, code: int = 4004, reason: str = "Device dihapus"):
        """
        Tutup semua WebSocket connections untuk device tertentu.
        Dipanggil saat device dihapus atau di-unclaim.
        """
        if device_id not in self.active_connections:
            return 0

        connections = self.active_connections[device_id].copy()
        closed = 0
        for ws in connections:
            try:
                await ws.close(code=code, reason=reason)
                closed += 1
            except Exception:
                pass  # Connection mungkin sudah mati

        # Cleanup — disconnect() akan dipanggil oleh finally block di ws.py,
        # tapi kita bersihkan juga di sini untuk safety
        self.active_connections.pop(device_id, None)
        logger.info(f"Closed {closed} WS connections for device {device_id}")
        return closed


# Singleton instance
ws_manager = ConnectionManager()
