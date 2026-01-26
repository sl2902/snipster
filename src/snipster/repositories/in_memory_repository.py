"""In-memory backend repository"""

from typing import List

from loguru import logger

from snipster.models import Snippet
from snipster.repositories.repository import SnippetRepository


class InMemorySnippetRepository(SnippetRepository):
    """In-memory implementation of the abstract base class"""

    def __init__(self):
        self._data: dict[int, Snippet] = {}
        self._next_id = 1

    def add(self, snippet: Snippet) -> None:
        self._data[self._next_id] = snippet
        self._next_id += 1

    def list(self) -> List[Snippet]:
        return list(self._data.values())

    def get(self, snippet_id: int) -> Snippet | None:
        return self._data.get(snippet_id)

    def delete(self, snippet_id: int) -> None:
        if snippet_id not in self._data:
            logger.error(f"Snippet with id {snippet_id} not found")
            raise KeyError(f"Snippet with id {snippet_id} not found")
        self._data.pop(snippet_id)

    def search(self, term: str, language: str | None = None) -> List[Snippet]:
        matches = []
        if language:
            logger.info(f"Searching for the term `{term}` in the {language} language")
            snippets = [
                snippet
                for k, snippet in self._data.items()
                if language and snippet.language.value.lower() == language.lower()
            ]
        else:
            logger.info(f"Searching for the term `{term}`")
            snippets = [snippet for k, snippet in self._data.items()]

        for snippet in snippets:
            term_lc = term.lower()
            if term_lc in snippet.title.lower():
                matches.append(snippet)
            elif snippet.description and term_lc in snippet.description.lower():
                matches.append(snippet)
            elif term_lc in snippet.code.lower():
                matches.append(snippet)
        if len(matches) == 0:
            logger.error(f"Term {term} not present in list of snippets")
            raise ValueError(f"Term {term} not present in list of snippets")

        return matches

    def toggle_favourite(self, snippet_id: int) -> None:
        snippet = self.get(snippet_id)
        if snippet:
            if not snippet.favorite:
                snippet.favorite = True
            else:
                snippet.favorite = False
            self._data[snippet_id] = snippet
        else:
            logger.error(f"Snippet with id {snippet_id} not found")
            raise KeyError(f"Snippet with id {snippet_id} not found")

    def tags(
        self, snippet_id: int, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        snippet = self.get(snippet_id)
        if snippet:
            logger.info(f"Updating tags {tags} for snippet {snippet_id}")
            snippet.tags = self.process_tags(snippet.tags, tags, remove, sort)

        else:
            logger.error(f"Snippet id {snippet_id} not found")
            raise KeyError(f"Snippet id {snippet_id} not found")

        self._data[snippet_id] = snippet


if __name__ == "__main__":  # pragma: no cover
    repo = InMemorySnippetRepository()
    snippet = Snippet(title="test code", code="print('hello test)")
    repo.add(snippet)
    logger.info(repo.list())
