# Jira-like Project Management Backend

Production-minded SDE-1 backend take-home implementation for a Jira-like project management platform. The code favors clear domain boundaries, normalized relational storage, auditable mutations, and a demo flow that can be explained in 5-10 minutes.

The project also includes a small built-in demo UI at `/demo`. It is intentionally not a separate frontend app; it exists to make the backend behavior easy to show during a review.

Hosted prototype: https://swiggy-assignment-dun.vercel.app/demo

## Tech Stack

- FastAPI with Swagger/OpenAPI at `/docs`
- PostgreSQL via SQLAlchemy 2.x
- Alembic migrations
- Pydantic request/response schemas
- Docker + docker-compose
- FastAPI WebSockets
- Seeded-user auth with optional JWT token endpoint
- Pytest coverage for core backend behavior
- Built-in HTML/CSS/JS demo page served by FastAPI

## Architecture

```text
Client / Demo UI / Swagger / WebSocket
        |
        v
app/api/routes/          HTTP route adapters and dependency wiring
        |
        v
app/services/            Business rules: workflow, sprint, comments, issues
        |
        v
app/repositories/        Query helpers and activity log access
        |
        v
app/models/              SQLAlchemy 2.x ORM models
        |
        v
PostgreSQL               Normalized relational schema + indexes

app/websocket/manager.py Broadcasts project-board events and tracks presence
app/core/                Config, DB session, auth/security
```

## Quick Start

```bash
docker-compose up --build
```

The API will be available at:

- Demo UI: http://localhost:8000/demo
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health
- WebSocket: `ws://localhost:8000/ws/projects/1/board?user_id=1`

Seeded users can authenticate either by passing `X-User-Id: 1` through `X-User-Id: 5`, or by getting a token:

```bash
curl -X POST http://localhost:8000/api/auth/token/alice
```

Then use `Authorization: Bearer <token>`.

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./local.db
export AUTO_CREATE_TABLES=true
python -m app.seed
uvicorn app.main:app --reload
pytest
```

For PostgreSQL outside Docker:

```bash
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/jira_pm
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## API Surface

- `POST /api/projects/{project_id}/issues` creates an issue with project-scoped keys such as `PROJ-1`
- `GET /api/projects/{project_id}/board` returns issues grouped by workflow status
- `GET /api/projects/{project_id}/backlog` returns backlog issues
- `GET /api/projects/{project_id}/issues` lists issues with cursor pagination and filters
- `GET /api/issues/{issue_id}` returns issue detail
- `PATCH /api/issues/{issue_id}` updates issue fields with optimistic locking
- `POST /api/issues/{issue_id}/transitions` moves an issue through the configured workflow
- `GET /api/projects/{project_id}/sprints` lists sprints
- `POST /api/projects/{project_id}/sprints` creates a sprint
- `PATCH /api/sprints/{sprint_id}` updates sprint metadata
- `POST /api/sprints/{sprint_id}/start` starts a planned sprint
- `POST /api/sprints/{sprint_id}/complete` completes a sprint and optionally carries incomplete work forward
- `POST /api/projects/{project_id}/sprints/move-issues` moves issues between backlog and sprint
- `GET /api/issues/{issue_id}/comments` lists threaded comments
- `POST /api/issues/{issue_id}/comments` adds a comment and creates mention notifications
- `POST /api/issues/{issue_id}/watch` watches an issue
- `DELETE /api/issues/{issue_id}/watch` unwatches an issue
- `GET /api/projects/{project_id}/activity` returns a paginated activity feed
- `GET /api/search` searches titles, descriptions, and comments with structured filters
- `GET /api/users` lists seeded users for demo/client selection
- `GET /api/notifications` lists current-user notifications

## Demo UI

Open `/demo` after the app starts. The page is a compact board view backed by the same APIs used in Swagger.

It can demonstrate:

- board columns grouped by workflow status
- issue creation with generated `PROJ-N` keys
- valid workflow transitions
- invalid transition handling with `422`
- stale-version optimistic locking with `409`
- threaded comment creation with `@mention` notification generation
- watch issue
- search across issue and comment text with structured filters
- sprint completion, velocity, and carry-over
- activity feed updates
- notification feed for the selected demo user

The demo page attempts to connect to the project WebSocket endpoint when the host supports WebSockets. The REST flows still work if the deployment platform does not keep long-lived socket connections open.

## Database Schema Overview

Core tables:

- `workspaces`, `projects`, `users`
- `issues` with `issue_key`, `issue_type`, `status_id`, `priority`, `assignee_id`, `reporter_id`, `sprint_id`, `parent_issue_id`, `story_points`, `labels`, `version`
- `sprints` with `planned`, `active`, and `completed` states plus computed `velocity`
- `workflow_statuses` and `workflow_transitions`
- `comments` with `parent_comment_id` for threading
- `activity_logs` for audit trail and WebSocket missed-event replay
- `notifications`
- `watchers`
- `custom_field_definitions` and `custom_field_values`

Important constraints and indexes:

- `projects.key` is unique
- `issues(project_id, issue_number)` and `issues(project_id, issue_key)` are unique
- issue filters have composite indexes by project plus status, assignee, sprint, priority, and type
- activity feed has indexes on `(project_id, id)` and `(project_id, event_type)`
- watcher and custom-field uniqueness are enforced in the database

## Workflow Engine

Workflow statuses are configured per project. The seed data creates:

```text
To Do -> In Progress -> In Review -> Done
                 ^          |
                 |----------|
```

Transitions are stored in `workflow_transitions`. `POST /api/issues/{id}/transitions` validates the current status against allowed targets. Invalid transitions return HTTP `422` with the allowed transitions.

Validation hooks implemented:

- An issue must have an assignee before moving to `In Progress`
- `story`, `task`, and `bug` issues must have `story_points` before moving to a done status

Automatic action implemented:

- Moving to `In Review` notifies the assignee and watchers, excluding the actor

## Sprint Completion

`POST /api/sprints/{id}/complete`:

- Requires the sprint to be active
- Calculates velocity as completed story points in done statuses
- Returns incomplete issue IDs
- Moves selected incomplete issues to `new_sprint_id`
- Moves the remaining incomplete issues back to backlog
- Writes a `sprint_updated` activity log event

## WebSocket Events

Subscribe to a project board:

```text
ws://localhost:8000/ws/projects/1/board?user_id=1&last_event_id=42
```

Event format:

```json
{
  "event_id": 43,
  "event_type": "issue_moved",
  "payload": {
    "issue_id": 1,
    "issue_key": "PROJ-1",
    "from_status": "In Progress",
    "to_status": "In Review",
    "version": 3
  }
}
```

Broadcast event types:

- `issue_created`
- `issue_updated`
- `issue_moved`
- `comment_added`
- `sprint_updated`
- `presence_updated`

Missed replay:

- Clients pass `last_event_id`
- The server replays newer `activity_logs` before waiting for live messages

Presence:

- Connected board viewers are tracked in memory by project
- `GET /api/projects/{project_id}/board` includes `active_viewers`

## Search and Filtering

`GET /api/search` supports:

- `q` across issue title, issue description, and comment body
- `project_id`
- `status_id`
- `assignee_id`
- `priority`
- `issue_type`
- `sprint_id`
- `cursor` and `limit`

The implementation uses a clean `ILIKE` fallback that works in tests and locally. In production PostgreSQL, I would add generated `tsvector` columns or expression GIN indexes for issue and comment text.

## Concurrency Strategy

Issues have a `version` column. Every `PATCH /api/issues/{id}` must include `expected_version`.

If the version does not match, the API returns `409 Conflict` with the current issue state. This prevents silent overwrites when two users edit the same issue from stale data. The client can merge the user’s intended change onto the latest issue and retry with the new version.

Transitions can also pass `expected_version`, which applies the same conflict check.

## Requirement Checklist

| Requirement | Status | Where |
| --- | --- | --- |
| FastAPI backend | Implemented | `app/main.py`, `app/api/routes/` |
| PostgreSQL + SQLAlchemy 2.x | Implemented | `app/core/database.py`, `app/models/models.py` |
| Alembic migrations | Implemented | `app/migrations/versions/0001_initial_schema.py` |
| Docker + docker-compose | Implemented | `Dockerfile`, `docker-compose.yml` |
| Pydantic schemas | Implemented | `app/schemas/schemas.py` |
| Swagger/OpenAPI | Implemented | `/docs` |
| Hosted/demo UI | Implemented | `/demo`, `app/demo.py` |
| Seeded-user/JWT auth | Implemented | `app/core/security.py`, `app/api/routes/auth.py` |
| Workspace, Project, User | Implemented | `app/models/models.py` |
| Issue, Sprint, Comment | Implemented | `app/models/models.py` |
| ActivityLog, Notification, Watcher | Implemented | `app/models/models.py` |
| WorkflowStatus, WorkflowTransition | Implemented | `app/models/models.py`, `app/services/workflow.py` |
| Custom fields | Implemented schema | `CustomFieldDefinition`, `CustomFieldValue` |
| Epic/story/task/bug/sub-task types | Implemented | `Issue.issue_type`, parent validation |
| Parent-child validation | Implemented | `app/services/issues.py` |
| Project-scoped issue keys | Implemented | `create_issue`, `Project.next_issue_number` |
| Labels, story points, timestamps | Implemented | `Issue` model |
| Optimistic locking | Implemented | `Issue.version`, `PATCH /api/issues/{id}` |
| Audit trail for mutations | Implemented | `activity_logs`, service calls |
| Configurable workflow per project | Implemented | status/transition tables |
| Invalid transition returns 422 | Implemented and tested | `tests/test_core_flows.py` |
| Assignee required for In Progress | Implemented | workflow hook |
| Story points required for Done | Implemented | workflow hook |
| In Review notifications | Implemented | workflow service |
| Sprint CRUD/start/complete | Implemented | `app/api/routes/sprints.py` |
| Move issues between backlog/sprint | Implemented | `move-issues` endpoint |
| Sprint velocity | Implemented and tested | sprint service/test |
| Threaded comments | Implemented | `Comment.parent_comment_id` |
| @mention notifications | Implemented and tested | comment service/test |
| Notification endpoint | Implemented | `GET /api/notifications` |
| Watch/unwatch | Implemented | issue routes |
| Activity feed with pagination/filtering | Implemented | activity route/repository |
| WebSocket board subscription | Implemented | `app/main.py`, `app/websocket/manager.py` |
| WebSocket event broadcast | Implemented | route service calls |
| Presence tracking | Implemented | connection manager |
| Missed event replay | Implemented | `last_event_id` query param |
| Search title/description/comments | Implemented and tested | search repository/test |
| Structured filters | Implemented and tested | list/search endpoints |
| Cursor pagination | Implemented | issue/search/activity repositories |
| Demo UI smoke coverage | Implemented | `tests/test_core_flows.py` |
| Tests | Implemented | `tests/` |

## Trade-offs

- Auth is intentionally simple: seeded users via `X-User-Id` and an optional JWT endpoint. This keeps focus on the project-management backend.
- WebSocket presence is in memory. For multiple API instances, I would move presence and broadcasts to Redis Pub/Sub.
- The Vercel hosted demo uses the same FastAPI app and seeds itself on startup. The Docker path remains the PostgreSQL-backed setup intended for local production-style review.
- Search uses `ILIKE` for portability. Production PostgreSQL should use `tsvector` and GIN indexes.
- Custom fields are modeled and migratable, but only seeded lightly. A fuller version would add CRUD and type-specific validation.
- Issue key allocation increments on the project row. At higher write concurrency, I would use row-level locking or a dedicated counter table/sequence per project.
- The API is synchronous SQLAlchemy for readability. Async SQLAlchemy is possible, but not necessary for this take-home.

## What I Would Improve With More Time

- Add role-based authorization by workspace/project membership
- Add custom-field CRUD and strict value validation
- Add API-level tests for WebSocket replay
- Add PostgreSQL full-text indexes and query ranking
- Add background notification delivery and read/unread APIs
- Add OpenTelemetry traces and structured request logs
- Add CI with linting, tests, migration check, and Docker build

## Demo Script

1. Open `/demo`
2. Create an issue and show the generated key `PROJ-N`
3. Select the issue and move it through a valid workflow transition
4. Click the invalid transition action and show the `422` response
5. Click the stale patch action and show the `409 Conflict`
6. Add a comment containing `@bob`, then switch to Bob and show the notification
7. Search/filter issues from the toolbar
8. Complete the active sprint and show velocity plus carry-over behavior
9. Open `/docs` for the full API surface and schemas
