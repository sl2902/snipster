"""Entrypoint into one of the 3 backends"""

from enum import StrEnum

from decouple import config

from snipster.repositories.in_memory_repository import InMemorySnippetRepository
from snipster.repositories.json_repository import JSONSnippetRepository
from snipster.repositories.repository import SnippetRepository
from snipster.repositories.sql_model_repository import SQLModelRepository


class RepositoryType(StrEnum):
    """Repository backends"""

    IN_MEMORY = "memory"
    SQL = "sql"
    JSON = "json"


def create_repository(repo_type: str | None = None) -> SnippetRepository:
    """
    Factory function to create repository based on type.

    Args:
        repo_type: Type of repository ('memory', 'sql', 'json')
        If None, reads from REPOSITORY_TYPE env var

    Returns:
        SnippetRepository instance
    """
    if repo_type is None:
        repo_type = config("REPOSITORY_TYPE", default="sql")

    repo_type = repo_type.lower()

    if repo_type == RepositoryType.IN_MEMORY.value:
        return InMemorySnippetRepository()
    if repo_type == RepositoryType.SQL.value:
        db_url = config("DATABASE_URL", default="sqlite:///snippets.db")
        return SQLModelRepository(db_url=db_url)
    if repo_type == RepositoryType.JSON.value:
        data_dir = config("JSON_DATA_DIR", default="data")
        return JSONSnippetRepository(snippet_dir=data_dir)

    raise ValueError(f"Unknown repository type: {repo_type}")
