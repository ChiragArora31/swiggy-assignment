from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import CustomFieldDefinition, CustomFieldValue, Issue, Project, User
from app.repositories.activity import log_activity
from app.repositories.issues import get_issue
from app.schemas import CustomFieldDefinitionCreate, CustomFieldDefinitionRead, CustomFieldValueRead, CustomFieldValueUpsert

router = APIRouter(tags=["custom-fields"])


def project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def issue_or_404(db: Session, issue_id: int) -> Issue:
    issue = get_issue(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


def definition_or_404(db: Session, project_id: int, field_definition_id: int) -> CustomFieldDefinition:
    definition = db.scalar(
        select(CustomFieldDefinition).where(
            CustomFieldDefinition.id == field_definition_id,
            CustomFieldDefinition.project_id == project_id,
        )
    )
    if not definition:
        raise HTTPException(status_code=404, detail="Custom field definition not found")
    return definition


def validate_custom_value(definition: CustomFieldDefinition, value: Any) -> None:
    if value is None and definition.is_required:
        raise HTTPException(status_code=422, detail=f"{definition.key} is required")
    if value is None:
        return
    if definition.field_type == "text" and not isinstance(value, str):
        raise HTTPException(status_code=422, detail=f"{definition.key} must be text")
    if definition.field_type == "number" and not isinstance(value, (int, float)):
        raise HTTPException(status_code=422, detail=f"{definition.key} must be a number")
    if definition.field_type == "dropdown" and value not in (definition.options or []):
        raise HTTPException(status_code=422, detail=f"{definition.key} must be one of {definition.options or []}")
    if definition.field_type == "date":
        try:
            date.fromisoformat(str(value))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f"{definition.key} must be an ISO date") from exc


def value_read(row: CustomFieldValue) -> CustomFieldValueRead:
    return CustomFieldValueRead(
        id=row.id,
        issue_id=row.issue_id,
        field_definition_id=row.field_definition_id,
        key=row.field_definition.key,
        name=row.field_definition.name,
        field_type=row.field_definition.field_type,
        value=row.value.get("value"),
        updated_at=row.updated_at,
    )


@router.get("/projects/{project_id}/custom-fields", response_model=list[CustomFieldDefinitionRead])
def list_custom_fields(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CustomFieldDefinitionRead]:
    project_or_404(db, project_id)
    definitions = db.scalars(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.project_id == project_id)
        .order_by(CustomFieldDefinition.id.asc())
    )
    return [CustomFieldDefinitionRead.model_validate(definition) for definition in definitions]


@router.post(
    "/projects/{project_id}/custom-fields",
    response_model=CustomFieldDefinitionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_custom_field(
    project_id: int,
    payload: CustomFieldDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomFieldDefinitionRead:
    project_or_404(db, project_id)
    if payload.field_type == "dropdown" and not payload.options:
        raise HTTPException(status_code=422, detail="Dropdown custom fields require options")
    definition = CustomFieldDefinition(project_id=project_id, **payload.model_dump())
    db.add(definition)
    db.flush()
    log_activity(
        db,
        project_id=project_id,
        issue_id=None,
        actor_id=current_user.id,
        event_type="custom_field_created",
        payload={"field_definition_id": definition.id, "key": definition.key},
    )
    db.commit()
    db.refresh(definition)
    return CustomFieldDefinitionRead.model_validate(definition)


@router.get("/issues/{issue_id}/custom-fields", response_model=list[CustomFieldValueRead])
def list_issue_custom_values(
    issue_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CustomFieldValueRead]:
    issue_or_404(db, issue_id)
    rows = db.scalars(
        select(CustomFieldValue)
        .join(CustomFieldDefinition)
        .where(CustomFieldValue.issue_id == issue_id)
        .order_by(CustomFieldDefinition.id.asc())
    )
    return [value_read(row) for row in rows]


@router.put("/issues/{issue_id}/custom-fields/{field_definition_id}", response_model=CustomFieldValueRead)
def upsert_issue_custom_value(
    issue_id: int,
    field_definition_id: int,
    payload: CustomFieldValueUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomFieldValueRead:
    issue = issue_or_404(db, issue_id)
    definition = definition_or_404(db, issue.project_id, field_definition_id)
    validate_custom_value(definition, payload.value)

    row = db.scalar(
        select(CustomFieldValue).where(
            CustomFieldValue.issue_id == issue.id,
            CustomFieldValue.field_definition_id == definition.id,
        )
    )
    if row:
        row.value = {"value": payload.value}
    else:
        row = CustomFieldValue(issue_id=issue.id, field_definition_id=definition.id, value={"value": payload.value})
        db.add(row)
    db.flush()
    log_activity(
        db,
        project_id=issue.project_id,
        issue_id=issue.id,
        actor_id=current_user.id,
        event_type="custom_field_value_updated",
        payload={"issue_id": issue.id, "field_definition_id": definition.id, "value": payload.value},
    )
    db.commit()
    db.refresh(row)
    return value_read(row)
