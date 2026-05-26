from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.repositories.activity import list_activity
from app.schemas import ActivityRead, Page

router = APIRouter(prefix="/projects/{project_id}/activity", tags=["activity"])


@router.get("", response_model=Page)
def project_activity(
    project_id: int,
    cursor: int | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    event_type: str | None = None,
    issue_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page:
    events, next_cursor = list_activity(
        db,
        project_id=project_id,
        cursor=cursor,
        limit=limit,
        event_type=event_type,
        issue_id=issue_id,
    )
    return Page(items=[ActivityRead.model_validate(event) for event in events], next_cursor=next_cursor)
