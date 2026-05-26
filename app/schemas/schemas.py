from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    username: str


class WorkflowStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    position: int
    is_done: bool


class SprintCreate(BaseModel):
    name: str
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class SprintUpdate(BaseModel):
    name: str | None = None
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class SprintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    goal: str | None
    start_date: date | None
    end_date: date | None
    state: str
    velocity: int
    created_at: datetime
    updated_at: datetime


class IssueCreate(BaseModel):
    issue_type: str = Field(pattern="^(epic|story|task|bug|sub_task)$")
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    assignee_id: int | None = None
    reporter_id: int | None = None
    sprint_id: int | None = None
    parent_issue_id: int | None = None
    story_points: int | None = Field(default=None, ge=0)
    labels: list[str] = Field(default_factory=list)


class IssuePatch(BaseModel):
    expected_version: int
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    assignee_id: int | None = None
    sprint_id: int | None = None
    parent_issue_id: int | None = None
    story_points: int | None = Field(default=None, ge=0)
    labels: list[str] | None = None


class IssueTransitionRequest(BaseModel):
    target_status_id: int | None = None
    target_status_name: str | None = None
    expected_version: int | None = None


class IssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    issue_number: int
    issue_key: str
    issue_type: str
    title: str
    description: str | None
    status: WorkflowStatusRead
    priority: str
    assignee: UserRead | None
    reporter: UserRead
    sprint_id: int | None
    parent_issue_id: int | None
    story_points: int | None
    labels: list[str]
    version: int
    created_at: datetime
    updated_at: datetime


class BoardColumn(BaseModel):
    status: WorkflowStatusRead
    issues: list[IssueRead]


class BoardRead(BaseModel):
    project_id: int
    columns: list[BoardColumn]
    active_viewers: list[int]


class SprintCompleteRequest(BaseModel):
    carry_over_issue_ids: list[int] = Field(default_factory=list)
    new_sprint_id: int | None = None


class SprintCompleteResponse(BaseModel):
    sprint: SprintRead
    velocity: int
    incomplete_issue_ids: list[int]
    carried_over_issue_ids: list[int]


class MoveIssueRequest(BaseModel):
    issue_ids: list[int]
    sprint_id: int | None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
    parent_comment_id: int | None = None


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    author: UserRead
    parent_comment_id: int | None
    body: str
    created_at: datetime
    updated_at: datetime


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    issue_id: int | None
    actor_id: int | None
    event_type: str
    payload: dict[str, Any]
    created_at: datetime


class Page(BaseModel):
    items: list[Any]
    next_cursor: int | None = None


class WatcherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    user: UserRead


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    issue_id: int | None
    type: str
    message: str
    read_at: datetime | None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
