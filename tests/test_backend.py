import pytest

from snipster.repositories.backend import create_repository
from snipster.repositories.in_memory_repository import InMemorySnippetRepository
from snipster.repositories.json_repository import JSONSnippetRepository
from snipster.repositories.sql_model_repository import SQLModelRepository


@pytest.fixture
def sql_repo(mocker):
    """Create SQLModelRepository"""
    mocker.patch(
        "snipster.repositories.backend.config", return_value="sqlite:///:memory:"
    )
    repo = create_repository("sql")
    yield repo


def test_create_memory_repository():
    """Test creating in-memory repository"""
    repo = create_repository("memory")

    assert isinstance(repo, InMemorySnippetRepository)


def test_create_sql_repository(sql_repo):
    """Test creating sql repository"""

    assert isinstance(sql_repo, SQLModelRepository)

    sql_repo.db_manager.engine.dispose()


def test_create_json_repository():
    """Test creating json repository"""
    repo = create_repository("json")

    assert isinstance(repo, JSONSnippetRepository)


def test_repo_object_uses_default():
    """Test repo object uses default"""
    repo = create_repository()

    assert isinstance(repo, SQLModelRepository)

    repo.db_manager.engine.dispose()


def test_unknown_repository():
    """Test unknown repository"""
    with pytest.raises(ValueError):
        create_repository("unknown_db")
