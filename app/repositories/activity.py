from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ActivityLog


def log_activity(
    db: Session,
    *,
    project_id: int,
    event_type: str,
    actor_id: int | None = None,
    issue_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> ActivityLog:
    activity = ActivityLog(
        project_id=project_id,
        issue_id=issue_id,
        actor_id=actor_id,
        event_type=event_type,
        payload=payload or {},
    )
    db.add(activity)
    db.flush()
    return activity


def list_activity(
    db: Session,
    *,
    project_id: int,
    cursor: int | None = None,
    limit: int = 50,
    event_type: str | None = None,
    issue_id: int | None = None,
) -> tuple[list[ActivityLog], int | None]:
    stmt = select(ActivityLog).where(ActivityLog.project_id == project_id)
    if cursor:
        stmt = stmt.where(ActivityLog.id < cursor)
    if event_type:
        stmt = stmt.where(ActivityLog.event_type == event_type)
    if issue_id:
        stmt = stmt.where(ActivityLog.issue_id == issue_id)
    stmt = stmt.order_by(ActivityLog.id.desc()).limit(limit + 1)
    rows = list(db.scalars(stmt))
    next_cursor = rows[-1].id if len(rows) > limit else None
    return rows[:limit], next_cursor
