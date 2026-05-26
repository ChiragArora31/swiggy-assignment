from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Comment, Issue


def get_issue(db: Session, issue_id: int) -> Issue | None:
    return db.scalar(
        select(Issue)
        .options(
            joinedload(Issue.status),
            joinedload(Issue.assignee),
            joinedload(Issue.reporter),
            selectinload(Issue.watchers),
        )
        .where(Issue.id == issue_id)
    )


def list_project_issues(
    db: Session,
    *,
    project_id: int,
    cursor: int | None = None,
    limit: int = 50,
    status_id: int | None = None,
    assignee_id: int | None = None,
    priority: str | None = None,
    issue_type: str | None = None,
    sprint_id: int | None = None,
) -> tuple[list[Issue], int | None]:
    stmt = (
        select(Issue)
        .options(joinedload(Issue.status), joinedload(Issue.assignee), joinedload(Issue.reporter))
        .where(Issue.project_id == project_id)
    )
    if cursor:
        stmt = stmt.where(Issue.id > cursor)
    if status_id:
        stmt = stmt.where(Issue.status_id == status_id)
    if assignee_id:
        stmt = stmt.where(Issue.assignee_id == assignee_id)
    if priority:
        stmt = stmt.where(Issue.priority == priority)
    if issue_type:
        stmt = stmt.where(Issue.issue_type == issue_type)
    if sprint_id is not None:
        stmt = stmt.where(Issue.sprint_id == sprint_id)
    stmt = stmt.order_by(Issue.id.asc()).limit(limit + 1)
    rows = list(db.scalars(stmt))
    next_cursor = rows[-1].id if len(rows) > limit else None
    return rows[:limit], next_cursor


def search_issues(
    db: Session,
    *,
    query: str | None,
    project_id: int | None = None,
    cursor: int | None = None,
    limit: int = 50,
    status_id: int | None = None,
    assignee_id: int | None = None,
    priority: str | None = None,
    issue_type: str | None = None,
    sprint_id: int | None = None,
) -> tuple[list[Issue], int | None]:
    stmt = (
        select(Issue)
        .options(joinedload(Issue.status), joinedload(Issue.assignee), joinedload(Issue.reporter))
        .distinct()
        .outerjoin(Comment, Comment.issue_id == Issue.id)
    )
    if project_id:
        stmt = stmt.where(Issue.project_id == project_id)
    if cursor:
        stmt = stmt.where(Issue.id > cursor)
    if query:
        pattern = f"%{query.lower()}%"
        stmt = stmt.where(
            or_(
                Issue.title.ilike(pattern),
                Issue.description.ilike(pattern),
                Comment.body.ilike(pattern),
            )
        )
    if status_id:
        stmt = stmt.where(Issue.status_id == status_id)
    if assignee_id:
        stmt = stmt.where(Issue.assignee_id == assignee_id)
    if priority:
        stmt = stmt.where(Issue.priority == priority)
    if issue_type:
        stmt = stmt.where(Issue.issue_type == issue_type)
    if sprint_id is not None:
        stmt = stmt.where(Issue.sprint_id == sprint_id)
    stmt = stmt.order_by(Issue.id.asc()).limit(limit + 1)
    rows = list(db.scalars(stmt))
    next_cursor = rows[-1].id if len(rows) > limit else None
    return rows[:limit], next_cursor
