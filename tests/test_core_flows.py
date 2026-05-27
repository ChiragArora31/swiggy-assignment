from sqlalchemy import select

from app.models import Notification, Sprint


def test_valid_workflow_transition(client, auth_headers):
    response = client.post(
        "/api/issues/1/transitions",
        json={"target_status_name": "In Progress", "expected_version": 1},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"]["name"] == "In Progress"
    assert body["version"] == 2


def test_invalid_workflow_transition_returns_422(client, auth_headers):
    response = client.post(
        "/api/issues/1/transitions",
        json={"target_status_name": "Done"},
        headers=auth_headers,
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Invalid transition" in detail["message"]
    assert detail["allowed_transitions"] == [{"id": 2, "name": "In Progress"}]


def test_optimistic_locking_conflict_returns_409(client, auth_headers):
    first = client.patch("/api/issues/1", json={"expected_version": 1, "title": "OAuth login v2"}, headers=auth_headers)
    assert first.status_code == 200

    stale = client.patch("/api/issues/1", json={"expected_version": 1, "priority": "critical"}, headers=auth_headers)

    assert stale.status_code == 409
    assert stale.json()["detail"]["message"] == "Issue version conflict"
    assert stale.json()["detail"]["current_issue"]["version"] == 2


def test_sprint_completion_velocity_and_carry_over(client, auth_headers, db_session):
    response = client.post(
        "/api/sprints/1/complete",
        json={"carry_over_issue_ids": [1], "new_sprint_id": 2},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["velocity"] == 3
    assert body["incomplete_issue_ids"] == [1]
    assert body["carried_over_issue_ids"] == [1]
    assert db_session.get(Sprint, 1).state == "completed"


def test_comment_mention_creates_notification(client, auth_headers, db_session):
    response = client.post(
        "/api/issues/1/comments",
        json={"body": "@bob can you check this search edge case?"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    notification = db_session.scalar(select(Notification).where(Notification.user_id == 2))
    assert notification is not None
    assert notification.type == "mention"
    assert "TST-1" in notification.message


def test_comment_update_and_delete(client, auth_headers):
    created = client.post(
        "/api/issues/1/comments",
        json={"body": "Initial review note"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]

    updated = client.patch(
        f"/api/issues/1/comments/{comment_id}",
        json={"body": "Updated review note"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["body"] == "Updated review note"

    deleted = client.delete(f"/api/issues/1/comments/{comment_id}", headers=auth_headers)
    assert deleted.status_code == 204

    comments = client.get("/api/issues/1/comments", headers=auth_headers)
    assert all(comment["id"] != comment_id for comment in comments.json())


def test_custom_field_definition_and_value(client, auth_headers):
    definition = client.post(
        "/api/projects/1/custom-fields",
        json={"key": "risk", "name": "Risk", "field_type": "dropdown", "options": ["low", "medium", "high"]},
        headers=auth_headers,
    )
    assert definition.status_code == 201
    field_id = definition.json()["id"]

    value = client.put(
        f"/api/issues/1/custom-fields/{field_id}",
        json={"value": "high"},
        headers=auth_headers,
    )
    assert value.status_code == 200
    assert value.json()["key"] == "risk"
    assert value.json()["value"] == "high"

    invalid = client.put(
        f"/api/issues/1/custom-fields/{field_id}",
        json={"value": "urgent"},
        headers=auth_headers,
    )
    assert invalid.status_code == 422


def test_search_and_structured_filters(client, auth_headers):
    response = client.get(
        "/api/search",
        params={"q": "OAuth", "project_id": 1, "priority": "high", "issue_type": "story"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["issue_key"] == "TST-1"


def test_demo_page_and_supporting_endpoints(client, auth_headers):
    demo = client.get("/demo")
    users = client.get("/api/users", headers=auth_headers)
    notifications = client.get("/api/notifications", headers=auth_headers)

    assert demo.status_code == 200
    assert "Project Management Platform" in demo.text
    assert users.status_code == 200
    assert len(users.json()) == 2
    assert notifications.status_code == 200
