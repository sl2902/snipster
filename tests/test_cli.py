import re

import pytest
from typer.testing import CliRunner

from snipster import Language, Snippet
from snipster.cli import app

runner = CliRunner(env={"NO_COLOR": "1"})


@pytest.fixture
def mock_repo(mocker):
    """Mock repository for CLI tests"""
    mock = mocker.MagicMock()
    mocker.patch("snipster.cli.create_reposistory", return_value=mock)
    return mock


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_add_snippet(mock_repo):
    """Test adding a snippet via CLI"""
    result = runner.invoke(
        app, ["add", "--title", "Test snippet", "--code", "print('hello')"]
    )

    assert result.exit_code == 0
    print(result.stdout)
    assert "Snippet" in result.stdout
    mock_repo.add.assert_called_once()


def test_list_snippet(mock_repo):
    """Test listing snippets"""
    snippet = Snippet(id=1, title="Test", code="code", language=Language.PYTHON)
    mock_repo.list.return_value = [snippet]

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "Test" in result.stdout


def test_list_empty_snippet(mock_repo):
    """Test listing when no snippets exist"""
    mock_repo.list.return_value = []

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No snippets found" in result.stdout


def test_get_snippet_found(mock_repo):
    """Test getting a snippet by ID"""
    snippet = snippet = Snippet(
        id=1, title="Test", code="print('hello')", language=Language.PYTHON
    )

    mock_repo.get.return_value = snippet

    result = runner.invoke(app, ["get", "--snippet-id", 1])

    assert result.exit_code == 0
    assert "Details of Snippet" in result.stdout


def test_get_snippet_not_found(mock_repo):
    """Test getting non-existent snippet"""
    mock_repo.get.return_value = None
    result = runner.invoke(app, ["get", "--snippet-id", 1])

    assert result.exit_code == 1
    assert "No snippet found" in result.stdout


def test_delete_snippet(mock_repo):
    """Test deleting snippet"""
    snippet = snippet = Snippet(
        id=1, title="Test", code="print('hello')", language=Language.PYTHON
    )

    mock_repo.delete.return_value = snippet
    result = runner.invoke(app, ["delete", "--snippet-id", 1])

    assert result.exit_code == 0
    assert "deleted" in result.stdout


def test_delete_snippet_not_found(mock_repo):
    """Test deleting non-existent snippet"""
    from sqlalchemy.exc import NoResultFound

    mock_repo.delete.side_effect = NoResultFound()

    result = runner.invoke(app, ["delete", "--snippet-id", 1])
    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_delete_snippet_operational_error(mock_repo):
    """Test deleting Operational error"""
    from sqlalchemy.exc import OperationalError

    mock_repo.delete.side_effect = OperationalError("Mock DB Error", None, None)

    result = runner.invoke(app, ["delete", "--snippet-id", 1])
    assert result.exit_code == 1
    assert "Operational Error" in result.stdout
    mock_repo.delete.assert_called_once_with(1)


def test_search_snippets(mock_repo):
    """Test searching snippets"""
    snippet = Snippet(id=1, title="Python Test", code="code", language=Language.PYTHON)
    mock_repo.search.return_value = [snippet]

    result = runner.invoke(app, ["search", "--term", "python"])

    assert result.exit_code == 0
    assert "Python" in result.stdout
    assert "Test" in result.stdout
    mock_repo.search.assert_called_once_with("python", language=None)


def test_search_snippets_no_match(mock_repo):
    """Test searching for non-existent terms in snippet"""
    mock_repo.search.side_effect = ValueError("No matches found")

    result = runner.invoke(app, ["search", "--term", "python"])

    assert result.exit_code == 1
    assert "No matches found" in strip_ansi(result.stdout)


def test_search_snippets_operational_error(mock_repo):
    """Test searching with Operational error"""
    from sqlalchemy.exc import OperationalError

    mock_repo.search.side_effect = OperationalError("Mock DB Error", None, None)

    result = runner.invoke(app, ["search", "--term", "python"])

    assert result.exit_code == 1
    assert "Operational Error" in strip_ansi(result.stdout)


def test_toggle_favourite_snippet(mock_repo):
    """Test toggle favourite snippet"""
    snippet = Snippet(id=1, title="Python Test", code="code", language=Language.PYTHON)
    mock_repo.toggle_favourite.return_value = [snippet]

    result = runner.invoke(app, ["toggle-favourite", "--snippet-id", 1])

    assert result.exit_code == 0
    assert "Snippet '1' favourited" in result.stdout


def test_add_with_tags(mock_repo):
    """Test adding snippet with multiple tags"""
    result = runner.invoke(
        app,
        ["tags", "--snippet-id", 1, "--tags", "test1,test2", "--no-remove", "--sort"],
    )

    assert result.exit_code == 0
    mock_repo.tags.assert_called_once_with(1, "test1", "test2", remove=False, sort=True)
    assert "Tags added" in result.stdout


def test_remove_tags(mock_repo):
    """Test removing tags from snippet"""
    result = runner.invoke(
        app, ["tags", "--snippet-id", "1", "--tags", "test1", "--remove"]
    )
    assert result.exit_code == 0
    mock_repo.tags.assert_called_once_with(1, "test1", remove=True, sort=True)


def test_tags_not_found(mock_repo):
    """Test tagging non-existent snippet"""
    from snipster.exceptions import SnippetNotFoundError

    mock_repo.tags.side_effect = SnippetNotFoundError("Not found")

    result = runner.invoke(
        app, ["tags", "--snippet-id", "999", "--tags", "test", "--no-remove", "--sort"]
    )

    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()
