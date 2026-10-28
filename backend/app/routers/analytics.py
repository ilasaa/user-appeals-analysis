from fastapi import APIRouter, Query
from typing import Literal
from app.db import get_connection
from app.queries import (
    GET_ANALYTICS_CATEGORIES,
    GET_ANALYTICS_SUMMARY,
    GET_ANALYTICS_TIMELINE
    
)
from app.schemas import (
    AnalyticsSummary,
    CategoryAnalytics,
    TimelinePoint
)


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
)
def get_analytics_summary():
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(GET_ANALYTICS_SUMMARY)

        summary = cursor.fetchone()

    return summary


@router.get(
    "/categories",
    response_model=list[CategoryAnalytics],
)
def get_analytics_categories():
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(GET_ANALYTICS_CATEGORIES)

        categories = cursor.fetchall()

    return categories

@router.get(
    "/timeline",
    response_model=list[TimelinePoint],
)
def get_analytics_timeline(
    period: Literal[
        "day",
        "week",
        "month",
    ] = "day",

    days: int = Query(
        default=30,
        ge=1,
        le=365,
    ),
):
    with (
        get_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            GET_ANALYTICS_TIMELINE,
            {
                "period": period,
                "days": days,
            },
        )

        timeline = cursor.fetchall()

    return timeline