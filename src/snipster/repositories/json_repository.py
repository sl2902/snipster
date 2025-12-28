"""JSON backend repository"""

import json
from pathlib import Path
from typing import List

from loguru import logger

from snipster.models import Snippet
from snipster.repositories.repository import SnippetRepository

PROJECT_ROOT = Path("pyproject.toml").resolve().parent


class JSONSnippetRepository(SnippetRepository):
    """JSON implementation of the abstract base class"""

    def __init__(self, snippet_dir: str = "data"):
        self.sub_dir = snippet_dir
        self.snippet_file = "all_snippets.jsonl"
        self._create_snippet_dir(self.sub_dir)
        self.full_filepath = str(PROJECT_ROOT / snippet_dir / self.snippet_file)
        self._data = self._load_existing_snippets_to_memory()
        logger.info(self._data.keys())
        self._next_id = max(self._data.keys(), default=0) + 1

    @staticmethod
    def _create_snippet_dir(sub_dir: str):
        p = PROJECT_ROOT / sub_dir
        p.mkdir(parents=True, exist_ok=True)

    def _load_existing_snippets_to_memory(self):
        snippet_dict = {}
        filepath = self.full_filepath
        try:
            with open(filepath, "r") as json_read:
                for line in json_read:
                    record = json.loads(line)
                    snippet_dict[record.get("id")] = Snippet(**record)
        except FileNotFoundError:
            logger.warning(f"JSONL Snippet file {filepath} not found")
        return snippet_dict

    def add(self, snippet: Snippet) -> None:
        for key in self._data:
            stored_snippet = self._data[key]
            if (
                stored_snippet.title == snippet.title
                and stored_snippet.language == snippet.language
            ):
                logger.warning(f"Duplicate snippet {snippet} for id {key} found")
                return None

        with open(self.full_filepath, "a") as f:
            snippet.id = self._next_id
            self._data[self._next_id] = snippet
            self._next_id += 1
            snippet.created_at = str(snippet.created_at)
            snippet.updated_at = str(snippet.updated_at)
            json.dump(snippet.model_dump(mode="json"), f, sort_keys=True)
            f.write("\n")

        logger.info(f"Data contains {self._data}")
        logger.info(f"Successfully added snippet {snippet} to jsonl file")

    def list(self) -> List[Snippet]:
        return list(self._data.values())

    def get(self, snippet_id: int) -> Snippet | None:
        return self._data.get(snippet_id)

    def delete(self, snippet_id: int) -> None:
        if snippet_id not in self._data:
            logger.warning(
                f"Snippet id {snippet_id} not found in JSON file. Nothing to remove"
            )
        else:
            self._data.pop(snippet_id)
            with open(self.full_filepath, "w") as f:
                for row, snippet in self._data.items():
                    json.dump(snippet.model_dump(mode="json"), f, sort_keys=True)
                    f.write("\n")
            logger.info(f"Snippet id {snippet_id} removed from JSON file")

    def search(self, term: str, *, language: str | None = None) -> List[Snippet]:
        pass

    def toggle_favourite(self, snippet_id: int) -> None:
        pass

    def tags(
        self, snippet_id: int, /, *tags: str, remove: bool = False, sort: bool = True
    ) -> None:
        pass

    def update_tags(self, snippet_id: int) -> None:
        pass


if __name__ == "__main__":  # pragma: no cover
    json_repo = JSONSnippetRepository()
    snippet = Snippet(title="test code", code="print('hello test')")
    json_repo.add(snippet)
    snippet = Snippet(title="test code 2", code="print('hello test 2')")
    json_repo.add(snippet)
    logger.info("Delete snippet id 1")
    json_repo.delete(1)
    # snippet = Snippet(title="test code 3", code="print('hello test 3')")
    # json_repo.add(snippet)
