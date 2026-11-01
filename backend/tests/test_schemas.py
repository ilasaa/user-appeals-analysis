"""Baseline Pydantic tests (also provided earlier in the conversation)."""

import pytest
from pydantic import ValidationError

from app.schemas import AppealCreate, AppealStatusUpdate, AppealUpdate


def test_appeal_create_defaults():
    appeal = AppealCreate(
        title="Проблема со входом", description="Не могу войти в аккаунт"
    )
    assert appeal.priority == "medium"
    assert appeal.category_id is None


def test_appeal_create_invalid_title():
    with pytest.raises(ValidationError):
        AppealCreate(title="Hi", description="Описание проблемы")


def test_appeal_update_empty():
    with pytest.raises(ValidationError):
        AppealUpdate()


def test_appeal_update_null_title():
    with pytest.raises(ValidationError):
        AppealUpdate(title=None)


def test_appeal_update_clear_category():
    appeal = AppealUpdate(category_id=None)
    assert "category_id" in appeal.model_fields_set


def test_appeal_status_invalid():
    with pytest.raises(ValidationError):
        AppealStatusUpdate(status="unknown")
