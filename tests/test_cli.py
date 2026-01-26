import re

import pytest
from typer.testing import CliRunner

from snipster import Language, Snippet
from snipster.cli import app
from snipster.exceptions import RepositoryError, SnippetNotFoundError

runner = CliRunner()


@pytest.fixture
def mock_repo(mocker):
    """Mock repository for CLI tests"""
    mock = mocker.MagicMock()
    mocker.patch("snipster.cli.create_repository", return_value=mock)
    yield mock


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m|\[.*?\]", "", text)


def test_add_snippet(mock_repo):
    """Test adding a snippet via CLI"""
    result = runner.invoke(
        app,
        [
            "add",
            "--title",
            "Test snippet",
            "--code",
            "print('hello')",
            "--language",
            "Python",
        ],
    )

    assert result.exit_code == 0
    assert "Snippet" in result.stdout
    mock_repo.add.assert_called_once()


def test_add_command_model_validation_error(mock_repo, mocker):
    """Test add command handles model validation error"""

    mock_console = mocker.patch("snipster.cli.console")

    result = runner.invoke(
        app, ["add", "--title", "Te", "--code", "print('test')", "--language", "Python"]
    )

    assert result.exit_code == 1
    mock_console.print.assert_called()

    call_args = str(mock_console.print.call_args[0][0])
    assert "Model validation failed" in call_args


def test_add_with_all_options(mock_repo):
    """Test adding a snippet with all options"""
    result = runner.invoke(
        app,
        [
            "add",
            "--title",
            "Test",
            "--code",
            "print('hello')",
            "--description",
            "A test snippet",
            "--language",
            "Python",
            "--tags",
            "test,example",
        ],
    )

    assert result.exit_code == 0
    mock_repo.add.assert_called_once()
    call_args = mock_repo.add.call_args[0][0]
    assert call_args.tags == "test,example"


def test_list_snippet(mock_repo):
    """Test listing snippets"""
    snippet = Snippet(id=1, title="Test", code="code", language=Language.PYTHON)
    mock_repo.list.return_value = [snippet]

    result = runner.invoke(app, ["list-snippet"])

    assert result.exit_code == 0
    assert "Test" in strip_ansi(result.stdout)


def test_list_empty_snippet(mock_repo):
    """Test listing when no snippets exist"""
    mock_repo.list.return_value = []

    result = runner.invoke(app, ["list-snippet"])
    assert result.exit_code == 0
    assert "No snippets found" in strip_ansi(result.stdout)


def test_get_snippet_found(mock_repo):
    """Test getting a snippet by ID"""
    snippet = Snippet(
        id=1, title="Test", code="print('hello')", language=Language.PYTHON
    )

    mock_repo.get.return_value = snippet

    result = runner.invoke(app, ["get", "--snippet-id", 1])

    assert result.exit_code == 0
    assert "Details of Snippet" in strip_ansi(result.stdout)


def test_get_snippet_not_found(mock_repo):
    """Test getting non-existent snippet"""
    mock_repo.get.return_value = None
    result = runner.invoke(app, ["get", "--snippet-id", 1])

    assert result.exit_code == 1
    assert "No snippet found" in strip_ansi(result.stdout)


def test_delete_snippet(mock_repo):
    """Test deleting snippet"""
    snippet = Snippet(
        id=1, title="Test", code="print('hello')", language=Language.PYTHON
    )

    mock_repo.delete.return_value = snippet
    result = runner.invoke(app, ["delete", "--snippet-id", 1])

    assert result.exit_code == 0
    assert "deleted" in result.stdout


def test_delete_snippet_not_found(mock_repo):
    """Test deleting non-existent snippet"""
    mock_repo.delete.side_effect = SnippetNotFoundError()

    result = runner.invoke(app, ["delete", "--snippet-id", 1])
    assert result.exit_code == 1
    assert "not found" in strip_ansi(result.stdout)


def test_delete_snippet_operational_error(mock_repo):
    """Test deleting Operational error"""
    mock_repo.delete.side_effect = RepositoryError("Mock DB Error", None, None)

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


def test_search_with_language_filter(mock_repo):
    """Test searching with language filter"""
    snippet = Snippet(id=1, title="Test", code="code", language=Language.PYTHON)
    mock_repo.search.return_value = [snippet]

    result = runner.invoke(app, ["search", "--term", "test", "--language", "python"])

    assert result.exit_code == 0
    mock_repo.search.assert_called_once_with("test", language="python")


def test_search_snippets_no_match(mock_repo, mocker):
    """Test searching for non-existent terms in snippet"""
    mock_console = mocker.patch("snipster.cli.console")
    mock_repo.search.return_value = []

    result = runner.invoke(app, ["search", "--term", "python"])

    assert result.exit_code == 1
    mock_console.print.assert_called_once()
    call_args = str(mock_console.print.call_args[0][0])
    assert "No matches found" in call_args


def test_search_term_found_but_lang_not_found(mock_repo, mocker):
    """Test search with valid term but non-matching language returns empty list"""
    mock_console = mocker.patch("snipster.cli.console")
    mock_repo.search.return_value = []

    result = runner.invoke(
        app, ["search", "--term", "python", "--language", "javascript"]
    )

    assert result.exit_code == 1
    mock_console.print.assert_called_once()
    call_args = str(mock_console.print.call_args[0][0])
    assert "No matches found for term 'python' and language 'javascript'" in strip_ansi(
        call_args
    )


def test_search_snippets_operational_error(mock_repo):
    """Test searching with Operational error"""
    mock_repo.search.side_effect = RepositoryError("Mock DB Error", None, None)

    result = runner.invoke(app, ["search", "--term", "python"])

    assert result.exit_code == 1
    assert "Operational Error" in strip_ansi(result.output)


def test_toggle_favourite_snippet(mock_repo):
    """Test toggle favourite snippet"""
    snippet = Snippet(id=1, title="Python Test", code="code", language=Language.PYTHON)
    mock_repo.toggle_favourite.return_value = [snippet]

    result = runner.invoke(app, ["toggle-favourite", "--snippet-id", 1])

    assert result.exit_code == 0
    assert "Snippet '1' favourited" in result.stdout


def test_toggle_favourite_snippet_not_found(mock_repo):
    """Test toggle favourite SnippetNotFound error"""
    mock_repo.toggle_favourite.side_effect = SnippetNotFoundError("Not found")
    result = runner.invoke(app, ["toggle-favourite", "--snippet-id", 999])

    assert result.exit_code == 1
    assert "snippet '999' not found" in strip_ansi(result.stdout.lower())


def test_add_with_tags(mock_repo):
    """Test adding snippet with multiple tags"""
    result = runner.invoke(
        app,
        [
            "tags",
            "--snippet-id",
            1,
            "--tags-input",
            "test1,test2",
            "--no-remove",
            "--sort",
        ],
    )

    assert result.exit_code == 0
    mock_repo.tags.assert_called_once_with(1, "test1", "test2", remove=False, sort=True)
    assert "Tags added" in strip_ansi(result.stdout)


def test_remove_tags(mock_repo):
    """Test removing tags from snippet"""
    result = runner.invoke(
        app, ["tags", "--snippet-id", 1, "--tags-input", "test1", "--remove"]
    )
    assert result.exit_code == 0
    mock_repo.tags.assert_called_once_with(1, "test1", remove=True, sort=True)


def test_tags_not_found(mock_repo):
    """Test tagging non-existent snippet"""
    mock_repo.tags.side_effect = SnippetNotFoundError("Not found")

    result = runner.invoke(
        app,
        ["tags", "--snippet-id", 999, "--tags-input", "test", "--no-remove", "--sort"],
    )

    assert result.exit_code == 1
    assert "snippet '999' not found" in strip_ansi(result.stdout.lower())
