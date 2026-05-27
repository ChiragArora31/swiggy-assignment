from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from app.api.routes import activity, auth, comments, custom_fields, demo as demo_routes, issues, projects, search, sprints, users
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.demo import DEMO_HTML
from app.models import ActivityLog
from app.websocket.manager import manager

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Jira-like project management backend with workflows, sprints, audit logs, and real-time board sync.",
)

app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(issues.router, prefix="/api")
app.include_router(sprints.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(custom_fields.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(demo_routes.router, prefix="/api")


@app.on_event("startup")
def maybe_create_tables() -> None:
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    if settings.seed_on_startup:
        from app.seed import seed

        seed()


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/demo")


@app.get("/demo", include_in_schema=False)
def demo() -> HTMLResponse:
    return HTMLResponse(DEMO_HTML)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/projects/{project_id}/board")
async def project_board_socket(
    websocket: WebSocket,
    project_id: int,
    user_id: int,
    last_event_id: int | None = None,
) -> None:
    await manager.connect_project(project_id, user_id, websocket)
    try:
        if last_event_id is not None:
            with SessionLocal() as db:
                events = list(
                    db.scalars(
                        select(ActivityLog)
                        .where(ActivityLog.project_id == project_id, ActivityLog.id > last_event_id)
                        .order_by(ActivityLog.id.asc())
                    )
                )
                for event in events:
                    await websocket.send_json(
                        {"event_id": event.id, "event_type": event.event_type, "payload": event.payload}
                    )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect_project(project_id, user_id, websocket)
