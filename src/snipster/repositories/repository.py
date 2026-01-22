"""Repository class to support multiple backend storages for Snippet model"""

from abc import ABC, abstractmethod
from typing import List

from snipster.models import Snippet

TAG_SEPARATOR = ", "


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
    def toggle_favourite(self, snippet_id: int) -> bool:
        pass

    @abstractmethod
    def tags(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        pass

    def process_tags(
        self,
        existing_tags: str | None,
        new_tags: tuple[str, ...],
        remove: bool = False,
        sort: bool = True,
    ) -> str:
        """Process and merge tags for a snippet.

        Args:
            existing_tags: Current comma-separated tags string, or None if no tags exist.
            new_tags: Tuple of tag strings to add or remove.
            remove: If True, remove the specified tags. If False, add them.
            sort: If True, sort the resulting tags alphabetically.

        Returns:
            Comma-separated string of processed tags.
        """
        tags_list = existing_tags.split(", ") if existing_tags else []
        if not remove:
            for tag in new_tags:
                if tag not in tags_list:
                    tags_list.append(tag)
        else:
            for tag in new_tags:
                if tag in tags_list:
                    tags_list.remove(tag)

        if sort:
            tags_list.sort()

        return TAG_SEPARATOR.join(tags_list)
