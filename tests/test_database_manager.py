import pytest
from sqlalchemy.exc import (
    IntegrityError,
    MultipleResultsFound,
    NoResultFound,
    OperationalError,
)

from snipster import Language, Snippet
from snipster.database_manager import DatabaseManager
from snipster.exceptions import (
    DuplicateSnippetError,
    RepositoryError,
    SnippetNotFoundError,
)


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


class TestConstructorValidation:
    """Group all constructor-related tests"""

    def test_uses_config_when_db_url_is_none(self, mocker):
        """Test that DATABASE_URL is read from config when db_url=Non"""
        mock_config = mocker.patch("snipster.database_manager.config")
        mock_config.return_value = "sqlite:///test_from_env.db"

        manager = DatabaseManager()

        mock_config.assert_called_once_with(
            "DATABASE_URL", default="sqlite:///snippets.db"
        )
        assert manager.db_url == "sqlite:///test_from_env.db"

        manager.engine.dispose()

    def test_explicit_db_url_overrides_config(self, mocker):
        """Test that explicit db_url takes precedence over config"""
        mock_config = mocker.patch("snipster.database_manager.config")

        manager = DatabaseManager(db_url="sqlite:///:memory:")

        mock_config.assert_not_called()
        assert manager.db_url == "sqlite:///:memory:"

        manager.engine.dispose()

    def test_constructor_rejects_empty_url(self):
        """Test that None db_url is rejected"""
        with pytest.raises(ValueError, match="db_url cannot be empty"):
            DatabaseManager(db_url="")

    def test_constructor_rejects_whitespace_url(self):
        """Test that None db_url is rejected"""
        with pytest.raises(ValueError, match="db_url cannot be empty"):
            DatabaseManager(db_url="  ")


class TestInsertSingleRecord:
    """Group all single insert-related tests"""

    def test_insert_record(self, db_manager, sample_snippet):
        is_inserted = db_manager.insert_record(Snippet, sample_snippet)
        actual = db_manager.select_by_id(Snippet, 1)

        assert is_inserted is True
        assert actual.title == "Hello World"
        assert actual.language == "Python"

    def test_insert_duplicate_record(self, db_manager):
        with pytest.raises(DuplicateSnippetError):
            for _ in range(2):
                snippet = Snippet(
                    title="Function Definition",
                    code="def greet(name):\n    return f'Hello, {name}!'",
                    language=Language.PYTHON,
                    tags="function, basics",
                )
                db_manager.insert_record(Snippet, snippet)

        actual = db_manager.select_all(Snippet)
        assert len(actual) == 1


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

        result = db_manager.select_by_id(Snippet, pk=inserted_id)

        assert result is not None
        assert result.id == inserted_id
        assert result.title == "Hello World"

    def test_select_by_id_no_records(self, db_manager):
        result = db_manager.select_by_id(Snippet, pk=1)
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

    def test_select_filter_by_title_ignorecase(self, db_manager, sample_snippet):
        db_manager.insert_records(Snippet, [sample_snippet])
        all_snippets = db_manager.select_with_filter(Snippet, col="title", term="world")

        assert len(all_snippets) == 1
        assert all_snippets[0].title == "Hello World"

    def test_select_filter_by_code_ignorecase(self, db_manager, sample_snippet):
        db_manager.insert_records(Snippet, [sample_snippet])
        all_snippets = db_manager.select_with_filter(Snippet, col="code", term="hello")

        assert len(all_snippets) == 1
        assert all_snippets[0].code == "print('Hello, World!')"

    def test_select_filter_by_description_ignorecase(self, db_manager, sample_snippet):
        db_manager.insert_records(Snippet, [sample_snippet])
        all_snippets = db_manager.select_with_filter(
            Snippet, col="description", term="HELLO"
        )

        assert len(all_snippets) == 1
        assert all_snippets[0].description == "Basic Python hello world"

    def test_select_filter_by_empty_term(self, db_manager, multiple_snippets):
        db_manager.insert_records(Snippet, multiple_snippets)
        select_all_snippets = db_manager.select_all(Snippet)
        filter_all_snippets = db_manager.select_with_filter(
            Snippet, col="description", term=""
        )

        assert len(select_all_snippets) == len(filter_all_snippets)

    def test_select_filter_with_non_existent_column(
        self, mocker, db_manager, sample_snippet
    ):
        db_manager.insert_records(Snippet, [sample_snippet])

        with pytest.raises(ValueError):
            db_manager.select_with_filter(Snippet, col="test", term="")


class TestDeleteSingleRecordOperations:
    """Group all delete-related tests"""

    def test_delete_single_record(self, db_manager, sample_snippet):
        db_manager.insert_record(Snippet, sample_snippet)

        snippet = db_manager.select_by_id(Snippet, 1)
        assert len([snippet]) == 1

        db_manager.delete_record(Snippet, snippet.id)
        snippet = db_manager.select_by_id(Snippet, 1)

        assert snippet is None

        snippet = db_manager.select_by_id(Snippet, 1)
        assert snippet is None

    def test_delete_no_record(self, mocker, db_manager):
        mock_session = mocker.patch("snipster.database_manager.Session")

        mock_session.return_value.__enter__.return_value.exec.return_value.one.side_effect = NoResultFound(
            "Mock DB error", None, None
        )

        with pytest.raises(SnippetNotFoundError):
            db_manager.delete_record(Snippet, 1)

    def test_delete_multi_result_records(self, mocker, db_manager):
        mock_session = mocker.patch("snipster.database_manager.Session")

        mock_session.return_value.__enter__.return_value.exec.return_value.one.side_effect = MultipleResultsFound(
            "Mock DB error", None, None
        )

        with pytest.raises(MultipleResultsFound):
            db_manager.delete_record(Snippet, 1)


class TestUpdateSingleRecordOperatons:
    """Group all update-related tests"""

    def test_update_single_record(self, db_manager, sample_snippet):
        db_manager.insert_record(Snippet, sample_snippet)

        snippet = db_manager.select_by_id(Snippet, 1)
        assert snippet is not None
        assert snippet.favorite is False

        db_manager.update(Snippet, 1, col="favorite", value=True)
        snippet = db_manager.select_by_id(Snippet, 1)
        assert snippet.favorite is True

        db_manager.update(Snippet, 1, col="favorite", value=False)
        snippet = db_manager.select_by_id(Snippet, 1)
        assert snippet.favorite is False

    def test_update_with_non_existent_column(self, db_manager):
        with pytest.raises(ValueError):
            db_manager.update(Snippet, 1, col="dummy", value=False)

    def test_update_no_record(self, mocker, db_manager):
        mock_session = mocker.patch("snipster.database_manager.Session")

        mock_session.return_value.__enter__.return_value.exec.return_value.one.side_effect = NoResultFound(
            "Mock DB error", None, None
        )

        with pytest.raises(SnippetNotFoundError):
            db_manager.update(Snippet, 999, col="favorite", value=True)


@pytest.mark.parametrize(
    "error_scenarios",
    [
        "delete_record",
        "insert_record",
        "insert_records",
        "select_by_id",
        "select_all",
        "select_with_filter",
        "update",
    ],
)
def test_operational_errors_are_logged(
    db_manager, mocker, sample_snippet, error_scenarios
):
    """Test that all DB operations log OperationalError properly"""
    mock_logger = mocker.patch("snipster.database_manager.logger")
    mock_session = mocker.patch("snipster.database_manager.Session")

    if error_scenarios == "delete_record":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            db_manager.delete_record(Snippet, 1)
    elif error_scenarios == "insert_records":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        db_manager.insert_records(Snippet, [sample_snippet])
    elif error_scenarios == "insert_record":
        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            IntegrityError("Mock DB error", None, None)
        )
        with pytest.raises(DuplicateSnippetError):
            db_manager.insert_record(Snippet, sample_snippet)
        mock_logger.warning.assert_called_once()

        mock_session.return_value.__enter__.return_value.commit.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            db_manager.insert_record(Snippet, sample_snippet)
    elif error_scenarios == "select_by_id":
        mock_session.return_value.__enter__.return_value.get.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            db_manager.select_by_id(Snippet, pk=1)
    elif error_scenarios == "select_all":
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            db_manager.select_all(Snippet)
    elif error_scenarios == "select_with_filter":
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            db_manager.select_with_filter(Snippet, col="title")
    elif error_scenarios == "update":
        mock_session.return_value.__enter__.return_value.exec.side_effect = (
            OperationalError("Mock DB error", None, None)
        )
        with pytest.raises(RepositoryError):
            db_manager.update(Snippet, pk=1, col="favorite", value=True)

    if error_scenarios != "insert_record":
        mock_logger.error.assert_called_once()
