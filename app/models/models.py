from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IssueType(str, Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    BUG = "bug"
    SUB_TASK = "sub_task"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SprintState(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


class NotificationType(str, Enum):
    MENTION = "mention"
    ASSIGNMENT = "assignment"
    STATUS_CHANGE = "status_change"
    WATCHED_ISSUE = "watched_issue"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)

    projects: Mapped[list["Project"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="users")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    key: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    next_issue_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="projects")
    issues: Mapped[list["Issue"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    sprints: Mapped[list["Sprint"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    statuses: Mapped[list["WorkflowStatus"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class WorkflowStatus(TimestampMixin, Base):
    __tablename__ = "workflow_statuses"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_workflow_status_project_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="todo")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped[Project] = relationship(back_populates="statuses")


class WorkflowTransition(TimestampMixin, Base):
    __tablename__ = "workflow_transitions"
    __table_args__ = (
        UniqueConstraint("project_id", "from_status_id", "to_status_id", name="uq_workflow_transition_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    from_status_id: Mapped[int] = mapped_column(ForeignKey("workflow_statuses.id", ondelete="CASCADE"), index=True)
    to_status_id: Mapped[int] = mapped_column(ForeignKey("workflow_statuses.id", ondelete="CASCADE"), index=True)

    from_status: Mapped[WorkflowStatus] = relationship(foreign_keys=[from_status_id])
    to_status: Mapped[WorkflowStatus] = relationship(foreign_keys=[to_status_id])


class Sprint(TimestampMixin, Base):
    __tablename__ = "sprints"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_sprint_project_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    state: Mapped[str] = mapped_column(String(32), default=SprintState.PLANNED.value, nullable=False, index=True)
    velocity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    project: Mapped[Project] = relationship(back_populates="sprints")
    issues: Mapped[list["Issue"]] = relationship(back_populates="sprint")


class Issue(TimestampMixin, Base):
    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("project_id", "issue_number", name="uq_issue_project_number"),
        UniqueConstraint("project_id", "issue_key", name="uq_issue_project_key"),
        CheckConstraint("story_points IS NULL OR story_points >= 0", name="ck_issue_story_points_non_negative"),
        Index("ix_issues_project_status", "project_id", "status_id"),
        Index("ix_issues_project_assignee", "project_id", "assignee_id"),
        Index("ix_issues_project_sprint", "project_id", "sprint_id"),
        Index("ix_issues_project_priority", "project_id", "priority"),
        Index("ix_issues_project_type", "project_id", "issue_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_key: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    issue_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status_id: Mapped[int] = mapped_column(ForeignKey("workflow_statuses.id"), index=True)
    priority: Mapped[str] = mapped_column(String(32), default=Priority.MEDIUM.value, nullable=False, index=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sprint_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sprints.id"), index=True)
    parent_issue_id: Mapped[Optional[int]] = mapped_column(ForeignKey("issues.id"), index=True)
    story_points: Mapped[Optional[int]] = mapped_column(Integer)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project: Mapped[Project] = relationship(back_populates="issues")
    status: Mapped[WorkflowStatus] = relationship()
    assignee: Mapped[Optional[User]] = relationship(foreign_keys=[assignee_id])
    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])
    sprint: Mapped[Optional[Sprint]] = relationship(back_populates="issues")
    parent: Mapped[Optional["Issue"]] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["Issue"]] = relationship(back_populates="parent")
    comments: Mapped[list["Comment"]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    watchers: Mapped[list["Watcher"]] = relationship(back_populates="issue", cascade="all, delete-orphan")


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_issue_created", "issue_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    parent_comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"), index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="comments")
    author: Mapped[User] = relationship()
    parent: Mapped[Optional["Comment"]] = relationship(remote_side=[id], back_populates="replies")
    replies: Mapped[list["Comment"]] = relationship(back_populates="parent")


class ActivityLog(TimestampMixin, Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_project_id_id", "project_id", "id"),
        Index("ix_activity_project_event", "project_id", "event_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    issue_id: Mapped[Optional[int]] = mapped_column(ForeignKey("issues.id", ondelete="SET NULL"), index=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    project: Mapped[Project] = relationship()
    issue: Mapped[Optional[Issue]] = relationship()
    actor: Mapped[Optional[User]] = relationship()


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read", "user_id", "read_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    issue_id: Mapped[Optional[int]] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()
    issue: Mapped[Optional[Issue]] = relationship()


class Watcher(TimestampMixin, Base):
    __tablename__ = "watchers"
    __table_args__ = (UniqueConstraint("issue_id", "user_id", name="uq_watcher_issue_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    issue: Mapped[Issue] = relationship(back_populates="watchers")
    user: Mapped[User] = relationship()


class CustomFieldDefinition(TimestampMixin, Base):
    __tablename__ = "custom_field_definitions"
    __table_args__ = (UniqueConstraint("project_id", "key", name="uq_custom_field_project_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    field_type: Mapped[str] = mapped_column(String(40), nullable=False)
    options: Mapped[Optional[list[str]]] = mapped_column(JSON)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped[Project] = relationship()


class CustomFieldValue(TimestampMixin, Base):
    __tablename__ = "custom_field_values"
    __table_args__ = (UniqueConstraint("issue_id", "field_definition_id", name="uq_custom_field_issue_field"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    field_definition_id: Mapped[int] = mapped_column(
        ForeignKey("custom_field_definitions.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    issue: Mapped[Issue] = relationship()
    field_definition: Mapped[CustomFieldDefinition] = relationship()
