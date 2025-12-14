"""Define models class"""

from datetime import datetime
from enum import Enum

from loguru import logger
from sqlmodel import Field, SQLModel, UniqueConstraint

from snipster.database_manager import DatabaseManager


class Language(str, Enum):
    PYTHON = "python"


class Snippet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(..., description="Title of the snippet")
    code: str = Field(..., description="Code snippet")
    description: str | None = Field(
        default=None, description="Description of the code snippet"
    )
    language: Language = Field(
        default=Language.PYTHON.value,
        description="Enum describing the programming language",
    )
    tags: str | None = Field(
        default=None, description="Labels to identify the code snippet"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation date of snippet"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Snippet last updated"
    )
    favorite: bool = Field(default=False, description="Is favourite?")

    __table_args__ = (UniqueConstraint("title", "language"),)


if __name__ == "__main__":  # pragma: no cover
    db_manager = DatabaseManager()
    logger.info(db_manager.select_by_snippet_id(Snippet, 1))
    results = db_manager.select_all(Snippet)
    logger.info(f" Number of records fetched: {len(results)}")
    logger.info("Testing Insert statement")
    snippet1 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    snippet2 = Snippet(
        title="For Loop",
        code="for i in range(10):\n    print(i)",
        language=Language.PYTHON,
        tags="loops, basics",
    )

    snippets = [snippet1, snippet2]
    db_manager.insert_records(Snippet, snippets)
