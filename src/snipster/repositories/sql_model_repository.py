"""SQLModel backend repository"""

from typing import List

import httpx
from decouple import config
from loguru import logger
from sqlalchemy.exc import (
    IntegrityError,
    MultipleResultsFound,
    NoResultFound,
    OperationalError,
    SQLAlchemyError,
)

from snipster.database_manager import DatabaseManager
from snipster.exceptions import (
    DatabaseConnectionError,
    DuplicateGistError,
    DuplicateSnippetError,
    GistNotFoundError,
    MultipleSnippetsFoundError,
    RepositoryError,
    SnippetNotFoundError,
)
from snipster.models import Gist, Snippet
from snipster.repositories.repository import SnippetRepository
from snipster.types import Language

GIST_BASE_URL = config("GIST_URL")


class SQLModelRepository(SnippetRepository):
    """SQLModel implementation of the abstract base class"""

    def __init__(self, db_url: str | None = None, echo: bool = False):
        self.db_url = db_url
        self.db_manager = DatabaseManager(self.db_url, echo)

    def add(self, snippet: Snippet) -> None:
        try:
            self.db_manager.insert_record(Snippet, snippet)
        except IntegrityError as err:
            logger.error(f"Duplicate record found: {snippet}")
            raise DuplicateSnippetError(f"Duplicate record found: {snippet}") from err
        except OperationalError as err:
            logger.error(f"Database connection error while adding snippet: {snippet}")
            raise DatabaseConnectionError(
                f"Database connection error while adding snippet: {snippet}"
            ) from err
        except SQLAlchemyError as err:
            logger.error(f"Database error occurred while adding snippet: {snippet}")
            raise RepositoryError(
                f"Database error occurred while adding snippet: {snippet}"
            ) from err
        logger.info("Added a single record successfully")

    def list(self) -> List[Snippet]:
        try:
            return list(self.db_manager.select_all(Snippet))
        except OperationalError as err:
            logger.error("Database connection error while listing all snippets")
            raise DatabaseConnectionError(
                "Database connection error while listing all snippets"
            ) from err
        except SQLAlchemyError as err:
            logger.error("Database error occurred while listing all snippets")
            raise RepositoryError(
                "Database error occurred while listing all snippets"
            ) from err

    def get(self, snippet_id: int) -> Snippet | None:
        try:
            return self.db_manager.select_by_id(Snippet, snippet_id)
        except OperationalError as err:
            logger.error(
                f"Database connection error while fetching snippet: {snippet_id}"
            )
            raise DatabaseConnectionError(
                f"Database connection error while fetching snippet: {snippet_id}"
            ) from err
        except SQLAlchemyError as err:
            logger.error(
                f"Database error occurred while fetching snippet: {snippet_id}"
            )
            raise RepositoryError(
                f"Database error occurred while fetching snippet: {snippet_id}"
            ) from err

    def delete(self, snippet_id: int) -> None:
        try:
            self.db_manager.delete_record(Snippet, snippet_id)
            logger.info(f"Record id '{snippet_id}' deleted successfully")
        except NoResultFound as err:
            logger.warning(f"Snippet with id {snippet_id} not found")
            raise SnippetNotFoundError(
                f"Snippet with id '{snippet_id}' not found"
            ) from err
        except MultipleResultsFound as err:
            logger.error(f"Multiple snippets found for snippet: {snippet_id}")
            raise MultipleSnippetsFoundError(
                f"Multiple snippets found for snippet: {snippet_id}"
            ) from err
        except OperationalError as err:
            logger.error(
                f"Database connection error while deleting snippet: {snippet_id}"
            )
            raise DatabaseConnectionError(
                f"Database connection error while deleting snippet: {snippet_id}"
            ) from err
        except SQLAlchemyError as err:
            logger.error(
                f"Database error occurred while deleting snippet: {snippet_id}"
            )
            raise RepositoryError(
                f"Database error occurred while deleting snippet: {snippet_id}"
            ) from err

    def search(self, term: str, *, language: str | None = None) -> List[Snippet]:
        cols_to_search = ["title", "code", "description"]
        all_snippets = {}
        for col in cols_to_search:
            try:
                snippets = self.db_manager.select_with_filter(Snippet, col, term)
            except OperationalError as err:
                logger.error(
                    f"Database connection error while searching snippet term: {term}"
                )
                raise DatabaseConnectionError(
                    f"Database connection error while searching snippet term: {term}"
                ) from err
            except SQLAlchemyError as err:
                logger.error(
                    f"Database error occurred while searching snippet term: {term}"
                )
                raise RepositoryError(
                    f"Database error occurred while searching snippet term: {term}"
                ) from err

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

    def get_gist(self, snippet_id: int) -> Gist | None:
        snippet = self.get(snippet_id)
        if not snippet:
            return None

        try:
            gist = self.db_manager.select_by_id(Gist, snippet_id)
        except OperationalError as err:
            logger.error("Database connection error while fetching gist")
            raise DatabaseConnectionError(
                "Database connection error  while fetching gist"
            ) from err
        except SQLAlchemyError as err:
            logger.error("Database error occurred  while fetching gist")
            raise RepositoryError(
                "Database error occurred  while fetching gist"
            ) from err

        if gist and not self.verify_gist_exists(gist.gist_id):
            self.db_manager.delete_record(Gist, snippet_id)
            logger.warning(
                f"Gist {gist.gist_id} was deleted on GitHub, cleaned up locally"
            )
            return None
        return gist

    def verify_gist_exists(self, gist_id: str) -> bool:
        try:
            response = httpx.get(
                f"{GIST_BASE_URL}/{gist_id}",
                headers={"Authorization": f"token {config('GH_TOKEN')}"},
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def add_gist(self, snippet_id: int, gist_url: str, is_public: bool) -> None:
        gist_id = gist_url.split("/")[-1]
        gist = Gist(
            snippet_id=snippet_id,
            gist_id=gist_id,
            gist_url=gist_url,
            is_public=is_public,
        )
        try:
            self.db_manager.insert_record(Gist, gist)
        except IntegrityError as err:
            if "UNIQUE constraint" in str(err):
                logger.warning(f"Gist already exists for snippet {snippet_id}")
                raise DuplicateGistError(
                    f"Snippet {snippet_id} already has a gist"
                ) from err
            logger.error(f"Failed to add gist for snippet: {snippet_id}")
            raise RepositoryError(
                f"Failed to add gist for snippet: {snippet_id}"
            ) from err
        except OperationalError as err:
            logger.error(f"Failed to add gist: {gist} for snippet: {snippet_id}: {err}")
            raise RepositoryError(
                f"Failed to add gist: {gist} for snippet: {snippet_id}"
            ) from err

        logger.info(f"Added gist successfully for snippet: {snippet_id}")

    def create_gist(
        self,
        snippet_id: int,
        code: str,
        title: str,
        language: str,
        *,
        is_public: bool = True,
    ) -> str:
        ext = Language.extension_for(language)

        gist = self.get_gist(snippet_id)
        if gist:
            logger.warning(f"Gist already exists for snippet {snippet_id}")
            raise DuplicateGistError

        logger.info(f"Create gist for snippet '{snippet_id}'")
        payload = {
            "description": title,
            "public": is_public,
            "files": {f"{title.replace(" ", "_").lower()}.{ext}": {"content": code}},
        }
        headers = {"Authorization": f"token {config('GH_TOKEN')}"}

        try:
            response = httpx.post(GIST_BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as err:
            logger.error(f"Failed to create gist: {err}")
            raise RepositoryError(f"Failed to create gist: {err}") from err

        gist_url = response.json()["html_url"]

        logger.info("Store gist for snippet '{snippet_id}'")
        self.add_gist(snippet_id, gist_url, is_public)

        return gist_url

    def _fetch_gist_unchecked(self, snippet_id: int) -> Gist | None:
        """Fetch gist without GitHub verification (may be stale)"""
        try:
            return self.db_manager.select_by_id(Gist, snippet_id)
        except SQLAlchemyError as e:
            raise RepositoryError("Failed to fetch gist") from e

    def delete_gist(
        self,
        snippet_id: int,
    ) -> None:
        gist = self._fetch_gist_unchecked(snippet_id)

        if not gist:
            raise GistNotFoundError(f"Gist not found for snippet '{snippet_id}'")

        headers = {"Authorization": f"token {config('GH_TOKEN')}"}

        try:
            response = httpx.delete(f"{GIST_BASE_URL}/{gist.gist_id}", headers=headers)
            response.raise_for_status()
            logger.info("Deleted gist from GitHub")
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 404:
                logger.warning("Gist already deleted on GitHub, cleaning up locally")
            else:
                raise RepositoryError(f"GitHub deletion failed: {err}") from err
        except httpx.HTTPError as err:
            logger.error(f"Cannot connect to GitHub: {err}")
            raise RepositoryError(f"Cannot connect to GitHub: {err}") from err

        try:
            self.db_manager.delete_record(Gist, snippet_id)
        except MultipleResultsFound as err:
            logger.error(f"Multiple gists found for snippet: {snippet_id}")
            raise MultipleSnippetsFoundError(
                f"Multiple gists found for snippet: {snippet_id}"
            ) from err
        except OperationalError as err:
            logger.error(
                f"Database connection error while deleting gist with snippet: {snippet_id}"
            )
            raise DatabaseConnectionError(
                f"Database connection error while deleting gist with snippet: {snippet_id}"
            ) from err
        except SQLAlchemyError as err:
            logger.error(
                f"Database error occurred while deleting gist with snippet: {snippet_id}"
            )
            raise RepositoryError(
                f"Database error occurred while deleting gist with snippet: {snippet_id}"
            ) from err

        logger.info(f"Deleted gist for snippet '{snippet_id}'")


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
