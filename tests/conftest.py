import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models import Issue, Project, Sprint, User, WorkflowStatus, WorkflowTransition, Workspace


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()

    workspace = Workspace(name="Test Workspace")
    session.add(workspace)
    session.flush()
    alice = User(workspace_id=workspace.id, email="alice@test.com", username="alice", display_name="Alice")
    bob = User(workspace_id=workspace.id, email="bob@test.com", username="bob", display_name="Bob")
    session.add_all([alice, bob])
    session.flush()
    project = Project(workspace_id=workspace.id, name="Test Project", key="TST", next_issue_number=1)
    session.add(project)
    session.flush()

    todo = WorkflowStatus(project_id=project.id, name="To Do", category="todo", position=1)
    progress = WorkflowStatus(project_id=project.id, name="In Progress", category="in_progress", position=2)
    review = WorkflowStatus(project_id=project.id, name="In Review", category="review", position=3)
    done = WorkflowStatus(project_id=project.id, name="Done", category="done", position=4, is_done=True)
    session.add_all([todo, progress, review, done])
    session.flush()
    session.add_all(
        [
            WorkflowTransition(project_id=project.id, from_status_id=todo.id, to_status_id=progress.id),
            WorkflowTransition(project_id=project.id, from_status_id=progress.id, to_status_id=review.id),
            WorkflowTransition(project_id=project.id, from_status_id=review.id, to_status_id=done.id),
        ]
    )
    sprint_1 = Sprint(project_id=project.id, name="Sprint 1", state="active")
    sprint_2 = Sprint(project_id=project.id, name="Sprint 2", state="planned")
    session.add_all([sprint_1, sprint_2])
    session.flush()

    issues = [
        Issue(
            project_id=project.id,
            issue_number=1,
            issue_key="TST-1",
            issue_type="story",
            title="OAuth login",
            description="OAuth backend flow",
            status_id=todo.id,
            priority="high",
            assignee_id=alice.id,
            reporter_id=alice.id,
            sprint_id=sprint_1.id,
            story_points=5,
            labels=["auth"],
        ),
        Issue(
            project_id=project.id,
            issue_number=2,
            issue_key="TST-2",
            issue_type="task",
            title="Done API task",
            description="Counts toward velocity",
            status_id=done.id,
            priority="medium",
            assignee_id=bob.id,
            reporter_id=alice.id,
            sprint_id=sprint_1.id,
            story_points=3,
            labels=["api"],
        ),
    ]
    project.next_issue_number = 3
    session.add_all(issues)
    session.commit()

    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers():
    return {"X-User-Id": "1"}
