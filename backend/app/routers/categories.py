from fastapi import APIRouter, HTTPException, status

from app.db import get_connection
from app.queries import (
    CREATE_CATEGORY,
    GET_CATEGORIES,
    GET_CATEGORY_BY_ID,
)
from app.schemas import (
    CategoryCreate,
    CategoryResponse,
)

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def get_categories():
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(GET_CATEGORIES)

        categories = cursor.fetchall()

    return categories


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(category_id: int):
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            GET_CATEGORY_BY_ID,
            (category_id,),
        )

        category = cursor.fetchone()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(category: CategoryCreate):
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            CREATE_CATEGORY,
            (
                category.name,
                category.description,
            ),
        )

        created = cursor.fetchone()

        if created is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists",
            )

        cursor.execute(
            GET_CATEGORY_BY_ID,
            (created["id"],),
        )

        created_category = cursor.fetchone()

    return created_category
