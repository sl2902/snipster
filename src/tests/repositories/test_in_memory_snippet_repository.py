import pytest

from snipster.models import Snippet
from snipster.repositories.in_memory_repository import InMemorySnippetRepository


@pytest.fixture
def repo():
    return InMemorySnippetRepository()


@pytest.fixture
def snippet_factory(repo):
    """Factory for creating test snippets"""

    def _create_snippet(title="test code", code="print('hello test')"):
        snippet = Snippet(title=title, code=code)
        repo.add(snippet)
        return snippet

    return _create_snippet


def test_add_and_get_snippet(repo, snippet_factory):
    """Test adding a snippet and retrieving it"""
    snippet = snippet_factory()
    repo.add(snippet)

    retrieved = repo.get(1)
    assert retrieved is not None
    assert retrieved == snippet


def test_add_multiple_snippets(repo):
    """Test adding multiple snippets with auto-incrementing IDs"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")

    all_snippets = [snippet1, snippet2]
    for snippet in all_snippets:
        repo.add(snippet)

    assert repo.get(1) == snippet1
    assert repo.get(2) == snippet2
    assert len(repo.list()) == len(all_snippets)


def test_list_empty_repo(repo):
    """Test listing snippets from empty repository"""
    assert len(repo.list()) == 0
    assert repo.list() == []


def test_list_returns_all_snippets(repo):
    """Test that list returns all added snippets"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")

    all_snippets = [snippet1, snippet2]
    for snippet in all_snippets:
        repo.add(snippet)

    all_snippets = repo.list()
    assert len(all_snippets) == 2
    assert all_snippets[0] in all_snippets
    assert all_snippets[1] in all_snippets


def test_get_non_existing_snippet(repo):
    """Test getting a non-existent snippet returns None"""
    assert repo.get(999) is None


def test_delete_existing_snippet(repo, snippet_factory):
    """Test deleting an existing snippet"""
    _ = snippet_factory()
    repo.delete(1)

    assert repo.get(1) is None
    assert len(repo.list()) == 0


def test_delete_non_existent_snippet_raises_error(repo):
    """Test that deleting non-existent snippet raises KeyError"""
    with pytest.raises(KeyError, match="Snippet with id 1 not found"):
        repo.delete(1)


def test_add_after_delete_increments_id(repo):
    """Test that IDs continue incrementing after deletion"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")

    repo.add(snippet1)
    repo.delete(1)
    repo.add(snippet2)

    assert repo.get(2) == snippet2
    assert repo.get(1) is None
