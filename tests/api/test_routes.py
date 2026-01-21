import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from snipster import Language, Snippet
from snipster.api import routes
from snipster.api.dependencies import get_repo
from snipster.exceptions import MultipleSnippetsFoundError, RepositoryError
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


def test_model_validation_error(client):
    """Test Model validation error"""

    response = client.post(
        "/snippets/v1/",
        json={
            "title": "fi",
            "code": "code1",
            "description": "description",
            "tags": "tag1,tag2",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()["detail"]
    for field, error in data.items():
        assert "value error" in error.lower()


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
    assert response.status_code == status.HTTP_201_CREATED
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


def test_delete_snippets_multiplesnippetsfound_error(client, mocker, sql_repo):
    """Test for MultipleSnippetsFoundError during delete"""

    mock_method = mocker.patch.object(sql_repo, "delete")
    mock_method.side_effect = MultipleSnippetsFoundError(
        "Multiple snippets found error"
    )

    response = client.delete("/snippets/v1/1")
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert "Multiple snippets found for snippet" in data["detail"]


def test_search_snippets_by_term(client, sql_repo):
    """Search for term in snippets"""

    snippet = Snippet(
        title="first", code="code1", description="description", tags="tag1,tag2"
    )
    sql_repo.add(snippet)

    response = client.get("/snippets/v1/search/?term=code")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_search_snippets_by_language(client, sql_repo):
    """Search for term in snippets by specific language"""

    snippet1 = Snippet(
        title="first", code="code1", description="description", tags="tag1,tag2"
    )
    snippet2 = Snippet(
        title="second", code="code2", description="description", tags="tag1,tag2"
    )
    snippet3 = Snippet(
        title="first",
        code="code1",
        description="description",
        tags="tag1,tag2",
        language=Language.JAVASCRIPT,
    )
    sql_repo.add(snippet1)
    sql_repo.add(snippet2)
    sql_repo.add(snippet3)

    response = client.get("/snippets/v1/search/?term=code&language=python")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_search_snippets_non_existent(client):
    """Search for non-existent snippets"""

    response = client.get("/snippets/v1/search/?term=code")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Search yielded no snippets"


def test_toggle_favourite_snippet(client, sql_repo):
    """Toggle favourite snippet"""

    snippet1 = Snippet(
        title="first", code="code1", description="description", tags="tag1,tag2"
    )
    sql_repo.add(snippet1)
    snippet = sql_repo.get(1)

    assert not snippet.favorite

    response = client.post("/snippets/v1/1/favourite")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Snippet '1' is Favourited"


def test_toggle_favourite_snippet_non_existent(client):
    """Search for non-existent snippet"""

    response = client.post("/snippets/v1/999/favourite")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Snippet '999' not found"


def test_tag_snippets(client, sql_repo):
    """Tag snippets"""

    snippet1 = Snippet(title="first", code="code1", description="description")
    sql_repo.add(snippet1)

    response = client.post("/snippets/v1/1/tags?tags=tag1&tags=tag2")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Successfully tagged snippet '1'"


def test_tag_snippets_removal(client, sql_repo):
    """Tag snippets for removal"""

    snippet1 = Snippet(
        title="first", code="code1", description="description", tags="tag1, tag2, tag3"
    )
    sql_repo.add(snippet1)

    response = client.post("/snippets/v1/1/tags?tags=tag2&remove=True")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert (
        data["message"]
        == "Successfully removed the following tags 'tag2' for snippet '1'"
    )


def test_tag_snippets_non_existstent(client):
    """Tag non-existent snippets"""

    response = client.post("/snippets/v1/999/tags?tags=tag2&remove=True")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Snippet '999' not found"


@pytest.mark.parametrize(
    "method,path,json_data,repo_method",
    [
        ("POST", "/snippets/v1/", {"title": "first", "code": "code1"}, "add"),
        ("GET", "/snippets/v1/list/", None, "list"),
        ("GET", "/snippets/v1/1", None, "get"),
        ("DELETE", "/snippets/v1/1", None, "delete"),
        ("GET", "/snippets/v1/search/?term=code", None, "search"),
        ("POST", "/snippets/v1/1/favourite", None, "toggle_favourite"),
        ("POST", "/snippets/v1/1/tags?tags=tag1&tags=tag2", None, "tags"),
    ],
    ids=["create", "list", "get", "delete", "search", "toggle_favourite", "tags"],
)
def test_routes_operational_errors_logged(
    client, sql_repo, mocker, method, path, json_data, repo_method
):
    """Test that all routes handle RepositoryError and return 500"""

    mock_method = mocker.patch.object(sql_repo, repo_method)
    mock_method.side_effect = RepositoryError("Database error")

    if method == "POST":
        response = client.post(path, json=json_data) if json_data else client.post(path)
    elif method == "GET":
        response = client.get(path)
    elif method == "DELETE":
        response = client.delete(path)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["detail"] == "Database error"
