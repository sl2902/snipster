import pytest
from sqlalchemy.exc import OperationalError

from snipster.database_manager import DatabaseManager
from snipster.models import Language, Snippet


@pytest.fixture(scope="function")
def db_manager():
    db_manager = DatabaseManager(db_url="sqlite:///:memory:")
    db_manager.create_db_and_models()
    yield db_manager
    db_manager.engine.dispose()


def test_insert_records(db_manager):
    snippet = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    n_rows = db_manager.insert_records(Snippet, [snippet])

    assert n_rows == 1


def test_insert_duplicate_records(db_manager):
    snippet1 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    snippet2 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    snippet3 = Snippet(
        title="For Loop",
        code="for i in range(10):\n    print(i)",
        language=Language.PYTHON,
        tags="loops, basics",
    )

    n_rows = 3
    n_dups = 1
    n_rows_inserted = db_manager.insert_records(Snippet, [snippet1, snippet2, snippet3])

    assert n_rows_inserted == 2
    assert n_rows - n_rows_inserted - n_dups == 0


def test_insert_records_logs_ops_error(db_manager, mocker):
    mock_logger = mocker.patch("snipster.database_manager.logger")
    db_manager.engine.dispose()
    snippet1 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    with pytest.raises(OperationalError):
        _ = db_manager.insert_records(Snippet, [snippet1])
    mock_logger.error.assert_called_once()


def test_select_by_snippet_id(db_manager):
    snippet1 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    db_manager.insert_records(Snippet, [snippet1])

    result = db_manager.select_by_snippet_id(Snippet, id=1)
    assert result.id == 1


def test_select_by_snippet_id_no_records(db_manager):
    result = db_manager.select_by_snippet_id(Snippet, id=1)
    assert result is None


def test_select_by_id_logs_ops_error(db_manager, mocker):
    mock_logger = mocker.patch("snipster.database_manager.logger")
    db_manager.engine.dispose()
    _ = db_manager.select_by_snippet_id(Snippet, id=1)
    mock_logger.error.assert_called_once()


def test_select_all(db_manager):
    snippet1 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    snippet2 = Snippet(
        title="For Loop",
        code="for i in range(10):\n    print(i)",
        language=Language.PYTHON,
        tags="loops, basics",
    )

    db_manager.insert_records(Snippet, [snippet1, snippet2])

    results = db_manager.select_all(Snippet)

    assert len(results) == 2
    assert results[1].title == "For Loop"


def test_select_all_logs_ops_error(db_manager, mocker):
    mock_logger = mocker.patch("snipster.database_manager.logger")
    db_manager.engine.dispose()
    _ = db_manager.select_all(Snippet)
    mock_logger.error.assert_called_once()
