from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Issue, IssueType, WorkflowStatus, WorkflowTransition
from app.models.models import NotificationType
from app.repositories.activity import log_activity
from app.services.notifications import create_notification, notify_issue_watchers


def get_status_by_name_or_id(
    db: Session,
    *,
    project_id: int,
    status_id: int | None = None,
    status_name: str | None = None,
) -> WorkflowStatus:
    if status_id is None and not status_name:
        raise HTTPException(status_code=422, detail="Provide target_status_id or target_status_name")

    stmt = select(WorkflowStatus).where(WorkflowStatus.project_id == project_id)
    if status_id is not None:
        stmt = stmt.where(WorkflowStatus.id == status_id)
    else:
        stmt = stmt.where(WorkflowStatus.name == status_name)
    status_obj = db.scalar(stmt)
    if not status_obj:
        raise HTTPException(status_code=404, detail="Target workflow status not found")
    return status_obj


def allowed_transitions(db: Session, issue: Issue) -> list[WorkflowStatus]:
    stmt = (
        select(WorkflowStatus)
        .join(WorkflowTransition, WorkflowTransition.to_status_id == WorkflowStatus.id)
        .where(
            WorkflowTransition.project_id == issue.project_id,
            WorkflowTransition.from_status_id == issue.status_id,
        )
        .order_by(WorkflowStatus.position.asc())
    )
    return list(db.scalars(stmt))


def validate_transition_hooks(issue: Issue, target_status: WorkflowStatus) -> None:
    if target_status.name == "In Progress" and issue.assignee_id is None:
        raise HTTPException(status_code=422, detail="Assignee is required before moving to In Progress")
    done_types = {IssueType.STORY.value, IssueType.TASK.value, IssueType.BUG.value}
    if target_status.is_done and issue.issue_type in done_types and issue.story_points is None:
        raise HTTPException(status_code=422, detail="Story points are required before moving to Done")


def transition_issue(
    db: Session,
    *,
    issue: Issue,
    target_status: WorkflowStatus,
    actor_id: int,
    expected_version: int | None = None,
) -> tuple[Issue, Any]:
    if expected_version is not None and issue.version != expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Issue version conflict", "current_version": issue.version, "issue_id": issue.id},
        )

    allowed = allowed_transitions(db, issue)
    if target_status.id not in {status_obj.id for status_obj in allowed}:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Invalid transition from {issue.status.name} to {target_status.name}",
                "allowed_transitions": [{"id": s.id, "name": s.name} for s in allowed],
            },
        )

    validate_transition_hooks(issue, target_status)
    previous_status = issue.status.name
    issue.status_id = target_status.id
    issue.version += 1

    activity = log_activity(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=actor_id,
        event_type="issue_moved",
        payload={
            "issue_id": issue.id,
            "issue_key": issue.issue_key,
            "from_status": previous_status,
            "to_status": target_status.name,
            "version": issue.version,
        },
    )

    if target_status.name == "In Review":
        recipients = {watcher.user_id for watcher in issue.watchers}
        if issue.assignee_id:
            recipients.add(issue.assignee_id)
        for user_id in recipients - {actor_id}:
            create_notification(
                db,
                user_id=user_id,
                notification_type=NotificationType.STATUS_CHANGE,
                message=f"{issue.issue_key} moved to In Review",
                issue_id=issue.id,
            )
    else:
        notify_issue_watchers(
            db,
            issue=issue,
            message=f"{issue.issue_key} moved from {previous_status} to {target_status.name}",
            skip_user_ids={actor_id},
        )

    db.commit()
    db.refresh(issue)
    return issue, activity
