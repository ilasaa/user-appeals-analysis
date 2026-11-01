"""Category API integration tests (real SQL, isolated PostgreSQL)."""

import pytest


def test_categories_empty(client):
    response = client.get("/api/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_create_and_get_category(client):
    created = client.post(
        "/api/categories",
        json={"name": "Авторизация", "description": "Проблемы со входом"},
    )

    assert created.status_code == 201
    category = created.json()
    assert category["name"] == "Авторизация"
    assert category["description"] == "Проблемы со входом"
    assert isinstance(category["id"], int)
    assert category["created_at"]

    one = client.get(f"/api/categories/{category['id']}")
    assert one.status_code == 200
    assert one.json() == category

    categories = client.get("/api/categories")
    assert categories.status_code == 200
    assert categories.json() == [category]


def test_categories_sorted_by_name(client):
    client.post("/api/categories", json={"name": "Платежи"})
    client.post("/api/categories", json={"name": "Аккаунт"})

    result = client.get("/api/categories")
    assert result.status_code == 200
    assert [row["name"] for row in result.json()] == ["Аккаунт", "Платежи"]


def test_duplicate_category_returns_409(client):
    data = {"name": "Аккаунт", "description": None}
    assert client.post("/api/categories", json=data).status_code == 201

    response = client.post("/api/categories", json=data)
    assert response.status_code == 409
    assert response.json()["detail"] == "Category already exists"
    assert len(client.get("/api/categories").json()) == 1


def test_category_not_found(client):
    response = client.get("/api/categories/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": ""},
        {"name": "x" * 101},
        {"name": None},
    ],
)
def test_category_invalid_payload_returns_422(client, payload):
    response = client.post("/api/categories", json=payload)
    assert response.status_code == 422
    assert client.get("/api/categories").json() == []


def test_category_invalid_id_returns_422(client):
    assert client.get("/api/categories/not-a-number").status_code == 422
