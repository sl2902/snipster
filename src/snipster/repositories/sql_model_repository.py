"""SQLModel backend repository"""

from typing import List

from loguru import logger

from snipster import Language, Snippet
from snipster.database_manager import DatabaseManager
from snipster.exceptions import SnippetNotFoundError
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
        self.db_manager.delete_record(Snippet, snippet_id)
        logger.info(f"Record id {id} deleted successfully")

    def search(self, term: str, *, language: str | None = None) -> List[Snippet]:
        cols_to_search = ["title", "code", "description"]
        for col in cols_to_search:
            snippets = self.db_manager.select_with_filter(Snippet, col, term)
            if snippets:
                break
        else:
            logger.error(f"No matches found for term {term} in the Snippets model")
            raise ValueError(f"No matches found for term {term} in the Snippets model")
        if language:
            lang_filtered_snippets = []
            for snippet in snippets:
                if snippet.language.value.lower() == language.lower():
                    lang_filtered_snippets.append(snippet)
            return lang_filtered_snippets
        return snippets

    def toggle_favourite(self, snippet_id: int) -> None:
        snippet = self.get(snippet_id)
        if snippet:
            if snippet.favorite is False:
                snippet.favorite = True
            else:
                snippet.favorite = False
        else:
            logger.error(f"Snippet with id {snippet_id} not found")
            raise SnippetNotFoundError(f"Snippet with id {snippet_id} not found")

        self.db_manager.update(Snippet, snippet_id, "favorite", snippet.favorite)
        logger.info(f"Successfully updated snippet id {snippet_id}")

    def tags(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        snippet = self.get(snippet_id)
        if snippet:
            logger.info(f"Updating tags {tags} for snippet {snippet_id}")
            existing_tags = snippet.tags.split(", ") if snippet.tags else []

            if not remove:
                for tag in tags:
                    tag = tag.strip()
                    if tag not in existing_tags:
                        existing_tags.append(tag)
            else:
                for tag in tags:
                    tag = tag.strip()
                    if tag in existing_tags:
                        existing_tags.remove(tag)

            if sort:
                snippet.tags = ", ".join(sorted(existing_tags))
            else:
                snippet.tags = ", ".join(existing_tags)

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
