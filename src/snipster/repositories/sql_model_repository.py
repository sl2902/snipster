"""SQLModel backend repository"""

from typing import List

from loguru import logger

from snipster.database_manager import DatabaseManager
from snipster.exceptions import (
    DuplicateSnippetError,
    RepositoryError,
    SnippetNotFoundError,
)
from snipster.models import Snippet
from snipster.repositories.repository import SnippetRepository
from snipster.types import Language


class SQLModelRepository(SnippetRepository):
    """SQLModel implementation of the abstract base class"""

    def __init__(self, db_url: str | None = None, echo: bool = False):
        self.db_url = db_url
        self.db_manager = DatabaseManager(self.db_url, echo)

    def add(self, snippet: Snippet) -> None:
        try:
            self.db_manager.insert_record(Snippet, snippet)
        except DuplicateSnippetError:
            logger.warning(f"Duplicate record found: {snippet}")
            raise
        except RepositoryError:
            logger.warning(f"Failed to add snippet: {snippet}")
            raise
        logger.info("Added a single record successfully")

    def list(self) -> List[Snippet]:
        return list(self.db_manager.select_all(Snippet))

    def get(self, snippet_id: int) -> Snippet | None:
        return self.db_manager.select_by_id(Snippet, snippet_id)

    def delete(self, snippet_id: int) -> None:
        self.db_manager.delete_record(Snippet, snippet_id)
        logger.info(f"Record id {snippet_id} deleted successfully")

    def search(self, term: str, *, language: str | None = None) -> List[Snippet]:
        cols_to_search = ["title", "code", "description"]
        all_snippets = {}
        for col in cols_to_search:
            snippets = self.db_manager.select_with_filter(Snippet, col, term)
            for snippet in snippets:
                if snippet.id not in all_snippets:
                    all_snippets[snippet.id] = snippet
        if not all_snippets:
            logger.warning(f"No matches found for term '{term}' in the Snippets model")
            return []
        if language:
            lang_filtered_snippets = [
                snippet
                for snippet in all_snippets.values()
                if snippet.language.value.lower() == language.lower()
            ]
            if not lang_filtered_snippets:
                logger.warning(
                    f"No matches found for term '{term}' and language {language} in the Snippets model"
                )
            return lang_filtered_snippets
        return list(all_snippets.values())

    def toggle_favourite(self, snippet_id: int) -> bool:
        snippet = self.get(snippet_id)
        if snippet:
            snippet.favorite = not snippet.favorite
        else:
            logger.error(f"Snippet with id {snippet_id} not found")
            raise SnippetNotFoundError(f"Snippet with id {snippet_id} not found")

        self.db_manager.update(Snippet, snippet_id, "favorite", snippet.favorite)
        if snippet.favorite:
            logger.info(f"Successfully favourited snippet id {snippet_id}")
        else:
            logger.info(f"Successfully unfavourited snippet id {snippet_id}")

        return snippet.favorite

    def tags(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        snippet = self.get(snippet_id)
        if snippet:
            logger.info(f"Updating tags {tags} for snippet {snippet_id}")
            snippet.tags = self.process_tags(snippet.tags, tags, remove, sort)

        else:
            logger.error(f"Snippet id {snippet_id} not found")
            raise SnippetNotFoundError(f"Snippet id {snippet_id} not found")

        self.db_manager.update(Snippet, pk=snippet_id, col="tags", value=snippet.tags)
        logger.info(f"Successfully updated tags for snippet {snippet_id}")


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
