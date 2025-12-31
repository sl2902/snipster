"""Repository class to support multiple backend storages for Snippet model"""

from abc import ABC, abstractmethod
from typing import List

from snipster import Snippet


class SnippetRepository(ABC):  # pragma: no cover
    @abstractmethod
    def add(self, snippet: Snippet) -> None:
        pass

    @abstractmethod
    def list(self) -> List[Snippet]:
        pass

    @abstractmethod
    def get(self, id: int) -> Snippet | None:
        pass

    @abstractmethod
    def delete(self, id: int) -> None:
        pass

    @abstractmethod
    def search(self, term: str, *, language: str | None = None) -> List[Snippet]:
        pass

    @abstractmethod
    def toggle_favourite(self, snippet_id: int) -> None:
        pass

    @abstractmethod
    def tags(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        pass
