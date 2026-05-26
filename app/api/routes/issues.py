from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Issue, User
from app.repositories.issues import get_issue, list_project_issues
from app.schemas import IssueCreate, IssuePatch, IssueRead, IssueTransitionRequest, Page
from app.services import issues as issue_service
from app.services.workflow import get_status_by_name_or_id, transition_issue
from app.websocket.manager import manager

router = APIRouter(tags=["issues"])


def issue_or_404(db: Session, issue_id: int) -> Issue:
    issue = get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/projects/{project_id}/issues", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
async def create_issue(
    project_id: int,
    payload: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IssueRead:
    issue, activity = issue_service.create_issue(db, project_id=project_id, payload=payload, actor_id=current_user.id)
    await manager.broadcast_project(project_id, "issue_created", activity.payload, activity.id)
    return IssueRead.model_validate(issue)


@router.get("/projects/{project_id}/issues", response_model=Page)
def list_issues(
    project_id: int,
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
    issues, next_cursor = list_project_issues(
        db,
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


@router.get("/issues/{issue_id}", response_model=IssueRead)
def get_issue_detail(
    issue_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> IssueRead:
    return IssueRead.model_validate(issue_or_404(db, issue_id))


@router.patch("/issues/{issue_id}", response_model=IssueRead)
async def patch_issue(
    issue_id: int,
    payload: IssuePatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IssueRead:
    issue = issue_or_404(db, issue_id)
    try:
        updated, activity = issue_service.patch_issue(db, issue=issue, payload=payload, actor_id=current_user.id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_409_CONFLICT:
            detail = {"message": "Issue version conflict", "current_issue": IssueRead.model_validate(issue).model_dump(mode="json")}
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
        raise
    if activity:
        await manager.broadcast_project(updated.project_id, "issue_updated", activity.payload, activity.id)
    return IssueRead.model_validate(updated)


@router.post("/issues/{issue_id}/transitions", response_model=IssueRead)
async def transition(
    issue_id: int,
    payload: IssueTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IssueRead:
    issue = issue_or_404(db, issue_id)
    target = get_status_by_name_or_id(
        db,
        project_id=issue.project_id,
        status_id=payload.target_status_id,
        status_name=payload.target_status_name,
    )
    updated, activity = transition_issue(
        db,
        issue=issue,
        target_status=target,
        actor_id=current_user.id,
        expected_version=payload.expected_version,
    )
    await manager.broadcast_project(updated.project_id, "issue_moved", activity.payload, activity.id)
    return IssueRead.model_validate(updated)


@router.post("/issues/{issue_id}/watch", response_model=dict)
def watch_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    issue = issue_or_404(db, issue_id)
    issue_service.watch_issue(db, issue=issue, user_id=current_user.id)
    return {"watched": True}


@router.delete("/issues/{issue_id}/watch", status_code=status.HTTP_204_NO_CONTENT)
def unwatch_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    issue = issue_or_404(db, issue_id)
    issue_service.unwatch_issue(db, issue=issue, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
