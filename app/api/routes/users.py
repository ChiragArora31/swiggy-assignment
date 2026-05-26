from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Notification, User
from app.schemas import NotificationRead, UserRead

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[UserRead]:
    users = list(db.scalars(select(User).order_by(User.id.asc())))
    return [UserRead.model_validate(user) for user in users]


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationRead]:
    notifications = list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(20)
        )
    )
    return [NotificationRead.model_validate(notification) for notification in notifications]
