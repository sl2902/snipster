import pytest

from snipster import Language, Snippet
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


def test_search_term_not_found_error(repo, snippet_factory):
    """Test ValueError due to term not found"""
    snippet1 = snippet_factory()

    repo.add(snippet1)

    with pytest.raises(ValueError):
        repo.search("missing_term")


def test_toggle_favourite(repo, snippet_factory):
    """Test toggle snippet `favourite`"""
    snippet_factory()

    snippet = repo.get(1)
    assert snippet.favorite is False

    repo.toggle_favourite(1)
    snippet = repo.get(1)
    assert snippet.favorite is True

    repo.toggle_favourite(1)
    snippet = repo.get(1)
    assert snippet.favorite is False

    with pytest.raises(KeyError):
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

    with pytest.raises(KeyError):
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
