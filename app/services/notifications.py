from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Issue, Notification, NotificationType, User


def create_notification(
    db: Session,
    *,
    user_id: int,
    notification_type: NotificationType | str,
    message: str,
    issue_id: int | None = None,
) -> Notification:
    type_value = notification_type.value if hasattr(notification_type, "value") else str(notification_type)
    notification = Notification(
        user_id=user_id,
        issue_id=issue_id,
        type=type_value,
        message=message,
    )
    db.add(notification)
    db.flush()
    return notification


def notify_issue_watchers(
    db: Session,
    *,
    issue: Issue,
    message: str,
    skip_user_ids: set[int] | None = None,
) -> None:
    skip_user_ids = skip_user_ids or set()
    for watcher in issue.watchers:
        if watcher.user_id not in skip_user_ids:
            create_notification(
                db,
                user_id=watcher.user_id,
                notification_type=NotificationType.WATCHED_ISSUE,
                message=message,
                issue_id=issue.id,
            )


def notify_mentions(db: Session, *, users: list[User], issue: Issue, actor_id: int) -> None:
    for user in users:
        if user.id == actor_id:
            continue
        create_notification(
            db,
            user_id=user.id,
            notification_type=NotificationType.MENTION,
            message=f"You were mentioned on {issue.issue_key}",
            issue_id=issue.id,
        )
