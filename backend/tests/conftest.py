"""Fixtures for integration tests against a dedicated local PostgreSQL database.

WARNING: Schema is re-created and data are truncated in appeals_test_db.
The fixture refuses non-local database addresses and any other database name.
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from app.main import app
from app.routers import appeals, categories, analytics


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env.test", override=False)


@pytest.fixture(scope="session")
def test_db_url():
    url = os.getenv("TEST_DATABASE_URL")

    if not url:
        pytest.fail(
            "TEST_DATABASE_URL is missing. Create .env.test in project root; "
            "point only to the local appeals_test_db database."
        )

    parsed = urlsplit(url)
    if parsed.scheme not in {"postgresql", "postgres"} or (
        parsed.hostname not in {"localhost", "127.0.0.1"}
    ) or parsed.path != "/appeals_test_db":
        pytest.fail(
            "Safety check failed: TEST_DATABASE_URL must point to "
            "postgresql://...@localhost:<port>/appeals_test_db "
            "or 127.0.0.1."
        )

    schema_path = PROJECT_ROOT / "database" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    # All destructive SQL below is restricted to the dedicated test database.
    with psycopg.connect(url) as connection:
        if connection.info.dbname != "appeals_test_db":
            pytest.fail("Refusing to recreate tables outside appeals_test_db")

        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS appeals")
            cursor.execute("DROP TABLE IF EXISTS categories")

            # schema.sql consists of plain CREATE TABLE statements; no PL/pgSQL.
            for statement in schema_sql.split(";"):
                if statement.strip():
                    cursor.execute(statement)

    return url


@pytest.fixture
def client(monkeypatch, test_db_url):
    """Patch all router-level imports of get_connection to use the test DB."""

    def test_connection():
        return psycopg.connect(test_db_url, row_factory=dict_row)

    for module in (appeals, categories, analytics):
        monkeypatch.setattr(module, "get_connection", test_connection)

    def clean_database():
        with test_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "TRUNCATE TABLE appeals, categories RESTART IDENTITY"
                )

    clean_database()
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        clean_database()
