"""SQLModel backend repository"""

from typing import List

from loguru import logger

from snipster.database_manager import DatabaseManager
from snipster.models import Language, Snippet
from snipster.repositories.repository import SnippetRepository


class SQLModelRepository(SnippetRepository):
    """SQLModel implementation of the abstract base class"""

    def __init__(self, db_url: str | None = None, echo: bool = False):
        self.db_url = db_url
        self.db_manager = DatabaseManager(self.db_url, echo)

    def add(self, snippet: Snippet) -> None:
        is_inserted = self.db_manager.insert_record(Snippet, snippet)
        if is_inserted:
            logger.info("Added a single record successfully")
        else:
            logger.warning(f"Duplicate recond found: {snippet}")

    def list(self) -> List[Snippet]:
        return list(self.db_manager.select_all(Snippet))

    def get(self, snippet_id: int) -> Snippet | None:
        return self.db_manager.select_by_id(Snippet, snippet_id)

    def delete(self, snippet_id: int) -> None:
        is_deleted = self.db_manager.delete_record(Snippet, snippet_id)
        if is_deleted:
            logger.info("Record id {id} deleted successfully")
        else:
            logger.warning("Found no record with id {id} to delete")


if __name__ == "__main__":  # pragma: no cover
    sql_repo = SQLModelRepository()
    snippet = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )
    sql_repo.add(snippet)
