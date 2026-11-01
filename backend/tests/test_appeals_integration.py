"""Appeal API integration tests (real PostgreSQL, no production data)."""

import pytest


def make_category(client, name="Учётная запись"):
    response = client.post("/api/categories", json={"name": name})
    assert response.status_code == 201
    return response.json()


def make_appeal(client, **changes):
    payload = {
        "title": "Не работает вход",
        "description": "Проблема при авторизации",
    }
    payload.update(changes)
    response = client.post("/api/appeals", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_appeals_empty_page(client):
    response = client.get("/api/appeals")
    assert response.status_code == 200
    assert response.json() == {
        "items": [], "total": 0, "page": 1, "page_size": 10,
        "total_pages": 0,
    }


def test_create_appeal_defaults_and_get_by_id(client):
    appeal = make_appeal(client)
    assert appeal["title"] == "Не работает вход"
    assert appeal["description"] == "Проблема при авторизации"
    assert appeal["status"] == "new"
    assert appeal["priority"] == "medium"
    assert appeal["category_id"] is None
    assert appeal["category_name"] is None
    assert appeal["resolved_at"] is None
    assert appeal["created_at"]
    assert appeal["updated_at"]

    response = client.get(f"/api/appeals/{appeal['id']}")
    assert response.status_code == 200
    assert response.json() == appeal


def test_create_appeal_with_category(client):
    category = make_category(client)
    appeal = make_appeal(
        client, category_id=category["id"], priority="high"
    )
    assert appeal["category_id"] == category["id"]
    assert appeal["category_name"] == category["name"]
    assert appeal["priority"] == "high"


def test_create_appeal_unknown_category(client):
    response = client.post(
        "/api/appeals",
        json={"title": "Ошибка входа", "description": "Ошибка", "category_id": 999},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"
    assert client.get("/api/appeals").json()["total"] == 0


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "Hi", "description": "Описание"},
        {"title": "x" * 201, "description": "Описание"},
        {"title": "Нормальный заголовок", "description": ""},
        {"title": "Нормальный заголовок"},
        {"title": "Нормальный заголовок", "description": "Описание", "priority": "urgent"},
        {"title": "Нормальный заголовок", "description": "Описание", "category_id": 0},
    ],
)
def test_create_appeal_invalid_data(client, payload):
    response = client.post("/api/appeals", json=payload)
    assert response.status_code == 422
    assert client.get("/api/appeals").json()["total"] == 0


def test_appeal_not_found(client):
    response = client.get("/api/appeals/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Appeal not found"


def test_list_pagination_and_order(client):
    first = make_appeal(client, title="Обращение номер один")
    second = make_appeal(client, title="Обращение номер два")
    third = make_appeal(client, title="Обращение номер три")

    page1 = client.get("/api/appeals", params={"page": 1, "page_size": 2})
    page2 = client.get("/api/appeals", params={"page": 2, "page_size": 2})

    assert page1.status_code == 200
    assert page1.json()["total"] == 3
    assert page1.json()["total_pages"] == 2
    assert page1.json()["page_size"] == 2
    assert [a["id"] for a in page1.json()["items"]] == [third["id"], second["id"]]
    assert [a["id"] for a in page2.json()["items"]] == [first["id"]]


def test_filter_by_status_priority_and_category(client):
    category = make_category(client)
    matching = make_appeal(
        client, title="Оплата не проходит", category_id=category["id"], priority="high"
    )
    make_appeal(client, title="Другая проблема", priority="low")
    updated = client.patch(
        f"/api/appeals/{matching['id']}/status", json={"status": "in_progress"}
    )
    assert updated.status_code == 200

    response = client.get(
        "/api/appeals",
        params={
            "status": "in_progress", "priority": "high", "category_id": category["id"]
        },
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == matching["id"]


def test_text_search_case_insensitive_in_title_and_description(client):
    one = make_appeal(client, title="Ошибка ОПЛАТЫ", description="Не проходит операция")
    two = make_appeal(client, title="Другая проблема", description="Платёжная ОПЛАТА")
    make_appeal(client, title="Потерянный пароль", description="Восстановление пароля")

    response = client.get("/api/appeals", params={"search": "  оплат  "})
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {r["id"] for r in response.json()["items"]} == {one["id"], two["id"]}


def test_sort_by_priority(client):
    low = make_appeal(client, title="Низкий приоритет", priority="low")
    critical = make_appeal(client, title="Критическая проблема", priority="critical")
    high = make_appeal(client, title="Высокий приоритет", priority="high")

    response = client.get(
        "/api/appeals", params={"sort_by": "priority", "sort_order": "desc"}
    )
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["items"]] == [
        critical["id"], high["id"], low["id"]
    ]


def test_patch_appeal_fields(client):
    category = make_category(client)
    old = make_appeal(client)
    response = client.patch(
        f"/api/appeals/{old['id']}",
        json={
            "title": "Новый заголовок",
            "description": "Новое описание",
            "priority": "critical",
            "category_id": category["id"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Новый заголовок"
    assert body["description"] == "Новое описание"
    assert body["priority"] == "critical"
    assert body["category_id"] == category["id"]
    assert body["category_name"] == category["name"]
    assert body["status"] == "new"


def test_patch_appeal_can_clear_category(client):
    category = make_category(client)
    appeal = make_appeal(client, category_id=category["id"])
    response = client.patch(
        f"/api/appeals/{appeal['id']}", json={"category_id": None}
    )
    assert response.status_code == 200
    assert response.json()["category_id"] is None
    assert response.json()["category_name"] is None


@pytest.mark.parametrize(
    "patch",
    [
        {},
        {"title": None},
        {"description": None},
        {"priority": None},
        {"priority": "very_high"},
        {"category_id": -1},
    ],
)
def test_patch_appeal_rejects_invalid_data(client, patch):
    appeal = make_appeal(client)
    response = client.patch(f"/api/appeals/{appeal['id']}", json=patch)
    assert response.status_code == 422
    assert client.get(f"/api/appeals/{appeal['id']}").json() == appeal


def test_patch_appeal_unknown_category(client):
    appeal = make_appeal(client)
    response = client.patch(
        f"/api/appeals/{appeal['id']}", json={"category_id": 999}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_patch_appeal_not_found(client):
    response = client.patch("/api/appeals/999", json={"priority": "high"})
    assert response.status_code == 404


def test_status_lifecycle(client):
    appeal = make_appeal(client)
    path = f"/api/appeals/{appeal['id']}/status"

    in_progress = client.patch(path, json={"status": "in_progress"})
    assert in_progress.status_code == 200
    assert in_progress.json()["status"] == "in_progress"
    assert in_progress.json()["resolved_at"] is None

    resolved = client.patch(path, json={"status": "resolved"})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None

    closed = client.patch(path, json={"status": "closed"})
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    assert closed.json()["resolved_at"] == resolved.json()["resolved_at"]

    reopened = client.patch(path, json={"status": "new"})
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "new"
    assert reopened.json()["resolved_at"] is None


def test_patch_status_invalid_and_missing_id(client):
    appeal = make_appeal(client)
    assert client.patch(
        f"/api/appeals/{appeal['id']}/status", json={"status": "paused"}
    ).status_code == 422
    response = client.patch("/api/appeals/999/status", json={"status": "closed"})
    assert response.status_code == 404


def test_delete_appeal_and_delete_unknown(client):
    appeal = make_appeal(client)
    response = client.delete(f"/api/appeals/{appeal['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/appeals/{appeal['id']}").status_code == 404
    assert client.delete(f"/api/appeals/{appeal['id']}").status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"page": 0},
        {"page_size": 0},
        {"page_size": 101},
        {"category_id": -1},
        {"status": "unknown"},
        {"priority": "urgent"},
        {"sort_by": "title"},
        {"sort_order": "sideways"},
        {"search": ""},
    ],
)
def test_list_invalid_query_parameters(client, params):
    response = client.get("/api/appeals", params=params)
    assert response.status_code == 422
