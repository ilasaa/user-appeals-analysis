"""Analytics API integration tests with live PostgreSQL queries."""

import pytest


def create_appeal(client, title="Новая проблема", category_id=None):
    response = client.post(
        "/api/appeals",
        json={
            "title": title,
            "description": "Описание проблемы",
            "category_id": category_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_category(client, name):
    response = client.post("/api/categories", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def test_summary_empty(client):
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    assert response.json() == {
        "total_appeals": 0,
        "new_appeals": 0,
        "in_progress_appeals": 0,
        "resolved_appeals": 0,
        "closed_appeals": 0,
        "average_resolution_hours": None,
    }


def test_summary_counts_and_resolution_time(client):
    new = create_appeal(client, title="Первое обращение")
    in_progress = create_appeal(client, title="Второе обращение")
    resolved = create_appeal(client, title="Третье обращение")
    closed = create_appeal(client, title="Четвёртое обращение")

    assert (
        client.patch(
            f"/api/appeals/{in_progress['id']}/status",
            json={"status": "in_progress"},
        ).status_code
        == 200
    )
    for appeal, status in [
        (resolved, "resolved"),
        (closed, "resolved"),
        (closed, "closed"),
    ]:
        assert (
            client.patch(
                f"/api/appeals/{appeal['id']}/status", json={"status": status}
            ).status_code
            == 200
        )

    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_appeals"] == 4
    assert data["new_appeals"] == 1
    assert data["in_progress_appeals"] == 1
    assert data["resolved_appeals"] == 1
    assert data["closed_appeals"] == 1
    assert data["average_resolution_hours"] is not None
    assert data["average_resolution_hours"] >= 0
    assert new["id"] != in_progress["id"]


def test_categories_analytics_including_empty_and_uncategorized(client):
    account = create_category(client, "Аккаунт")
    empty = create_category(client, "Без обращений")
    first = create_appeal(client, "Не открывается аккаунт", account["id"])
    create_appeal(client, "Не получается войти", account["id"])
    create_appeal(client, "Проблема без категории", None)

    response = client.get("/api/analytics/categories")
    assert response.status_code == 200
    rows = response.json()
    assert rows == [
        {
            "category_id": account["id"],
            "category_name": "Аккаунт",
            "appeals_count": 2,
        },
        {
            "category_id": None,
            "category_name": "Без категории",
            "appeals_count": 1,
        },
        {
            "category_id": empty["id"],
            "category_name": "Без обращений",
            "appeals_count": 0,
        },
    ]
    assert first["id"] > 0


def test_categories_analytics_empty(client):
    response = client.get("/api/analytics/categories")
    assert response.status_code == 200
    assert response.json() == []


def test_timeline_fills_missing_days_with_zero(client):
    create_appeal(client)
    response = client.get(
        "/api/analytics/timeline", params={"period": "day", "days": 3}
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 3
    assert [row["appeals_count"] for row in rows] == [0, 0, 1]
    assert [row["period_start"] for row in rows] == sorted(
        row["period_start"] for row in rows
    )


@pytest.mark.parametrize("period", ["day", "week", "month"])
def test_timeline_groups_periods(client, period):
    create_appeal(client)
    response = client.get(
        "/api/analytics/timeline", params={"period": period, "days": 45}
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 1
    assert sum(row["appeals_count"] for row in rows) == 1
    starts = [row["period_start"] for row in rows]
    assert starts == sorted(set(starts))


def test_timeline_default_parameters(client):
    response = client.get("/api/analytics/timeline")
    assert response.status_code == 200
    assert len(response.json()) == 30
    assert all(row["appeals_count"] == 0 for row in response.json())


@pytest.mark.parametrize(
    "params",
    [
        {"period": "year"},
        {"days": 0},
        {"days": 366},
        {"days": "abc"},
    ],
)
def test_timeline_invalid_parameters(client, params):
    assert client.get("/api/analytics/timeline", params=params).status_code == 422
