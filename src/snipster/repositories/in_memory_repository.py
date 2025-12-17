"""In-memory backend repository"""

from typing import List

from loguru import logger

from snipster.models import Snippet
from snipster.repositories.repository import SnippetRepository


class InMemorySnippetRepository(SnippetRepository):
    """In-memory implementation of the abstract base class"""

    def __init__(self):
        self._data: dict[str, Snippet] = {}

    def add(self, snippet: Snippet) -> None:
        _id = max(self._data.keys(), default=0) + 1
        self._data[_id] = snippet

    def list(self) -> List[Snippet]:
        return list(self._data.values())

    def get(self, snippet_id: int) -> Snippet | None:
        return self._data.get(snippet_id)

    def delete(self, snippet_id: int) -> None:
        if snippet_id not in self._data:
            logger.error(f"Snippet with id {snippet_id} not found")
            raise KeyError(f"Snippet with id {snippet_id} not found")
        self._data.pop(snippet_id)


if __name__ == "__main__":  # pragma: no cover
    repo = InMemorySnippetRepository()
    snippet = Snippet(title="test code", code="print('hello test)")
    repo.add(snippet)
    logger.info(repo.list())
