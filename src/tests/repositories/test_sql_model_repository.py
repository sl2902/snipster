import pytest

from snipster.models import Snippet
from snipster.repositories.sql_model_repository import SQLModelRepository


@pytest.fixture
def repo():
    repository = SQLModelRepository(db_url="sqlite:///:memory:")
    yield repository
    repository.db_manager.engine.dispose()


@pytest.fixture
def snippet_factory(repo):
    def _create_snippet(title="test code", code="print('hello test')"):
        snippet = Snippet(title=title, code=code)
        repo.add(snippet)
        return snippet

    return _create_snippet


def test_add_snippet(repo, snippet_factory):
    expected = snippet_factory()
    actual = repo.get(1)
    assert actual is not None
    assert actual.title == expected.title
    assert actual.code == expected.code


def test_add_duplicate_snippet(repo, snippet_factory):
    for _ in range(2):
        snippet = snippet_factory()
        repo.add(snippet)

    all_snippets = repo.list()
    assert len(all_snippets) == 1
    assert all_snippets[0].title == snippet.title
