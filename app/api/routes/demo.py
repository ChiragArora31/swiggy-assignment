from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Issue, User
from app.repositories.issues import get_issue
from app.schemas import IssuePatch
from app.seed import reset_seed_data
from app.services.issues import patch_issue
from app.services.workflow import get_status_by_name_or_id, transition_issue

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reset", response_model=dict)
def reset_demo_data() -> dict:
    reset_seed_data()
    return {"reset": True}


def issue_or_404(db: Session, issue_id: int) -> Issue:
    issue = get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("/issues/{issue_id}/invalid-transition", response_model=dict)
def demonstrate_invalid_transition(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    issue = issue_or_404(db, issue_id)
    target = get_status_by_name_or_id(db, project_id=issue.project_id, status_name="Done")
    try:
        transition_issue(db, issue=issue, target_status=target, actor_id=current_user.id, expected_version=issue.version)
    except HTTPException as exc:
        db.rollback()
        return {"expected_error": True, "status_code": exc.status_code, "detail": exc.detail}
    return {"expected_error": False, "message": "The selected issue can move to Done from its current status."}


@router.post("/issues/{issue_id}/stale-conflict", response_model=dict)
def demonstrate_stale_conflict(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    issue = issue_or_404(db, issue_id)
    stale_version = issue.version
    patch_issue(
        db,
        issue=issue,
        payload=IssuePatch(expected_version=stale_version, title=f"{issue.title} (updated)"),
        actor_id=current_user.id,
    )
    issue = issue_or_404(db, issue_id)
    try:
        patch_issue(
            db,
            issue=issue,
            payload=IssuePatch(expected_version=stale_version, priority="critical"),
            actor_id=current_user.id,
        )
    except HTTPException as exc:
        db.rollback()
        return {
            "expected_error": True,
            "status_code": exc.status_code,
            "detail": {"message": "Issue version conflict", "issue_id": issue.id, "current_version": issue.version},
        }
    return {"expected_error": False, "message": "No conflict occurred."}
