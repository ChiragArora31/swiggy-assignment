from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Issue, IssueType, Project, User, Watcher, WorkflowStatus
from app.repositories.activity import log_activity
from app.schemas import IssueCreate, IssuePatch
from app.services.notifications import create_notification, notify_issue_watchers
from app.models.models import NotificationType

VALID_PARENT_TYPES = {
    IssueType.EPIC.value: {IssueType.STORY.value, IssueType.TASK.value, IssueType.BUG.value},
    IssueType.STORY.value: {IssueType.SUB_TASK.value},
    IssueType.TASK.value: {IssueType.SUB_TASK.value},
    IssueType.BUG.value: {IssueType.SUB_TASK.value},
}


def ensure_user(db: Session, user_id: int | None) -> User | None:
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


def default_status(db: Session, project_id: int) -> WorkflowStatus:
    status_obj = db.scalar(
        select(WorkflowStatus).where(WorkflowStatus.project_id == project_id).order_by(WorkflowStatus.position.asc())
    )
    if not status_obj:
        raise HTTPException(status_code=422, detail="Project has no workflow statuses")
    return status_obj


def validate_parent(db: Session, issue_type: str, parent_issue_id: int | None, project_id: int) -> None:
    if issue_type == IssueType.SUB_TASK.value and parent_issue_id is None:
        raise HTTPException(status_code=422, detail="Sub-task requires a parent story, task, or bug")
    if issue_type != IssueType.SUB_TASK.value and parent_issue_id is None:
        return
    parent = db.get(Issue, parent_issue_id)
    if not parent or parent.project_id != project_id:
        raise HTTPException(status_code=422, detail="Parent issue not found in project")
    allowed_children = VALID_PARENT_TYPES.get(parent.issue_type, set())
    if issue_type not in allowed_children:
        raise HTTPException(
            status_code=422,
            detail=f"{parent.issue_type} cannot be parent of {issue_type}",
        )


def create_issue(db: Session, *, project_id: int, payload: IssueCreate, actor_id: int) -> tuple[Issue, Any]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    reporter_id = payload.reporter_id or actor_id
    ensure_user(db, reporter_id)
    ensure_user(db, payload.assignee_id)
    validate_parent(db, payload.issue_type, payload.parent_issue_id, project_id)

    issue_number = project.next_issue_number
    project.next_issue_number += 1
    issue = Issue(
        project_id=project.id,
        issue_number=issue_number,
        issue_key=f"{project.key}-{issue_number}",
        issue_type=payload.issue_type,
        title=payload.title,
        description=payload.description,
        status_id=default_status(db, project.id).id,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        reporter_id=reporter_id,
        sprint_id=payload.sprint_id,
        parent_issue_id=payload.parent_issue_id,
        story_points=payload.story_points,
        labels=payload.labels,
    )
    db.add(issue)
    db.flush()

    if issue.assignee_id:
        create_notification(
            db,
            user_id=issue.assignee_id,
            notification_type=NotificationType.ASSIGNMENT,
            message=f"You were assigned {issue.issue_key}",
            issue_id=issue.id,
        )

    activity = log_activity(
        db,
        project_id=project.id,
        issue_id=issue.id,
        actor_id=actor_id,
        event_type="issue_created",
        payload={"issue_id": issue.id, "issue_key": issue.issue_key},
    )
    db.commit()
    db.refresh(issue)
    return issue, activity


def patch_issue(db: Session, *, issue: Issue, payload: IssuePatch, actor_id: int) -> tuple[Issue, Any]:
    if issue.version != payload.expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Issue version conflict", "current_issue": issue},
        )

    changes: dict[str, dict[str, Any]] = {}
    data = payload.model_dump(exclude_unset=True, exclude={"expected_version"})
    if "assignee_id" in data:
        ensure_user(db, data["assignee_id"])
    if "parent_issue_id" in data:
        validate_parent(db, issue.issue_type, data["parent_issue_id"], issue.project_id)

    for field, new_value in data.items():
        old_value = getattr(issue, field)
        if old_value != new_value:
            setattr(issue, field, new_value)
            changes[field] = {"from": old_value, "to": new_value}

    if not changes:
        return issue, None

    issue.version += 1
    activity = log_activity(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=actor_id,
        event_type="issue_updated",
        payload={"issue_id": issue.id, "issue_key": issue.issue_key, "changes": changes, "version": issue.version},
    )
    notify_issue_watchers(db, issue=issue, message=f"{issue.issue_key} was updated", skip_user_ids={actor_id})
    if "assignee_id" in changes and issue.assignee_id:
        create_notification(
            db,
            user_id=issue.assignee_id,
            notification_type=NotificationType.ASSIGNMENT,
            message=f"You were assigned {issue.issue_key}",
            issue_id=issue.id,
        )
    db.commit()
    db.refresh(issue)
    return issue, activity


def watch_issue(db: Session, *, issue: Issue, user_id: int) -> Watcher:
    watcher = db.scalar(select(Watcher).where(Watcher.issue_id == issue.id, Watcher.user_id == user_id))
    if watcher:
        return watcher
    watcher = Watcher(issue_id=issue.id, user_id=user_id)
    db.add(watcher)
    log_activity(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=user_id,
        event_type="watcher_added",
        payload={"issue_id": issue.id, "user_id": user_id},
    )
    db.commit()
    db.refresh(watcher)
    return watcher


def unwatch_issue(db: Session, *, issue: Issue, user_id: int) -> None:
    watcher = db.scalar(select(Watcher).where(Watcher.issue_id == issue.id, Watcher.user_id == user_id))
    if watcher:
        db.delete(watcher)
        log_activity(
            db,
            project_id=issue.project_id,
            issue_id=issue.id,
            actor_id=user_id,
            event_type="watcher_removed",
            payload={"issue_id": issue.id, "user_id": user_id},
        )
        db.commit()


def allowed_parent_types() -> Iterable[str]:
    return VALID_PARENT_TYPES.keys()
