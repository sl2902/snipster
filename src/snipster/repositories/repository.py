"""Repository class to support multiple backend storages for Snippet model"""

from abc import ABC, abstractmethod
from typing import List

from snipster.models import Snippet


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
