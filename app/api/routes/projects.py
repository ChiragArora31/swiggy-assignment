from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Issue, Project, User, WorkflowStatus
from app.schemas import BoardColumn, BoardRead, IssueRead
from app.websocket.manager import manager

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/{project_id}/board", response_model=BoardRead)
def get_board(
    project_id: int,
    sprint_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> BoardRead:
    statuses = list(
        db.scalars(select(WorkflowStatus).where(WorkflowStatus.project_id == project_id).order_by(WorkflowStatus.position))
    )
    columns: list[BoardColumn] = []
    for status in statuses:
        stmt = (
            select(Issue)
            .options(joinedload(Issue.status), joinedload(Issue.assignee), joinedload(Issue.reporter))
            .where(Issue.project_id == project_id, Issue.status_id == status.id)
            .order_by(Issue.issue_number)
        )
        if sprint_id is not None:
            stmt = stmt.where(Issue.sprint_id == sprint_id)
        issues = list(db.scalars(stmt))
        columns.append(BoardColumn(status=status, issues=[IssueRead.model_validate(issue) for issue in issues]))
    return BoardRead(project_id=project_id, columns=columns, active_viewers=manager.active_viewers(project_id))


@router.get("/{project_id}/backlog", response_model=list[IssueRead])
def get_backlog(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[IssueRead]:
    issues = list(
        db.scalars(
            select(Issue)
            .options(joinedload(Issue.status), joinedload(Issue.assignee), joinedload(Issue.reporter))
            .where(Issue.project_id == project_id, Issue.sprint_id.is_(None))
            .order_by(Issue.issue_number.asc())
        )
    )
    return [IssueRead.model_validate(issue) for issue in issues]


@router.get("", response_model=list[dict])
def list_projects(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    projects = list(db.scalars(select(Project).order_by(Project.id.asc())))
    return [{"id": project.id, "name": project.name, "key": project.key} for project in projects]
