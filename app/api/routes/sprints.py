from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Sprint, User
from app.schemas import MoveIssueRequest, SprintCompleteRequest, SprintCompleteResponse, SprintCreate, SprintRead, SprintUpdate
from app.services.sprints import complete_sprint, create_sprint, move_issues, start_sprint
from app.websocket.manager import manager

router = APIRouter(tags=["sprints"])


def sprint_or_404(db: Session, sprint_id: int) -> Sprint:
    sprint = db.get(Sprint, sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint


@router.get("/projects/{project_id}/sprints", response_model=list[SprintRead])
def list_sprints(
    project_id: int,
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SprintRead]:
    stmt = select(Sprint).where(Sprint.project_id == project_id).order_by(Sprint.id.asc())
    if state:
        stmt = stmt.where(Sprint.state == state)
    return [SprintRead.model_validate(sprint) for sprint in db.scalars(stmt)]


@router.post("/projects/{project_id}/sprints", response_model=SprintRead, status_code=status.HTTP_201_CREATED)
async def create_project_sprint(
    project_id: int,
    payload: SprintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintRead:
    sprint = create_sprint(
        db,
        project_id=project_id,
        name=payload.name,
        goal=payload.goal,
        start_date=payload.start_date,
        end_date=payload.end_date,
        actor_id=current_user.id,
    )
    await manager.broadcast_project(project_id, "sprint_updated", {"sprint_id": sprint.id, "action": "created"})
    return SprintRead.model_validate(sprint)


@router.patch("/sprints/{sprint_id}", response_model=SprintRead)
def update_sprint(
    sprint_id: int,
    payload: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintRead:
    sprint = sprint_or_404(db, sprint_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)
    db.commit()
    db.refresh(sprint)
    return SprintRead.model_validate(sprint)


@router.post("/sprints/{sprint_id}/start", response_model=SprintRead)
async def start(
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintRead:
    sprint = start_sprint(db, sprint=sprint_or_404(db, sprint_id), actor_id=current_user.id)
    await manager.broadcast_project(sprint.project_id, "sprint_updated", {"sprint_id": sprint.id, "action": "started"})
    return SprintRead.model_validate(sprint)


@router.post("/sprints/{sprint_id}/complete", response_model=SprintCompleteResponse)
async def complete(
    sprint_id: int,
    payload: SprintCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SprintCompleteResponse:
    sprint, incomplete_ids, carried_ids, activity = complete_sprint(
        db,
        sprint=sprint_or_404(db, sprint_id),
        carry_over_issue_ids=payload.carry_over_issue_ids,
        new_sprint_id=payload.new_sprint_id,
        actor_id=current_user.id,
    )
    await manager.broadcast_project(sprint.project_id, "sprint_updated", activity.payload, activity.id)
    return SprintCompleteResponse(
        sprint=SprintRead.model_validate(sprint),
        velocity=sprint.velocity,
        incomplete_issue_ids=incomplete_ids,
        carried_over_issue_ids=carried_ids,
    )


@router.post("/projects/{project_id}/sprints/move-issues", response_model=dict)
async def move_project_issues(
    project_id: int,
    payload: MoveIssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    activity = move_issues(
        db,
        project_id=project_id,
        issue_ids=payload.issue_ids,
        sprint_id=payload.sprint_id,
        actor_id=current_user.id,
    )
    await manager.broadcast_project(project_id, "issue_updated", activity.payload, activity.id)
    return {"moved_issue_ids": payload.issue_ids, "sprint_id": payload.sprint_id}
