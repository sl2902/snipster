"""Define models class"""

from datetime import datetime, timezone

from loguru import logger
from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel, UniqueConstraint

from snipster.database_manager import DatabaseManager
from snipster.types import Language


class SnippetBase(SQLModel):
    """Shared fields for all snippet schemas"""

    title: str = Field(..., description="Title of the snippet")
    code: str = Field(..., description="Code snippet")
    description: str | None = Field(
        default=None, description="Description of the code snippet"
    )
    language: Language = Field(
        default=Language.PYTHON,
        description="Enum describing the programming language",
    )
    tags: str | None = Field(
        default=None, description="Labels to identify the code snippet"
    )
    favorite: bool = Field(
        default=False, description="Flag to mark snippet as favorite"
    )


class Snippet(SnippetBase, table=True):
    """A code snippet with metadata for organization and retrieval.

    Snippets are uniquely identified by their title + language combination,
    allowing the same title across different programming languages.

    Attributes:
        id: Auto-generated primary key.
        title: Human-readable name (minimum 3 characters).
        code: The actual code content.
        description: Optional explanation of what the code does.
        language: Programming language (defaults to Python).
        tags: Comma-separated labels for categorization.
        created_at: Timestamp of creation.
        updated_at: Timestamp of last modification.
        favorite: Flag for quick-access snippets.
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation date of snippet",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Snippet last updated",
    )

    # https://github.com/fastapi/sqlmodel/issues/52#issuecomment-2495817760
    model_config = ConfigDict(validate_assignment=True, from_attributes=True)
    # __table_args__ = {"extend_existing": True}

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v

    __table_args__ = (
        UniqueConstraint("title", "language"),
        {"extend_existing": True},
    )


if __name__ == "__main__":  # pragma: no cover
    db_manager = DatabaseManager(echo=False)
    # snippet = snippet = Snippet(title="xx", code="test")
    # logger.debug(snippet)
    logger.info(db_manager.select_by_id(Snippet, 1))
    results = db_manager.select_all(Snippet)
    logger.info(f" Number of records fetched: {len(results)}")
    if results:
        logger.info(results)
    logger.info("Testing Insert statement")

    snippet1 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    snippet2 = Snippet(
        title="Hello World",
        code="print('Hello, World!')",
        description="Basic Python hello world",
        language=Language.PYTHON,
        tags="beginner, tutorial",
    )

    snippet3 = Snippet(
        title="For Loop",
        code="for i in range(10):\n    print(i)",
        language=Language.PYTHON,
        tags="loops, basics",
    )

    snippet4 = Snippet(
        title="For Loop",
        code="for i in range(10):\n    print(i)",
        language=Language.PYTHON,
        tags="loops, basics",
    )

    snippet5 = Snippet(
        title="List Comprehension",
        code="squares = [x**2 for x in range(10)]",
        language=Language.PYTHON,
        tags="list, comprehension",
    )

    snippet6 = Snippet(
        title="Dictionary Example",
        code="my_dict = {'key': 'value', 'number': 42}",
        language=Language.PYTHON,
        tags="dictionary, basics",
    )

    snippet7 = Snippet(
        title="Function Definition",
        code="def greet(name):\n    return f'Hello, {name}!'",
        language=Language.PYTHON,
        tags="function, basics",
    )

    snippets = [snippet1, snippet2, snippet3, snippet4, snippet5, snippet6, snippet7]
    db_manager.insert_records(Snippet, snippets, batch_size=3)

    for _ in range(2):
        snippet7 = Snippet(
            title="Function Definition",
            code="def greet(name):\n    return f'Hello, {name}!'",
            language=Language.PYTHON,
            tags="function, basics",
        )
        is_inserted = db_manager.insert_record(Snippet, snippet7)
        logger.info(f"Record inserted status {is_inserted}")

    snippet_id = 5
    is_deleted = db_manager.delete_record(Snippet, snippet_id)
    if is_deleted:
        logger.info(f"Snippet with id {snippet_id} has been deleted")
    else:
        logger.warning(f"Snippet with id {snippet_id} does not exist")
