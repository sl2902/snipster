import pytest

from snipster.repositories.backend import create_repository
from snipster.repositories.in_memory_repository import InMemorySnippetRepository
from snipster.repositories.json_repository import JSONSnippetRepository
from snipster.repositories.sql_model_repository import SQLModelRepository


@pytest.fixture
def sql_repo(mocker):
    """Create SQLModelRepository"""

    def mock_config(key, default=None):
        config_values = {
            "DATABASE_URL": "sqlite:///:memory:",
            "REPOSITORY_TYPE": "sql",
        }
        return config_values.get(key, default)

    mocker.patch("snipster.repositories.backend.config", side_effect=mock_config)
    repo = create_repository("sql")
    yield repo
    repo.db_manager.engine.dispose()


def test_create_memory_repository():
    """Test creating in-memory repository"""
    repo = create_repository("memory")

    assert isinstance(repo, InMemorySnippetRepository)


def test_create_sql_repository(sql_repo):
    """Test creating sql repository"""

    assert isinstance(sql_repo, SQLModelRepository)


def test_create_json_repository(mocker, tmp_path):
    """Test creating json repository with custom path"""
    mocker.patch(
        "snipster.repositories.backend.config",
        side_effect=lambda key, default=None: str(tmp_path)
        if key == "JSON_DATA_DIR"
        else default,
    )

    repo = create_repository("json")

    assert isinstance(repo, JSONSnippetRepository)
    assert repo.sub_dir == str(tmp_path)


def test_repo_object_uses_default(mocker):
    """Test repo object uses default"""
    mocker.patch(
        "snipster.repositories.backend.config",
        side_effect=lambda key, default=None: {
            "REPOSITORY_TYPE": "sql",
            "DATABASE_URL": "sqlite:///:memory:",
        }.get(key, default),
    )

    repo = create_repository()

    assert isinstance(repo, SQLModelRepository)

    repo.db_manager.engine.dispose()


def test_unknown_repository():
    """Test unknown repository"""
    with pytest.raises(ValueError):
        create_repository("unknown_db")


@pytest.mark.parametrize(
    "repo_type,expected_class",
    [
        ("memory", InMemorySnippetRepository),
        ("MEMORY", InMemorySnippetRepository),
        ("Memory", InMemorySnippetRepository),
    ],
)
def test_create_repository_case_insensitive(repo_type, expected_class):
    """Test that repository type is case insensitive"""
    repo = create_repository(repo_type)

    assert isinstance(repo, expected_class)
