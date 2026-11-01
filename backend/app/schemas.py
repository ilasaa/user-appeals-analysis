from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AppealCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=1)

    category_id: int | None = Field(default=None, gt=0)

    priority: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] = "medium"


class AppealUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    category_id: int | None = Field(
        default=None,
        gt=0,
    )

    priority: (
        Literal[
            "low",
            "medium",
            "high",
            "critical",
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")

        for field in ("title", "description", "priority"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self


class AppealResponse(BaseModel):
    id: int

    title: str
    description: str

    category_id: int | None
    category_name: str | None

    status: str
    priority: str

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class AppealsPage(BaseModel):
    items: list[AppealResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime


class AppealStatusUpdate(BaseModel):
    status: Literal[
        "new",
        "in_progress",
        "resolved",
        "closed",
    ]


class AnalyticsSummary(BaseModel):
    total_appeals: int
    new_appeals: int
    in_progress_appeals: int
    resolved_appeals: int
    closed_appeals: int
    average_resolution_hours: float | None


class CategoryAnalytics(BaseModel):
    category_id: int | None
    category_name: str
    appeals_count: int


class TimelinePoint(BaseModel):
    period_start: date
    appeals_count: int
