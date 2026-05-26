from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models import (
    ActivityLog,
    Comment,
    CustomFieldDefinition,
    Issue,
    Project,
    Sprint,
    User,
    Watcher,
    WorkflowStatus,
    WorkflowTransition,
    Workspace,
)


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(Project).where(Project.key == "PROJ")):
            print("Seed data already exists")
            return

        workspace = Workspace(name="Acme Engineering")
        db.add(workspace)
        db.flush()

        users = [
            User(workspace_id=workspace.id, email="alice@example.com", username="alice", display_name="Alice Sharma"),
            User(workspace_id=workspace.id, email="bob@example.com", username="bob", display_name="Bob Chen"),
            User(workspace_id=workspace.id, email="carol@example.com", username="carol", display_name="Carol Mehta"),
            User(workspace_id=workspace.id, email="dinesh@example.com", username="dinesh", display_name="Dinesh Rao"),
            User(workspace_id=workspace.id, email="emma@example.com", username="emma", display_name="Emma Singh"),
        ]
        db.add_all(users)
        db.flush()

        project = Project(workspace_id=workspace.id, name="Platform Backend", key="PROJ")
        db.add(project)
        db.flush()

        statuses = [
            WorkflowStatus(project_id=project.id, name="To Do", category="todo", position=1),
            WorkflowStatus(project_id=project.id, name="In Progress", category="in_progress", position=2),
            WorkflowStatus(project_id=project.id, name="In Review", category="review", position=3),
            WorkflowStatus(project_id=project.id, name="Done", category="done", position=4, is_done=True),
        ]
        db.add_all(statuses)
        db.flush()
        by_name = {status.name: status for status in statuses}
        db.add_all(
            [
                WorkflowTransition(project_id=project.id, from_status_id=by_name["To Do"].id, to_status_id=by_name["In Progress"].id),
                WorkflowTransition(project_id=project.id, from_status_id=by_name["In Progress"].id, to_status_id=by_name["In Review"].id),
                WorkflowTransition(project_id=project.id, from_status_id=by_name["In Review"].id, to_status_id=by_name["Done"].id),
                WorkflowTransition(project_id=project.id, from_status_id=by_name["In Review"].id, to_status_id=by_name["In Progress"].id),
            ]
        )

        today = date.today()
        sprint_1 = Sprint(
            project_id=project.id,
            name="Sprint 1",
            goal="Workflow and issue tracking MVP",
            start_date=today - timedelta(days=7),
            end_date=today + timedelta(days=7),
            state="active",
        )
        sprint_2 = Sprint(
            project_id=project.id,
            name="Sprint 2",
            goal="Collaboration polish",
            start_date=today + timedelta(days=8),
            end_date=today + timedelta(days=21),
        )
        db.add_all([sprint_1, sprint_2])
        db.flush()

        project.next_issue_number = 1

        def make_issue(
            issue_type: str,
            title: str,
            *,
            description: str,
            status: str,
            priority: str = "medium",
            assignee: User | None = None,
            reporter: User | None = None,
            sprint: Sprint | None = None,
            parent: Issue | None = None,
            points: int | None = None,
            labels: list[str] | None = None,
        ) -> Issue:
            number = project.next_issue_number
            project.next_issue_number += 1
            issue = Issue(
                project_id=project.id,
                issue_number=number,
                issue_key=f"{project.key}-{number}",
                issue_type=issue_type,
                title=title,
                description=description,
                status_id=by_name[status].id,
                priority=priority,
                assignee_id=assignee.id if assignee else None,
                reporter_id=(reporter or users[0]).id,
                sprint_id=sprint.id if sprint else None,
                parent_issue_id=parent.id if parent else None,
                story_points=points,
                labels=labels or [],
            )
            db.add(issue)
            db.flush()
            db.add(
                ActivityLog(
                    project_id=project.id,
                    issue_id=issue.id,
                    actor_id=(reporter or users[0]).id,
                    event_type="issue_created",
                    payload={"issue_id": issue.id, "issue_key": issue.issue_key},
                )
            )
            return issue

        epic_auth = make_issue("epic", "Authentication platform", description="Foundation for secure account access.", status="In Progress", priority="high", assignee=users[0], sprint=sprint_1, labels=["auth"])
        story_oauth = make_issue("story", "Add OAuth login", description="Support OAuth 2.0 login for web clients.", status="In Review", priority="high", assignee=users[1], sprint=sprint_1, parent=epic_auth, points=5, labels=["auth", "backend"])
        task_jwt = make_issue("task", "Issue JWT access tokens", description="Create signed tokens for seeded users.", status="Done", priority="medium", assignee=users[2], sprint=sprint_1, parent=epic_auth, points=3, labels=["auth"])
        make_issue("bug", "Fix expired token handling", description="Expired tokens should return 401.", status="To Do", priority="high", assignee=users[3], sprint=sprint_1, parent=epic_auth, points=2, labels=["auth", "bug"])
        make_issue("sub_task", "Document token endpoint", description="Add Swagger examples.", status="Done", assignee=users[4], sprint=sprint_1, parent=task_jwt, labels=["docs"])

        epic_board = make_issue("epic", "Sprint board", description="Board, backlog, and sprint operations.", status="In Progress", priority="critical", assignee=users[0], sprint=sprint_1, labels=["board"])
        story_board = make_issue("story", "Render board columns", description="Return issues grouped by workflow status.", status="In Progress", priority="high", assignee=users[1], sprint=sprint_1, parent=epic_board, points=8, labels=["board"])
        story_carry = make_issue("story", "Carry over incomplete work", description="Complete sprint and move selected items.", status="To Do", priority="medium", assignee=users[2], sprint=sprint_1, parent=epic_board, points=5, labels=["sprint"])
        make_issue("task", "Add activity feed filters", description="Filter activity by issue and event type.", status="To Do", priority="medium", assignee=users[3], parent=epic_board, points=3, labels=["activity"])
        make_issue("sub_task", "Add board WebSocket smoke test", description="Verify event replay contract.", status="To Do", assignee=users[4], parent=story_board, labels=["realtime"])

        epic_collab = make_issue("epic", "Collaboration layer", description="Comments, watchers, mentions, notifications.", status="To Do", priority="medium", assignee=users[0], labels=["collaboration"])
        story_comments = make_issue("story", "Threaded comments", description="Support replies and @mentions.", status="To Do", priority="high", assignee=users[1], parent=epic_collab, points=3, labels=["comments"])
        make_issue("bug", "Search misses comment text", description="Search should include comment body.", status="In Progress", priority="medium", assignee=users[2], parent=epic_collab, points=2, labels=["search"])

        db.add_all(
            [
                Comment(issue_id=story_oauth.id, author_id=users[0].id, body="@bob please review the OAuth callback edge cases."),
                Comment(issue_id=story_comments.id, author_id=users[2].id, body="Threading is ready for API review."),
                Watcher(issue_id=story_oauth.id, user_id=users[0].id),
                Watcher(issue_id=story_oauth.id, user_id=users[2].id),
                Watcher(issue_id=story_board.id, user_id=users[3].id),
                CustomFieldDefinition(project_id=project.id, key="risk", name="Risk", field_type="dropdown", options=["low", "medium", "high"]),
            ]
        )
        db.commit()
        print("Seed data created: workspace=1 project=1 users=5 issues=13")


if __name__ == "__main__":
    seed()
