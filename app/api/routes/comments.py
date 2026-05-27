from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Comment, Issue, User
from app.repositories.issues import get_issue
from app.schemas import CommentCreate, CommentRead, CommentUpdate
from app.services.comments import create_comment, delete_comment, update_comment
from app.websocket.manager import manager

router = APIRouter(prefix="/issues/{issue_id}/comments", tags=["comments"])


def issue_or_404(db: Session, issue_id: int) -> Issue:
    issue = get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


def comment_or_404(db: Session, issue_id: int, comment_id: int) -> Comment:
    comment = db.scalar(
        select(Comment)
        .options(joinedload(Comment.issue), joinedload(Comment.author))
        .where(Comment.id == comment_id, Comment.issue_id == issue_id)
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.get("", response_model=list[CommentRead])
def list_comments(
    issue_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CommentRead]:
    issue_or_404(db, issue_id)
    comments = list(
        db.scalars(
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.issue_id == issue_id)
            .order_by(Comment.parent_comment_id.nullsfirst(), Comment.created_at.asc(), Comment.id.asc())
        )
    )
    return [CommentRead.model_validate(comment) for comment in comments]


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    issue_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentRead:
    comment, activity = create_comment(db, issue=issue_or_404(db, issue_id), payload=payload, actor_id=current_user.id)
    await manager.broadcast_project(comment.issue.project_id, "comment_added", activity.payload, activity.id)
    return CommentRead.model_validate(comment)


@router.patch("/{comment_id}", response_model=CommentRead)
async def edit_comment(
    issue_id: int,
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentRead:
    comment = comment_or_404(db, issue_id, comment_id)
    comment, activity = update_comment(db, comment=comment, payload=payload, actor_id=current_user.id)
    await manager.broadcast_project(comment.issue.project_id, "comment_updated", activity.payload, activity.id)
    return CommentRead.model_validate(comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment(
    issue_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    comment = comment_or_404(db, issue_id, comment_id)
    project_id = comment.issue.project_id
    activity = delete_comment(db, comment=comment, actor_id=current_user.id)
    await manager.broadcast_project(project_id, "comment_deleted", activity.payload, activity.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
