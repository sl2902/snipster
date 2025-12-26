import pytest

from snipster import Snippet
from snipster.repositories.json_repository import JSONSnippetRepository


@pytest.fixture
def repo(tmp_path):
    yield JSONSnippetRepository(snippet_dir=str(tmp_path))


@pytest.fixture
def snippet_factory(repo):
    """Factory for creating test snippets"""

    def _create_snippet(title="test code", code="print('hello test')"):
        snippet = Snippet(title=title, code=code)
        repo.add(snippet)
        return snippet

    return _create_snippet


# @pytest.fixture(scope="function")
# def snippet_filepath(tmp_path_factory):
#     fn = tmp_path_factory.mktemp("data")
#     return fn


def test_create_snippet_file(repo, snippet_factory):
    """Test file creation and write snippets to it"""
    _ = snippet_factory()
    snippet_dict = repo._load_existing_snippets_to_memory()

    assert snippet_dict is not None
    assert len(snippet_dict) == 1


def test_add_and_get_snippet(repo, snippet_factory):
    """Test adding a snippet and retrieving it"""
    snippet = snippet_factory()

    retrieved = repo.get(1)
    assert retrieved is not None
    assert retrieved.title == snippet.title
    assert retrieved.code == snippet.code


def test_add_multiple_snippets(repo):
    """Test adding multiple snippets with auto-incrementing IDs"""
    snippet1 = Snippet(title="first", code="code1")
    snippet2 = Snippet(title="second", code="code2")

    all_snippets = [snippet1, snippet2]
    for snippet in all_snippets:
        repo.add(snippet)

    assert len(repo.list()) == len(all_snippets)
    assert repo.get(1).title == snippet1.title
    assert repo.get(2).title == snippet2.title


def test_add_duplicate_snippets(repo, snippet_factory):
    """Test that duplicate snippets (same title+language) are rejected"""
    for _ in range(2):
        snippet = snippet_factory()

    all_snippets = repo.list()
    assert len(all_snippets) == 1
    assert all_snippets[0].title == snippet.title


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
    """Test that deleting non-existent snippet doesn't raise error"""
    snippet_factory()

    repo.delete(999)

    all_snippets = repo.list()
    assert len(all_snippets) == 1


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
