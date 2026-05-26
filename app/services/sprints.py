from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Issue, Sprint, SprintState, WorkflowStatus
from app.repositories.activity import log_activity


def create_sprint(db: Session, *, project_id: int, name: str, goal: str | None, start_date, end_date, actor_id: int) -> Sprint:
    sprint = Sprint(project_id=project_id, name=name, goal=goal, start_date=start_date, end_date=end_date)
    db.add(sprint)
    db.flush()
    log_activity(db, project_id=project_id, actor_id=actor_id, event_type="sprint_updated", payload={"sprint_id": sprint.id, "action": "created"})
    db.commit()
    db.refresh(sprint)
    return sprint


def start_sprint(db: Session, *, sprint: Sprint, actor_id: int) -> Sprint:
    if sprint.state != SprintState.PLANNED.value:
        raise HTTPException(status_code=422, detail="Only planned sprints can be started")
    active = db.scalar(select(Sprint).where(Sprint.project_id == sprint.project_id, Sprint.state == SprintState.ACTIVE.value))
    if active:
        raise HTTPException(status_code=422, detail=f"Sprint {active.id} is already active")
    sprint.state = SprintState.ACTIVE.value
    activity = log_activity(
        db,
        project_id=sprint.project_id,
        actor_id=actor_id,
        event_type="sprint_updated",
        payload={"sprint_id": sprint.id, "action": "started"},
    )
    db.commit()
    db.refresh(sprint)
    return sprint


def complete_sprint(
    db: Session,
    *,
    sprint: Sprint,
    carry_over_issue_ids: list[int],
    new_sprint_id: int | None,
    actor_id: int,
) -> tuple[Sprint, list[int], list[int], object]:
    if sprint.state != SprintState.ACTIVE.value:
        raise HTTPException(status_code=422, detail="Only active sprints can be completed")
    if carry_over_issue_ids and new_sprint_id is None:
        raise HTTPException(status_code=422, detail="new_sprint_id is required when carrying issues over")

    done_status_ids = set(
        db.scalars(select(WorkflowStatus.id).where(WorkflowStatus.project_id == sprint.project_id, WorkflowStatus.is_done.is_(True)))
    )
    issues = list(db.scalars(select(Issue).where(Issue.sprint_id == sprint.id)))
    incomplete = [issue for issue in issues if issue.status_id not in done_status_ids]
    completed = [issue for issue in issues if issue.status_id in done_status_ids]
    incomplete_ids = [issue.id for issue in incomplete]
    invalid_carry = sorted(set(carry_over_issue_ids) - set(incomplete_ids))
    if invalid_carry:
        raise HTTPException(status_code=422, detail={"message": "Only incomplete issues can be carried over", "invalid_issue_ids": invalid_carry})

    if new_sprint_id is not None:
        target = db.get(Sprint, new_sprint_id)
        if not target or target.project_id != sprint.project_id or target.state == SprintState.COMPLETED.value:
            raise HTTPException(status_code=422, detail="Carry-over sprint must exist in the same project and not be completed")
    carried = []
    for issue in incomplete:
        if issue.id in carry_over_issue_ids:
            issue.sprint_id = new_sprint_id
            issue.version += 1
            carried.append(issue.id)
            log_activity(
                db,
                project_id=sprint.project_id,
                issue_id=issue.id,
                actor_id=actor_id,
                event_type="issue_updated",
                payload={"issue_id": issue.id, "action": "carried_over", "sprint_id": new_sprint_id},
            )
        else:
            issue.sprint_id = None
            issue.version += 1
            log_activity(
                db,
                project_id=sprint.project_id,
                issue_id=issue.id,
                actor_id=actor_id,
                event_type="issue_updated",
                payload={"issue_id": issue.id, "action": "moved_to_backlog"},
            )

    sprint.velocity = sum(issue.story_points or 0 for issue in completed)
    sprint.state = SprintState.COMPLETED.value
    activity = log_activity(
        db,
        project_id=sprint.project_id,
        actor_id=actor_id,
        event_type="sprint_updated",
        payload={
            "sprint_id": sprint.id,
            "action": "completed",
            "velocity": sprint.velocity,
            "incomplete_issue_ids": incomplete_ids,
            "carried_over_issue_ids": carried,
        },
    )
    db.commit()
    db.refresh(sprint)
    return sprint, incomplete_ids, carried, activity


def move_issues(db: Session, *, project_id: int, issue_ids: list[int], sprint_id: int | None, actor_id: int) -> object:
    if sprint_id is not None:
        sprint = db.get(Sprint, sprint_id)
        if not sprint or sprint.project_id != project_id or sprint.state == SprintState.COMPLETED.value:
            raise HTTPException(status_code=422, detail="Sprint must exist in the same project and not be completed")

    issues = list(db.scalars(select(Issue).where(Issue.project_id == project_id, Issue.id.in_(issue_ids))))
    if len(issues) != len(set(issue_ids)):
        raise HTTPException(status_code=404, detail="One or more issues were not found")
    for issue in issues:
        issue.sprint_id = sprint_id
        issue.version += 1
    activity = log_activity(
        db,
        project_id=project_id,
        actor_id=actor_id,
        event_type="issue_updated",
        payload={"action": "move_issues", "issue_ids": issue_ids, "sprint_id": sprint_id},
    )
    db.commit()
    return activity
