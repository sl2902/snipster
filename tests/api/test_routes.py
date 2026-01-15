import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from snipster import Snippet
from snipster.api import routes
from snipster.api.dependencies import get_repo
from snipster.repositories.backend import create_repository


@pytest.fixture(scope="function")
def sql_repo(mocker, tmp_path):
    """Create SQLModelRepository"""

    db_file = tmp_path / "test.db"

    def mock_config(key, default=None):
        config_values = {
            "DATABASE_URL": f"sqlite:///{db_file}",  # "sqlite:///:memory:?check_same_thread=False",
            # "DATABASE_URL": "sqlite:///file:testdb?mode=memory&cache=shared&uri=true",
            "REPOSITORY_TYPE": "sql",
        }
        return config_values.get(key, default)

    mocker.patch("snipster.repositories.backend.config", side_effect=mock_config)
    repo = create_repository("sql")
    yield repo
    repo.db_manager.engine.dispose()


@pytest.fixture(scope="function")
def client(sql_repo):
    """Instantiate TestClient"""

    app = FastAPI()
    app.include_router(routes.router)

    app.dependency_overrides[get_repo] = lambda: sql_repo

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_snippet(client, sql_repo):
    """Create Snippet endpoint"""

    response = client.post(
        "/snippets/v1/",
        json={
            "title": "first",
            "code": "code1",
            "description": "description",
            "tags": "tag1,tag2",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Successfully created Snippet with title 'first'"


def test_create_duplicate_snippet(client, sql_repo):
    """Create duplicate snippet"""

    snippet = Snippet(
        title="first", code="code1", description="description", tags="tag1,tag2"
    )
    sql_repo.add(snippet)

    response = client.post(
        "/snippets/v1/",
        json={
            "title": "first",
            "code": "code1",
            "description": "description",
            "tags": "tag1,tag2",
        },
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"] == "Snippet already exists"


def test_list_snippets(client, sql_repo):
    """List snippets endpoint"""

    snippet1 = Snippet(
        title="first", code="code1", description="description", tags="tag1,tag2"
    )
    snippet2 = Snippet(
        title="second", code="code2", description="description", tags="tag1,tag2"
    )
    sql_repo.add(snippet1)
    sql_repo.add(snippet2)

    response = client.get("/snippets/v1/list/")
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 2


def test_list_snippets_empty(client, sql_repo):
    """List snippets empty repository"""

    response = client.get("/snippets/v1/list/")
    data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert data["detail"] == "No snippets in repository"


def test_get_snippet(client, sql_repo):
    """Fetch single snippet"""

    snippet = Snippet(
        title="first", code="code1", description="description", tags="tag1,tag2"
    )
    sql_repo.add(snippet)

    response = client.get("/snippets/v1/1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "first"


def test_get_snippet_non_existent(client, sql_repo):
    """Fetch non-existent snippet"""

    response = client.get("/snippets/v1/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Snippet '999' not found"


def test_delete_snippet(client, sql_repo):
    """Delete snippet"""

    snippet = Snippet(
        title="first", code="code1", description="description", tags="tag1,tag2"
    )
    sql_repo.add(snippet)

    response = client.delete("/snippets/v1/1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Snippet '1' deleted successfully"


def test_delete_snippet_non_existent(client, sql_repo):
    """Delete non-existent snippet"""

    response = client.delete("/snippets/v1/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Snippet '999' not found"
