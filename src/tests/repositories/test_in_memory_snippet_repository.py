import pytest

from snipster.models import Snippet
from snipster.repositories.in_memory_repository import InMemorySnippetRepository


@pytest.fixture
def repo():
    return InMemorySnippetRepository()


@pytest.fixture
def add_snippet(repo):
    snippet = Snippet(title="test code", code="print('hello test)")
    repo.add(snippet)
    return snippet


@pytest.fixture
def snippet_id_1():
    return 1


@pytest.fixture
def snippet_id_2():
    return 2


def test_add_snippet(repo, add_snippet):
    assert repo.get(1) is not None
    assert repo.get(1) == add_snippet


def test_list_snippet(repo, add_snippet):
    assert len(repo.list()) == 1
    assert repo.list()[0] == add_snippet


def test_empty_list(repo):
    assert len(repo.list()) == 0


def test_get_existing_snippet(repo, add_snippet, snippet_id_1):
    assert repo.get(snippet_id_1) == add_snippet


def test_get_non_existing_snippet(repo, add_snippet, snippet_id_2):
    assert repo.get(snippet_id_2) is None


def test_get_empty_repo(repo, snippet_id_1):
    assert repo.get(snippet_id_1) is None


def test_delete_non_existent_snippet(repo, snippet_id_1):
    with pytest.raises(KeyError, match=f"Snippet with id {snippet_id_1} not found"):
        repo.delete(snippet_id_1)


def test_delete_existing_snippet(repo, add_snippet, snippet_id_1):
    repo.delete(snippet_id_1)

    assert repo.get(snippet_id_1) is None
