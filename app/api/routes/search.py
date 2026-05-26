from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.repositories.issues import search_issues
from app.schemas import IssueRead, Page

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=Page)
def search(
    q: str | None = Query(default=None),
    project_id: int | None = None,
    cursor: int | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    status_id: int | None = None,
    assignee_id: int | None = None,
    priority: str | None = None,
    issue_type: str | None = None,
    sprint_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Page:
    issues, next_cursor = search_issues(
        db,
        query=q,
        project_id=project_id,
        cursor=cursor,
        limit=limit,
        status_id=status_id,
        assignee_id=assignee_id,
        priority=priority,
        issue_type=issue_type,
        sprint_id=sprint_id,
    )
    return Page(items=[IssueRead.model_validate(issue) for issue in issues], next_cursor=next_cursor)
