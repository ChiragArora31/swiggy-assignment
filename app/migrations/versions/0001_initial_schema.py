"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_workspace_id", "users", ["workspace_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("key", sa.String(length=16), nullable=False, unique=True),
        sa.Column("next_issue_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])
    op.create_index("ix_projects_key", "projects", ["key"])

    op.create_table(
        "workflow_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "name", name="uq_workflow_status_project_name"),
    )
    op.create_index("ix_workflow_statuses_project_id", "workflow_statuses", ["project_id"])

    op.create_table(
        "workflow_transitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status_id", sa.Integer(), sa.ForeignKey("workflow_statuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_status_id", sa.Integer(), sa.ForeignKey("workflow_statuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "from_status_id", "to_status_id", name="uq_workflow_transition_pair"),
    )
    op.create_index("ix_workflow_transitions_project_id", "workflow_transitions", ["project_id"])
    op.create_index("ix_workflow_transitions_from_status_id", "workflow_transitions", ["from_status_id"])
    op.create_index("ix_workflow_transitions_to_status_id", "workflow_transitions", ["to_status_id"])

    op.create_table(
        "sprints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("goal", sa.Text()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("velocity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "name", name="uq_sprint_project_name"),
    )
    op.create_index("ix_sprints_project_id", "sprints", ["project_id"])
    op.create_index("ix_sprints_state", "sprints", ["state"])

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_number", sa.Integer(), nullable=False),
        sa.Column("issue_key", sa.String(length=40), nullable=False),
        sa.Column("issue_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status_id", sa.Integer(), sa.ForeignKey("workflow_statuses.id"), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("assignee_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sprint_id", sa.Integer(), sa.ForeignKey("sprints.id")),
        sa.Column("parent_issue_id", sa.Integer(), sa.ForeignKey("issues.id")),
        sa.Column("story_points", sa.Integer()),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("story_points IS NULL OR story_points >= 0", name="ck_issue_story_points_non_negative"),
        sa.UniqueConstraint("project_id", "issue_number", name="uq_issue_project_number"),
        sa.UniqueConstraint("project_id", "issue_key", name="uq_issue_project_key"),
    )
    for name, cols in {
        "ix_issues_project_id": ["project_id"],
        "ix_issues_issue_key": ["issue_key"],
        "ix_issues_status_id": ["status_id"],
        "ix_issues_assignee_id": ["assignee_id"],
        "ix_issues_reporter_id": ["reporter_id"],
        "ix_issues_sprint_id": ["sprint_id"],
        "ix_issues_parent_issue_id": ["parent_issue_id"],
        "ix_issues_project_status": ["project_id", "status_id"],
        "ix_issues_project_assignee": ["project_id", "assignee_id"],
        "ix_issues_project_sprint": ["project_id", "sprint_id"],
        "ix_issues_project_priority": ["project_id", "priority"],
        "ix_issues_project_type": ["project_id", "issue_type"],
    }.items():
        op.create_index(name, "issues", cols)

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("parent_comment_id", sa.Integer(), sa.ForeignKey("comments.id")),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_comments_issue_id", "comments", ["issue_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])
    op.create_index("ix_comments_parent_comment_id", "comments", ["parent_comment_id"])
    op.create_index("ix_comments_issue_created", "comments", ["issue_id", "created_at"])

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="SET NULL")),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activity_logs_project_id", "activity_logs", ["project_id"])
    op.create_index("ix_activity_logs_issue_id", "activity_logs", ["issue_id"])
    op.create_index("ix_activity_logs_actor_id", "activity_logs", ["actor_id"])
    op.create_index("ix_activity_logs_event_type", "activity_logs", ["event_type"])
    op.create_index("ix_activity_project_id_id", "activity_logs", ["project_id", "id"])
    op.create_index("ix_activity_project_event", "activity_logs", ["project_id", "event_type"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE")),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_issue_id", "notifications", ["issue_id"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read_at"])

    op.create_table(
        "watchers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("issue_id", "user_id", name="uq_watcher_issue_user"),
    )
    op.create_index("ix_watchers_issue_id", "watchers", ["issue_id"])
    op.create_index("ix_watchers_user_id", "watchers", ["user_id"])

    op.create_table(
        "custom_field_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("field_type", sa.String(length=40), nullable=False),
        sa.Column("options", sa.JSON()),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "key", name="uq_custom_field_project_key"),
    )
    op.create_index("ix_custom_field_definitions_project_id", "custom_field_definitions", ["project_id"])

    op.create_table(
        "custom_field_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_definition_id", sa.Integer(), sa.ForeignKey("custom_field_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("issue_id", "field_definition_id", name="uq_custom_field_issue_field"),
    )
    op.create_index("ix_custom_field_values_issue_id", "custom_field_values", ["issue_id"])
    op.create_index("ix_custom_field_values_field_definition_id", "custom_field_values", ["field_definition_id"])


def downgrade() -> None:
    for table in [
        "custom_field_values",
        "custom_field_definitions",
        "watchers",
        "notifications",
        "activity_logs",
        "comments",
        "issues",
        "sprints",
        "workflow_transitions",
        "workflow_statuses",
        "projects",
        "users",
        "workspaces",
    ]:
        op.drop_table(table)
