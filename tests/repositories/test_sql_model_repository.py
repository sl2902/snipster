import httpx
import pytest
from sqlalchemy.exc import (
    IntegrityError,
    MultipleResultsFound,
    OperationalError,
    SQLAlchemyError,
)

from snipster import Gist, Language, Snippet
from snipster.exceptions import (
    DatabaseConnectionError,
    DuplicateGistError,
    DuplicateSnippetError,
    GistNotFoundError,
    MultipleSnippetsFoundError,
    RepositoryError,
    SnippetNotFoundError,
)
from snipster.repositories.sql_model_repository import SQLModelRepository
from snipster.types import GistStatus


@pytest.fixture
def repo():
    repository = SQLModelRepository(db_url="sqlite:///:memory:")
    yield repository
    repository.db_manager.engine.dispose()


@pytest.fixture
def snippet_factory(repo):
    """Factory for creating test snippets"""

    def _create_snippet(title="test code", code="print('hello test')"):
        snippet = Snippet(title=title, code=code)
        repo.add(snippet)
        return snippet

    return _create_snippet


def test_add_and_get_snippet(repo, snippet_factory):
    """Test adding a snippet and retrieving it by ID"""
    snippet = snippet_factory()

    retrieved = repo.get(snippet.id)
    assert retrieved is not None
    assert retrieved.title == snippet.title
    assert retrieved.code == snippet.code
    assert retrieved.id == snippet.id


def test_add_multiple_snippets(repo):
    """Test adding multiple different snippets"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")

    repo.add(snippet1)
    repo.add(snippet2)

    all_snippets = repo.list()
    assert len(all_snippets) == 2

    assert repo.get(snippet1.id) is not None
    assert repo.get(snippet2.id) is not None


def test_add_duplicate_snippet_error(repo, snippet_factory):
    """Test that duplicate snippets (same title+language) are rejected and an error is thrown"""

    with pytest.raises(DuplicateSnippetError):
        for _ in range(2):
            snippet_factory()
    all_snippets = repo.list()
    assert len(all_snippets) == 1
    assert all_snippets[0].title == "test code"


def test_list_empty_repo(repo):
    """Test listing snippets from empty repository"""
    assert len(repo.list()) == 0
    assert repo.list() == []


def test_list_returns_all_snippets(repo):
    """Test that list returns all added snippets"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")

    repo.add(snippet1)
    repo.add(snippet2)

    all_snippets = repo.list()
    assert len(all_snippets) == 2

    titles = {s.title for s in all_snippets}
    assert titles == {"first", "second"}


def test_get_non_existent_snippet(repo):
    """Test that getting non-existent snippet returns None"""
    assert repo.get(999) is None


def test_delete_existing_snippet(repo, snippet_factory):
    """Test deleting an existing snippet"""
    snippet = snippet_factory()
    snippet_id = snippet.id

    repo.delete(snippet_id)

    assert repo.get(snippet_id) is None
    assert len(repo.list()) == 0


def test_delete_non_existent_snippet_does_not_fail(repo, snippet_factory):
    """Test that deleting non-existent snippet raise SnippetNotFoundError"""
    snippet_factory()

    with pytest.raises(SnippetNotFoundError):
        repo.delete(999)


def test_delete_removes_from_list(repo):
    """Test that deleted snippet is removed from list"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")

    repo.add(snippet1)
    repo.add(snippet2)

    assert len(repo.list()) == 2

    repo.delete(snippet1.id)

    remaining = repo.list()
    assert len(remaining) == 1
    assert remaining[0].title == "second"


def test_delete_raises_error_on_multiple_results(repo, mocker):
    """Test delete raises error when multiple snippets found"""

    mock_session = mocker.patch("snipster.database_manager.Session")

    mock_result = mocker.Mock()
    mock_result.one.side_effect = MultipleResultsFound(
        "Multiple rows were found for one()"
    )
    mock_session.return_value.__enter__.return_value.exec.return_value = mock_result

    with pytest.raises(MultipleSnippetsFoundError, match="Multiple snippets found"):
        repo.delete(1)


def test_id_persistence_after_operations(repo):
    """Test that IDs are persistent across add/delete operations"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")
    snippet3 = Snippet(title="third", code="code3")

    repo.add(snippet1)
    id1 = snippet1.id

    repo.add(snippet2)
    id2 = snippet2.id

    repo.delete(id1)

    repo.add(snippet3)
    id3 = snippet3.id

    assert id3 != id1
    assert id3 > id2


def test_search_term_in_title(repo):
    """Test whether search term is in snippet title"""
    snippet1 = Snippet(title="first_title", code="code1")

    repo.add(snippet1)
    all_snippets = repo.search("first")

    assert len(all_snippets) == 1
    assert all_snippets[0].title == snippet1.title


def test_search_python_term_in_code(repo):
    """Test whether search term is in snippet `code` in Python"""
    snippet1 = Snippet(title="first_title", code="code1")
    snippet2 = Snippet(title="second_title", code="code2")
    snippet3 = Snippet(title="third_itle", code="code3", language=Language.JAVASCRIPT)

    repo.add(snippet1)
    repo.add(snippet2)
    repo.add(snippet3)
    all_snippets = repo.search("code", language="python")
    codes = {snippet.code for snippet in all_snippets}

    assert len(all_snippets) == 2
    assert codes == {snippet1.code, snippet2.code}


def test_search_term_in_description(repo):
    """Test whether search term is in snippet `description`"""
    snippet1 = Snippet(title="first_title", code="code1", description="Describe code1")
    snippet2 = Snippet(title="second_title", code="code2", description="Describe code2")
    snippet3 = Snippet(title="third_itle", code="code3", language=Language.JAVASCRIPT)

    repo.add(snippet1)
    repo.add(snippet2)
    repo.add(snippet3)
    all_snippets = repo.search("code1")

    assert len(all_snippets) == 1
    assert all_snippets[0].description == snippet1.description


def test_search_term_not_found(repo, snippet_factory):
    """Test search that returns no results"""
    snippet1 = snippet_factory()

    repo.add(snippet1)
    results = repo.search("search")

    assert len(results) == 0
    assert isinstance(results, list)


def test_search_term_found_but_lang_not_found(repo, mocker, snippet_factory):
    """Test search with valid term but non-matching language returns empty list"""
    mock_logger = mocker.patch("snipster.repositories.sql_model_repository.logger")
    snippet1 = snippet_factory()

    repo.add(snippet1)
    results = repo.search("test", language="TypeScript")

    assert len(results) == 0
    mock_logger.warning.assert_called_once()


def test_search_wildcard_percent_doesnt_match_all(repo):
    """Test that % is escaped and doesn't match everything"""
    repo.add(Snippet(title="test1", code="code"))
    repo.add(Snippet(title="test2", code="code"))
    repo.add(Snippet(title="100%", code="code"))

    results = repo.search("%")

    assert len(results) == 1
    assert results[0].title == "100%"


def test_search_wildcard_underscore_doesnt_match_all(repo):
    """Test that _ is escaped and doesn't match everything"""
    repo.add(Snippet(title="test1", code="code"))
    repo.add(Snippet(title="test2", code="code"))
    repo.add(Snippet(title="test_var", code="code"))

    results = repo.search("_")

    assert len(results) == 1
    assert results[0].title == "test_var"


def test_search_backslash_escaping(repo):
    """Test that backslashes are properly escaped"""
    repo.add(Snippet(title="C:\\Users", code="code"))
    repo.add(Snippet(title="normal", code="code"))

    results = repo.search("C:\\")

    assert len(results) == 1
    assert "C:\\" in results[0].title


def test_search_prevents_sql_injection_or_operator(repo, snippet_factory):
    """Test that OR injection doesn't return all records"""
    snippet1 = snippet_factory()

    repo.add(snippet1)
    results = repo.search("nonexistent' OR '1'='1")

    assert len(results) == 0


def test_toggle_favourite(repo, snippet_factory):
    """Test toggle snippet `favourite`"""
    snippet_factory()

    snippet = repo.get(1)
    assert snippet.favorite is False

    favourite = repo.toggle_favourite(1)
    assert favourite is True

    favourite = repo.toggle_favourite(1)
    assert favourite is False

    with pytest.raises(SnippetNotFoundError):
        repo.toggle_favourite(999)


def test_snippet_add_tags(repo, snippet_factory):
    """Test add tags to snippet"""
    snippet_factory()

    repo.tags(1, "tag1", "tag2", "tag4", "tag3")
    snippet_with_tags = repo.get(1)

    all_tags = snippet_with_tags.tags.split(", ")
    assert len(all_tags) == 4
    assert all_tags == ["tag1", "tag2", "tag3", "tag4"]


def test_snippet_remove_tags(repo, snippet_factory):
    """Test remove tags from snippet"""
    snippet_factory()

    repo.tags(1, "tag1", "tag2", "tag4", "tag3")
    repo.tags(1, "tag2", "tag3", remove=True)
    snippet_with_tags = repo.get(1)

    all_tags = snippet_with_tags.tags.split(", ")
    assert len(all_tags) == 2
    assert all_tags == ["tag1", "tag4"]


def test_snippet_unsort_tags_then_sort_tags(repo, snippet_factory):
    """Test unsorted tags followed by sort tags in snippet"""
    snippet_factory()

    repo.tags(1, "tag1", "tag2", "tag4", "tag3", sort=False)

    repo.tags(1, "tag2", sort=False, remove=True)
    snippet_with_unsorted_tags = repo.get(1)
    all_tags = snippet_with_unsorted_tags.tags.split(", ")

    assert len(all_tags) == 3
    assert all_tags == ["tag1", "tag4", "tag3"]

    repo.tags(1, "tag1", "tag2", "tag4", "tag3")
    snippet_with_sorted_tags = repo.get(1)
    all_tags = snippet_with_sorted_tags.tags.split(", ")

    assert len(all_tags) == 4
    assert all_tags == ["tag1", "tag2", "tag3", "tag4"]

    with pytest.raises(SnippetNotFoundError):
        repo.tags(999, "tag1")


def test_duplicate_tags(repo, snippet_factory):
    """Test adding duplicate tags"""
    snippet_factory()

    repo.tags(1, "tag1")
    snippet = repo.get(1)

    assert snippet is not None
    assert snippet.tags == "tag1"

    repo.tags(1, "tag1", "tag2")
    snippet = repo.get(1)

    assert len(snippet.tags.split(", ")) == 2
    assert snippet.tags == "tag1, tag2"


def test_create_gist_success(repo, mocker):
    """Test successful gist creation"""
    mock_get_gist = mocker.patch.object(repo, "get_gist", return_value=None)

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.side_effect = lambda key, default=None: {
        "GH_TOKEN": "test_token_123",
        "GIST_URL": "https://api.github.com/gists",
    }.get(key, default)

    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "html_url": "https://gist.github.com/user/abc123"
    }
    mock_response.raise_for_status = mocker.Mock()

    mock_post = mocker.patch("snipster.repositories.sql_model_repository.httpx.post")
    mock_post.return_value = mock_response

    mock_add_gist = mocker.patch.object(repo, "add_gist")

    gist_url = repo.create_gist(
        snippet_id=1,
        code="print('hello')",
        title="Test Snippet",
        language="Python",
        is_public=True,
    )

    mock_get_gist.assert_called_once_with(1)
    mock_post.assert_called_once()
    mock_add_gist.assert_called_once_with(
        1, "https://gist.github.com/user/abc123", True
    )

    assert gist_url == "https://gist.github.com/user/abc123"


def test_create_gist_fails_with_gist_exists(repo, mocker):
    """Test create_gist raises error when gist already exists for snippet"""

    existing_gist = mocker.Mock()
    existing_gist.gist_url = "https://gist.github.com/existing/test"
    mock_get_gist = mocker.patch.object(repo, "get_gist", return_value=existing_gist)

    with pytest.raises(DuplicateGistError):
        repo.create_gist(1, "print('test')", "Test", language="Python")

    mock_get_gist.assert_called_once_with(1)


def test_create_gist_github_api_failure(repo, mocker):
    """Test create_gist handles GitHub API errors"""
    mocker.patch.object(repo, "get_gist", return_value=None)

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.side_effect = lambda key, default=None: {
        "GH_TOKEN": "test_token",
        "GIST_URL": "https://api.github.com/gists",
    }.get(key, default)

    mock_post = mocker.patch("snipster.repositories.sql_model_repository.httpx.post")
    mock_post.side_effect = httpx.HTTPError("API rate limit exceeded")

    with pytest.raises(RepositoryError, match="Failed to create gist"):
        repo.create_gist(1, "test", "Test", language="Python")


def test_get_gist(repo, snippet_factory, mocker):
    """Test fetching gist"""

    mocker.patch.object(repo, "_verify_gist_exists", return_value=True)

    snippet = snippet_factory()

    repo.add_gist(snippet.id, "https://api.github.com/gists/test", is_public=True)

    gist = repo.get_gist(snippet.id)

    assert gist.gist_url == "https://api.github.com/gists/test"
    assert gist.gist_id == "test"


def test_get_gist_does_not_exist_when_snippet_exists(repo, snippet_factory):
    """Test non-existent gist when snippet exists"""

    snippet = snippet_factory()
    gist = repo.get_gist(snippet.id)

    assert snippet is not None
    assert gist is None


def test_get_gist_does_not_exist(repo, snippet_factory):
    """Test non-existent gist"""

    gist = repo.get_gist(1)

    assert gist is None


def test_get_gist_missing_from_github(repo, mocker, snippet_factory):
    """Test get_gist that exists in the database but is removed from GitHub"""

    snippet = snippet_factory()

    repo.add_gist(snippet.id, "https://api.github.com/gists/test", is_public=True)

    mocker.patch.object(repo, "_verify_gist_exists", return_value=False)

    gist = repo.get_gist(snippet.id)

    assert gist is not None
    assert gist.status == GistStatus.DELETED_ON_GITHUB


def test_verify_gist_exists(repo, mocker, snippet_factory):
    """Test existence of gist on GitHub"""

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_config_123"

    mock_response = mocker.Mock()
    mock_response.status_code = 200

    mock_get = mocker.patch("snipster.repositories.sql_model_repository.httpx.get")
    mock_get.return_value = mock_response

    result = repo._verify_gist_exists("gist_id")

    assert result is True
    mock_get.assert_called_once_with(
        "https://api.github.com/gists/gist_id",
        headers={"Authorization": "token test_config_123"},
    )


def test_verify_gist_exists_returns_false_when_gist_not_found(repo, mocker):
    """Test _verify_gist_exists returns False when gist deleted on GitHub"""

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_token_123"

    mock_response = mocker.Mock()
    mock_response.status_code = 404

    mock_get = mocker.patch("snipster.repositories.sql_model_repository.httpx.get")
    mock_get.return_value = mock_response

    result = repo._verify_gist_exists("deleted_gist")

    assert result is False


def test_verify_gist_exists_returns_false_on_http_error(repo, mocker):
    """Test _verify_gist_exists returns False when HTTP error occurs"""

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_token"

    mock_get = mocker.patch("snipster.repositories.sql_model_repository.httpx.get")
    mock_get.side_effect = httpx.HTTPError("Connection error")

    result = repo._verify_gist_exists("test")

    assert result is False


def test_add_gist_fails_when_snippet_not_found(repo):
    """Test add_gist raises error when snippet doesn't exist"""

    with pytest.raises(RepositoryError):
        repo.add_gist(1, "https://api.github.com/gists/test", is_public=True)


def test_add_gist_fails_with_unique_constraint_error(mocker):
    """Test add_gist fails due to unique constraint error"""

    repo = SQLModelRepository(db_url="sqlite:///:memory:")
    repo.add(Snippet(title="test", code="test"))
    snippet = repo.get(1)

    mock_logger = mocker.patch("snipster.repositories.sql_model_repository.logger")
    mock_session = mocker.patch("snipster.database_manager.Session")

    orig_error = Exception("UNIQUE constraint failed: gist.snippet_id")
    mock_session.return_value.__enter__.return_value.commit.side_effect = (
        IntegrityError(
            statement="INSERT INTO gist",
            params={},
            orig=orig_error,
        )
    )

    with pytest.raises(DuplicateGistError):
        for _ in range(2):
            repo.add_gist(
                snippet.id, "https://api.github.com/gists/test", is_public=True
            )

    mock_logger.warning.assert_called_once()
    repo.db_manager.engine.dispose()


def test_add_gist_fails_with_operational_error(mocker):
    """Test add_gist fails due to Operational error"""

    repo = SQLModelRepository(db_url="sqlite:///:memory:")
    repo.add(Snippet(title="test", code="test"))
    snippet = repo.get(1)

    mock_session = mocker.patch("snipster.database_manager.Session")

    mock_session.return_value.__enter__.return_value.commit.side_effect = (
        OperationalError(
            "Mock DB error",
            None,
            None,
        )
    )

    with pytest.raises(RepositoryError):
        repo.add_gist(snippet.id, "https://api.github.com/gists/test", is_public=True)

    repo.db_manager.engine.dispose()


def test_delete_gist_successful(repo, mocker, snippet_factory):
    """Test successful gist deletion"""

    mocker.patch.object(repo, "_verify_gist_exists", return_value=True)

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_config_123"

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.Mock()

    mock_delete = mocker.patch(
        "snipster.repositories.sql_model_repository.httpx.delete"
    )
    mock_delete.return_value = mock_response

    snippet = snippet_factory()
    repo.add_gist(snippet.id, "https://api.github.com/gists/test", is_public=True)

    gist = repo.get_gist(snippet.id)
    assert gist is not None
    assert gist.gist_url == "https://api.github.com/gists/test"

    repo.delete_gist(snippet.id)

    mock_delete.assert_called_once()
    call_args = mock_delete.call_args
    assert "test" in call_args[0][0]
    assert call_args.kwargs["headers"]["Authorization"] == "token test_config_123"

    gist = repo.get_gist(snippet.id)
    assert gist is None

    snippet_after = repo.get(snippet.id)
    assert snippet_after is not None


def test_delete_gist_not_found_error(repo, snippet_factory):
    """Test delete_gist with GistNotFoundError"""

    snippet = snippet_factory()

    with pytest.raises(GistNotFoundError):
        repo.delete_gist(snippet.id)


def test_delete_gist_multiple_gists_found_error(repo, mocker, snippet_factory):
    """Test delete_gist fails for Multiple Gists Found Error"""

    snippet = snippet_factory()
    repo.add_gist(
        snippet.id, "https://api.github.com/gists/test_gist_id", is_public=True
    )

    mocker.patch.object(repo, "_verify_gist_exists", return_value=True)

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_token"

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = mocker.Mock()

    mock_delete = mocker.patch(
        "snipster.repositories.sql_model_repository.httpx.delete"
    )
    mock_delete.return_value = mock_response

    original_delete = repo.db_manager.delete_record

    def mock_delete_record(model, pk):
        if model == Gist:
            raise MultipleResultsFound("Multiple rows were found for one()")
        return original_delete(model, pk)

    mocker.patch.object(
        repo.db_manager, "delete_record", side_effect=mock_delete_record
    )

    with pytest.raises(MultipleSnippetsFoundError, match="Multiple gists found"):
        repo.delete_gist(snippet.id)


def test_delete_gist_already_deleted_on_github(repo, mocker, snippet_factory):
    """Test delete_gist handles 404 (already deleted on GitHub) gracefully"""

    mocker.patch.object(repo, "_verify_gist_exists", return_value=False)

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_token"

    # Mock 404 response
    mock_response = mocker.Mock()
    mock_response.status_code = 404

    mock_delete = mocker.patch(
        "snipster.repositories.sql_model_repository.httpx.delete"
    )
    mock_delete.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=mocker.Mock(), response=mock_response
    )

    snippet = snippet_factory()
    repo.add_gist(snippet.id, "https://api.github.com/gists/test", is_public=True)

    repo.delete_gist(snippet.id)

    gist = repo.get_gist(snippet.id)
    assert gist is None


def test_delete_gist_github_500_error(repo, mocker, snippet_factory):
    """Test delete_gist raises error on non-404 HTTP status errors"""

    mocker.patch.object(repo, "_verify_gist_exists", return_value=True)

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_token"

    # Mock 500 response
    mock_response = mocker.Mock()
    mock_response.status_code = 500

    mock_delete = mocker.patch(
        "snipster.repositories.sql_model_repository.httpx.delete"
    )
    mock_delete.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error", request=mocker.Mock(), response=mock_response
    )

    snippet = snippet_factory()
    repo.add_gist(snippet.id, "https://api.github.com/gists/test", is_public=True)

    with pytest.raises(RepositoryError, match="GitHub deletion failed"):
        repo.delete_gist(snippet.id)

    gist = repo.get_gist(snippet.id)
    assert gist is not None


def test_delete_gist_connection_error(repo, mocker, snippet_factory):
    """Test delete_gist handles connection errors"""

    mocker.patch.object(repo, "_verify_gist_exists", return_value=True)

    mock_config = mocker.patch("snipster.repositories.sql_model_repository.config")
    mock_config.return_value = "test_token"

    mock_delete = mocker.patch(
        "snipster.repositories.sql_model_repository.httpx.delete"
    )
    mock_delete.side_effect = httpx.ConnectError("Connection refused")

    snippet = snippet_factory()
    repo.add_gist(snippet.id, "https://api.github.com/gists/test", is_public=True)

    with pytest.raises(RepositoryError, match="Cannot connect to GitHub"):
        repo.delete_gist(snippet.id)

    gist = repo.get_gist(snippet.id)
    assert gist is not None


def test_list_gist(repo, mocker):
    """Test list all gists"""

    snippet1 = Snippet(title="Test1", code="print('Test1')")
    snippet2 = Snippet(title="Test2", code="print('Test2')")

    repo.add(snippet1)
    repo.add(snippet2)

    repo.add_gist(snippet1.id, "https://api.github.com/gists/test1", is_public=True)
    repo.add_gist(snippet2.id, "https://api.github.com/gists/test2", is_public=True)

    mocker.patch.object(repo, "_verify_gist_exists", return_value=True)

    all_gists = repo.list_gist()

    assert len(all_gists) == 2


def test_list_gist_fails_with_http_error(repo, mocker):
    """Test list_gist which fails with HTTP Error"""

    mock_logger = mocker.patch("snipster.repositories.sql_model_repository.logger")

    snippet1 = Snippet(title="Test1", code="print('Test1')")
    repo.add(snippet1)
    repo.add_gist(snippet1.id, "https://api.github.com/gists/test1", is_public=True)

    mocker.patch.object(
        repo, "_verify_gist_exists", side_effect=httpx.HTTPError("Connection failed")
    )

    gists = repo.list_gist()
    assert len(gists) == 1
    # gist status remains unchanged
    assert gists[0].status == GistStatus.ACTIVE
    mock_logger.error.assert_called()
    err_msg = mock_logger.error.call_args_list[0]
    assert "Failed to reconcile gist" in str(err_msg)


def test_list_gist_fails_with_sqlalchemy_error(repo, mocker):
    """Test list_gist which fails with SQLAlchemy Error"""

    mock_logger = mocker.patch("snipster.repositories.sql_model_repository.logger")

    snippet1 = Snippet(title="Test1", code="print('Test1')")
    repo.add(snippet1)
    repo.add_gist(snippet1.id, "https://api.github.com/gists/test1", is_public=True)

    mocker.patch.object(
        repo, "_verify_gist_exists", side_effect=SQLAlchemyError("Repository error")
    )

    gists = repo.list_gist()
    assert len(gists) == 1
    # gist status remains unchanged
    assert gists[0].status == GistStatus.ACTIVE
    mock_logger.error.assert_called()
    err_msg = mock_logger.error.call_args_list[0]
    assert "Failed to reconcile gist" in str(err_msg)


def test_list_gist_fails_with_operational_error(repo, mocker):
    """Test list_gist which fails with Operational Error"""

    mock_logger = mocker.patch("snipster.repositories.sql_model_repository.logger")

    snippet1 = Snippet(title="Test1", code="print('Test1')")
    repo.add(snippet1)
    repo.add_gist(snippet1.id, "https://api.github.com/gists/test1", is_public=True)

    mocker.patch.object(
        repo,
        "_verify_gist_exists",
        side_effect=OperationalError(
            statement="SELECT * FROM gist", params={}, orig=Exception("Connection lost")
        ),
    )

    gists = repo.list_gist()
    assert len(gists) == 1
    # gist status remains unchanged
    assert gists[0].status == GistStatus.ACTIVE
    mock_logger.error.assert_called()
    err_msg = mock_logger.error.call_args_list[0]
    assert "Failed to reconcile gist" in str(err_msg)


@pytest.mark.parametrize(
    "error_scenarios",
    [
        "add",
        "list",
        "get",
        "delete",
        "search",
        "toggle_favourite",
        "tags",
        "get_gist",
        "list_gist",
        "delete_gist",
    ],
)
def test_sql_repo_operational_errors_logged(repo, mocker, error_scenarios):
    """Test that all sql repo db operations log OperationalError properly"""
    mock_session = mocker.patch("snipster.database_manager.Session")

    snippet1 = Snippet(title="first", code="code1")

    if error_scenarios == "add":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.add(snippet1)
    elif error_scenarios == "list":
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.list()
    elif error_scenarios == "get":
        mock_session.return_value.__enter__.return_value.get.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.get(1)
    elif error_scenarios == "delete":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.delete(1)
    elif error_scenarios == "search":
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.search("test")
    elif error_scenarios == "toggle_favourite":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.toggle_favourite(1)
    elif error_scenarios == "tags":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.tags(1, "test")
    elif error_scenarios == "get_gist":
        repo.add(snippet1)
        mocker.patch.object(repo, "_verify_gist_exists", return_value=False)
        mocker.patch("snipster.repositories.sql_model_repository.httpx.post")
        mock_session.return_value.__enter__.return_value.get.side_effect = [
            snippet1,
            OperationalError("Mock DB error", None, None),
        ]
        with pytest.raises(DatabaseConnectionError):
            repo.get_gist(1)
    elif error_scenarios == "delete_gist":
        repo.add(snippet1)
        mocker.patch.object(repo, "_verify_gist_exists", return_value=True)
        mocker.patch("snipster.repositories.sql_model_repository.httpx.delete")
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(DatabaseConnectionError):
            repo.delete_gist(1)
    elif error_scenarios == "list_gist":
        repo.add(snippet1)
        repo.add_gist(snippet1.id, "https://api.github.com/gists/test1", is_public=True)
        mocker.patch.object(
            repo.db_manager,
            "select_all",
            side_effect=OperationalError(
                statement="SELECT * FROM gist",
                params={},
                orig=Exception("Connection lost"),
            ),
        )
        with pytest.raises(DatabaseConnectionError):
            repo.list_gist()


@pytest.mark.parametrize(
    "error_scenarios",
    [
        "add",
        "list",
        "get",
        "delete",
        "search",
        "toggle_favourite",
        "tags",
        "get_gist",
        "add_gist",
        "delete_gist",
        "list_gist",
        "_fetch_gist",
    ],
)
def test_sql_repo_sqlalchemy_errors_logged(repo, mocker, error_scenarios):
    """Test that all sql repo db operations log SQLAlchemyError properly"""
    mock_session = mocker.patch("snipster.database_manager.Session")

    snippet1 = Snippet(title="first", code="code1")

    if error_scenarios == "add":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.add(snippet1)
    elif error_scenarios == "list":
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.list()
    elif error_scenarios == "get":
        mock_session.return_value.__enter__.return_value.get.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.get(1)
    elif error_scenarios == "delete":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.delete(1)
    elif error_scenarios == "search":
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.search("test")
    elif error_scenarios == "toggle_favourite":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.toggle_favourite(1)
    elif error_scenarios == "tags":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.tags(1, "test1")
    elif error_scenarios == "get_gist":
        repo.add(snippet1)
        mocker.patch.object(repo, "_verify_gist_exists", return_value=True)
        mocker.patch("snipster.repositories.sql_model_repository.httpx.get")
        mock_session.return_value.__enter__.return_value.get.side_effect = [
            snippet1,
            SQLAlchemyError("Mock DB error", None, None),
        ]
        with pytest.raises(RepositoryError):
            repo.get_gist(1)
    elif error_scenarios == "add_gist":
        repo.add(snippet1)
        mocker.patch.object(repo, "_verify_gist_exists", return_value=True)
        mocker.patch.object(
            repo, "_post_gist_on_github", return_value="http://gist.github.com/test"
        )
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            SQLAlchemyError("Mock DB error", None, None),
        )
        with pytest.raises(RepositoryError):
            repo.add_gist(snippet_id=1, gist_url="test", is_public=True)
    elif error_scenarios == "delete_gist":
        repo.add(snippet1)
        mocker.patch.object(repo, "_verify_gist_exists", return_value=True)
        mocker.patch("snipster.repositories.sql_model_repository.httpx.delete")
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo.delete_gist(1)
    elif error_scenarios == "_fetch_gist":
        mock_session.return_value.__enter__.return_value.get.side_effect = (
            SQLAlchemyError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            repo._fetch_gist_unchecked(1)
    elif error_scenarios == "list_gist":
        repo.add(snippet1)
        repo.add_gist(snippet1.id, "https://api.github.com/gists/test1", is_public=True)
        mocker.patch.object(
            repo.db_manager, "select_all", side_effect=SQLAlchemyError("Mock DB error")
        )
        with pytest.raises(RepositoryError):
            repo.list_gist()
