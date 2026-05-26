from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.project_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self.presence: dict[str, set[int]] = defaultdict(set)

    async def connect_project(self, project_id: int, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.project_connections[project_id].add(websocket)
        self.presence[f"project:{project_id}"].add(user_id)
        await self.broadcast_project(project_id, "presence_updated", {"active_viewers": self.active_viewers(project_id)})

    async def disconnect_project(self, project_id: int, user_id: int, websocket: WebSocket) -> None:
        self.project_connections[project_id].discard(websocket)
        self.presence[f"project:{project_id}"].discard(user_id)
        await self.broadcast_project(project_id, "presence_updated", {"active_viewers": self.active_viewers(project_id)})

    def active_viewers(self, project_id: int) -> list[int]:
        return sorted(self.presence[f"project:{project_id}"])

    async def broadcast_project(
        self,
        project_id: int,
        event_type: str,
        payload: dict[str, Any],
        event_id: int | None = None,
    ) -> None:
        message = {"event_id": event_id, "event_type": event_type, "payload": payload}
        stale: list[WebSocket] = []
        for websocket in self.project_connections[project_id]:
            try:
                await websocket.send_json(message)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.project_connections[project_id].discard(websocket)


manager = ConnectionManager()
