from __future__ import annotations

import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Comment, Issue, User
from app.repositories.activity import log_activity
from app.schemas import CommentCreate
from app.services.notifications import notify_mentions, notify_issue_watchers

MENTION_RE = re.compile(r"@([a-zA-Z0-9_.-]+)")


def mentioned_users(db: Session, body: str, workspace_id: int) -> list[User]:
    usernames = set(MENTION_RE.findall(body))
    if not usernames:
        return []
    return list(db.scalars(select(User).where(User.workspace_id == workspace_id, User.username.in_(usernames))))


def create_comment(db: Session, *, issue: Issue, payload: CommentCreate, actor_id: int) -> tuple[Comment, object]:
    if payload.parent_comment_id is not None:
        parent = db.get(Comment, payload.parent_comment_id)
        if not parent or parent.issue_id != issue.id:
            raise HTTPException(status_code=422, detail="Parent comment must belong to the same issue")

    comment = Comment(
        issue_id=issue.id,
        author_id=actor_id,
        parent_comment_id=payload.parent_comment_id,
        body=payload.body,
    )
    db.add(comment)
    db.flush()

    users = mentioned_users(db, payload.body, issue.project.workspace_id)
    notify_mentions(db, users=users, issue=issue, actor_id=actor_id)
    notify_issue_watchers(db, issue=issue, message=f"New comment on {issue.issue_key}", skip_user_ids={actor_id})

    activity = log_activity(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=actor_id,
        event_type="comment_added",
        payload={"issue_id": issue.id, "comment_id": comment.id, "mentions": [user.username for user in users]},
    )
    db.commit()
    db.refresh(comment)
    return comment, activity
