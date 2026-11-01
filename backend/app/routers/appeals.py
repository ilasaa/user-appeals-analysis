from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.db import get_connection
from app.queries import (
    COUNT_APPEALS,
    CREATE_APPEAL,
    DELETE_APPEAL,
    GET_APPEAL_BY_ID,
    GET_APPEALS,
    GET_CATEGORY_BY_ID,
    UPDATE_APPEAL,
    UPDATE_APPEAL_STATUS,
)
from app.schemas import (
    AppealCreate,
    AppealResponse,
    AppealStatusUpdate,
    AppealUpdate,
    AppealsPage,
)

router = APIRouter(
    prefix="/api/appeals",
    tags=["Appeals"],
)


@router.get(
    "",
    response_model=AppealsPage,
)
def get_appeals(
    status: (
        Literal[
            "new",
            "in_progress",
            "resolved",
            "closed",
        ]
        | None
    ) = None,
    priority: (
        Literal[
            "low",
            "medium",
            "high",
            "critical",
        ]
        | None
    ) = None,
    category_id: int | None = Query(
        default=None,
        gt=0,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    sort_by: Literal[
        "created_at",
        "updated_at",
        "priority",
    ] = "created_at",
    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc",
):
    search_pattern = f"%{search.strip()}%" if search and search.strip() else None

    filters = {
        "status": status,
        "priority": priority,
        "category_id": category_id,
        "search": search_pattern,
    }

    offset = (page - 1) * page_size

    sort_columns = {
        "created_at": "a.created_at",
        "updated_at": "a.updated_at",
        "priority": (
            "CASE a.priority "
            "WHEN 'low' THEN 1 "
            "WHEN 'medium' THEN 2 "
            "WHEN 'high' THEN 3 "
            "WHEN 'critical' THEN 4 "
            "END"
        ),
    }

    query = (
        f"{GET_APPEALS}\n"
        f"ORDER BY {sort_columns[sort_by]} "
        f"{sort_order.upper()}, a.id DESC\n"
        "LIMIT %(limit)s::integer "
        "OFFSET %(offset)s::integer"
    )

    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            COUNT_APPEALS,
            filters,
        )

        total = cursor.fetchone()["total"]

        cursor.execute(
            query,
            {
                **filters,
                "limit": page_size,
                "offset": offset,
            },
        )

        appeals = cursor.fetchall()

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": appeals,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get(
    "/{appeal_id}",
    response_model=AppealResponse,
)
def get_appeal(appeal_id: int):
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            GET_APPEAL_BY_ID,
            (appeal_id,),
        )

        appeal = cursor.fetchone()

    if appeal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appeal not found",
        )

    return appeal


@router.post(
    "",
    response_model=AppealResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appeal(appeal: AppealCreate):
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        if appeal.category_id is not None:
            cursor.execute(
                GET_CATEGORY_BY_ID,
                (appeal.category_id,),
            )

            category = cursor.fetchone()

            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

        cursor.execute(
            CREATE_APPEAL,
            (
                appeal.title,
                appeal.description,
                appeal.category_id,
                appeal.priority,
            ),
        )

        created_id = cursor.fetchone()["id"]

        cursor.execute(
            GET_APPEAL_BY_ID,
            (created_id,),
        )

        created_appeal = cursor.fetchone()

    return created_appeal


@router.patch(
    "/{appeal_id}/status",
    response_model=AppealResponse,
)
def update_appeal_status(
    appeal_id: int,
    data: AppealStatusUpdate,
):
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            UPDATE_APPEAL_STATUS,
            {
                "appeal_id": appeal_id,
                "status": data.status,
            },
        )

        updated = cursor.fetchone()

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appeal not found",
            )

        cursor.execute(
            GET_APPEAL_BY_ID,
            (appeal_id,),
        )

        appeal = cursor.fetchone()

    return appeal


@router.patch(
    "/{appeal_id}",
    response_model=AppealResponse,
)
def update_appeal(
    appeal_id: int,
    data: AppealUpdate,
):
    changed_fields = data.model_fields_set

    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        if "category_id" in changed_fields and data.category_id is not None:
            cursor.execute(
                GET_CATEGORY_BY_ID,
                (data.category_id,),
            )

            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                )

        cursor.execute(
            UPDATE_APPEAL,
            {
                "appeal_id": appeal_id,
                "title": data.title,
                "description": data.description,
                "category_id": data.category_id,
                "priority": data.priority,
                "change_title": "title" in changed_fields,
                "change_description": "description" in changed_fields,
                "change_category": "category_id" in changed_fields,
                "change_priority": "priority" in changed_fields,
            },
        )

        updated = cursor.fetchone()

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appeal not found",
            )

        cursor.execute(
            GET_APPEAL_BY_ID,
            (appeal_id,),
        )

        appeal = cursor.fetchone()

    return appeal


@router.delete(
    "/{appeal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_appeal(appeal_id: int):
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            DELETE_APPEAL,
            (appeal_id,),
        )

        deleted = cursor.fetchone()

        if deleted is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appeal not found",
            )
