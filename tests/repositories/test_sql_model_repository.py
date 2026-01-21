import pytest
from sqlalchemy.exc import (
    OperationalError,
)

from snipster import Language, Snippet
from snipster.exceptions import (
    DuplicateSnippetError,
    RepositoryError,
    SnippetNotFoundError,
)
from snipster.repositories.sql_model_repository import SQLModelRepository


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


@pytest.mark.parametrize(
    "error_scenarios",
    [
        "add",
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
        with pytest.raises(RepositoryError):
            repo.add(snippet1)
