import pytest
from sqlalchemy.exc import OperationalError

from snipster.database_manager import DatabaseManager
from snipster.models import Language, Snippet


@pytest.fixture(scope="function")
def db_manager():
    db_manager = DatabaseManager(db_url="sqlite:///:memory:")
    yield db_manager
    db_manager.engine.dispose()


@pytest.fixture(scope="function")
def sample_snippet():
    """Factory for creating test snippets"""
    return Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )


@pytest.fixture(scope="function")
def multiple_snippets():
    """Factory for creating multiple test snippets"""
    return [
        Snippet(
            title="Hello World",
            code="print('Hello, World!')",
            description="Basic Python hello world",
            language=Language.PYTHON,
            tags="beginner, tutorial",
        ),
        Snippet(
            title="For Loop",
            code="for i in range(10):\n    print(i)",
            language=Language.PYTHON,
            tags="loops, basics",
        ),
    ]


@pytest.fixture(scope="function")
def multiple_snippets_with_duplicates():
    """Factory for creating multiple test snippets with duplicates"""
    return [
        Snippet(
            title="Hello World",
            code="print('Hello, World!')",
            description="Basic Python hello world",
            language=Language.PYTHON,
            tags="beginner, tutorial",
        ),
        Snippet(
            title="Hello World",
            code="print('Hello, World!')",
            description="Basic Python hello world",
            language=Language.PYTHON,
            tags="beginner, tutorial",
        ),
        Snippet(
            title="For Loop",
            code="for i in range(10):\n    print(i)",
            language=Language.PYTHON,
            tags="loops, basics",
        ),
        Snippet(
            title="For Loop",
            code="for i in range(10):\n    print(i)",
            language=Language.PYTHON,
            tags="loops, basics",
        ),
        Snippet(
            title="List Comprehension",
            code="squares = [x**2 for x in range(10)]",
            language=Language.PYTHON,
            tags="list, comprehension",
        ),
        Snippet(
            title="Dictionary Example",
            code="my_dict = {'key': 'value', 'number': 42}",
            language=Language.PYTHON,
            tags="dictionary, basics",
        ),
        Snippet(
            title="Function Definition",
            code="def greet(name):\n    return f'Hello, {name}!'",
            language=Language.PYTHON,
            tags="function, basics",
        ),
    ]


class TestInsertRecords:
    """Group all insert-related tests"""

    def test_insert_records(self, db_manager, sample_snippet):
        n_rows = db_manager.insert_records(Snippet, [sample_snippet])

        assert n_rows == 1

    def test_insert_duplicate_records(
        self, db_manager, multiple_snippets_with_duplicates
    ):
        n_rows = 7
        n_dups = 2
        n_rows_inserted = db_manager.insert_records(
            Snippet, multiple_snippets_with_duplicates
        )

        all_snippets = db_manager.select_all(Snippet)

        assert n_rows_inserted == len(
            all_snippets
        ), f"Database should contain exactly {n_rows} records"
        assert n_rows - n_rows_inserted - n_dups == 0
        titles = {s.title for s in all_snippets}
        assert titles == {
            "Hello World",
            "For Loop",
            "List Comprehension",
            "Dictionary Example",
            "Function Definition",
        }, "Should contain both unique snippets"

    def test_insert_batched_records(
        self, db_manager, multiple_snippets_with_duplicates
    ):
        n_rows = 7
        n_dups = 2
        n_rows_inserted = db_manager.insert_records(
            Snippet, multiple_snippets_with_duplicates, batch_size=3
        )

        all_snippets = db_manager.select_all(Snippet)

        assert n_rows_inserted == len(all_snippets)
        assert n_rows - n_rows_inserted - n_dups == 0

    def test_insert_empty_batch(self, db_manager):
        n_rows = 0
        n_dups = 0
        n_rows_inserted = db_manager.insert_records(Snippet, [])

        all_snippets = db_manager.select_all(Snippet)

        assert n_rows_inserted == len(all_snippets)
        assert n_rows - n_rows_inserted - n_dups == 0


class TestSelectOperations:
    """Group all select-related tests"""

    def test_select_by_id(self, db_manager, sample_snippet):
        db_manager.insert_records(Snippet, [sample_snippet])

        all_snippets = db_manager.select_all(Snippet)
        inserted_id = all_snippets[0].id

        result = db_manager.select_by_id(Snippet, id=inserted_id)

        assert result is not None
        assert result.id == inserted_id
        assert result.title == "Hello World"

    def test_select_by_id_no_records(self, db_manager):
        result = db_manager.select_by_id(Snippet, id=1)
        assert result is None

    def test_select_all(self, db_manager, multiple_snippets):
        db_manager.insert_records(Snippet, multiple_snippets)

        results = db_manager.select_all(Snippet)

        assert len(results) == 2
        assert results[1].title == "For Loop"

    def test_select_all_with_limit(self, db_manager, multiple_snippets):
        db_manager.insert_records(Snippet, multiple_snippets)

        results = db_manager.select_all(Snippet, limit=1)

        assert len(results) == 1
        assert results[0].title == "Hello World"


@pytest.mark.parametrize(
    "error_scenarios", ["insert_records", "select_by_id", "select_all"]
)
def test_operational_errors_are_logged(
    db_manager, mocker, sample_snippet, error_scenarios
):
    """Test that all DB operations log OperationalError properly"""
    mock_logger = mocker.patch("snipster.database_manager.logger")
    mock_session = mocker.patch("snipster.database_manager.Session")

    if error_scenarios == "insert_records":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        db_manager.insert_records(Snippet, [sample_snippet])
    elif error_scenarios == "select_by_id":
        mock_session.return_value.__enter__.return_value.get.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        db_manager.select_by_id(Snippet, id=1)
    else:
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        db_manager.select_all(Snippet)

    mock_logger.error.assert_called_once()
