"""Additional unit tests for Pydantic schemas. Database not required."""

import pytest
from pydantic import ValidationError

from app.schemas import AppealCreate, AppealStatusUpdate, AppealUpdate, CategoryCreate


@pytest.mark.parametrize("priority", ["low", "medium", "high", "critical"])
def test_create_accepts_allowed_priorities(priority):
    appeal = AppealCreate(
        title="Ошибка авторизации",
        description="Не удаётся войти",
        priority=priority,
    )
    assert appeal.priority == priority


@pytest.mark.parametrize("category_id", [0, -10])
def test_create_rejects_invalid_category_id(category_id):
    with pytest.raises(ValidationError):
        AppealCreate(
            title="Ошибка авторизации", description="Описание", category_id=category_id
        )


@pytest.mark.parametrize("field", ["title", "description", "priority"])
def test_update_rejects_explicit_null(field):
    with pytest.raises(ValidationError):
        AppealUpdate.model_validate({field: None})


def test_update_partial_payload_keeps_unset_fields_distinct():
    update = AppealUpdate(description="Исправленное описание")
    assert update.model_fields_set == {"description"}
    assert update.title is None  # Missing, rather than explicitly assigned null.


@pytest.mark.parametrize("status", ["new", "in_progress", "resolved", "closed"])
def test_status_model_accepts_all_statuses(status):
    data = AppealStatusUpdate(status=status)
    assert data.status == status


@pytest.mark.parametrize("name", ["", "X" * 101])
def test_category_name_validation(name):
    with pytest.raises(ValidationError):
        CategoryCreate(name=name)
