"""Define models class"""

from datetime import datetime
from enum import Enum

from loguru import logger
from sqlmodel import Field, SQLModel

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
        default=Language.PYTHON, description="Enum describing the programming language"
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


if __name__ == "__main__":
    db_manager = DatabaseManager()
    logger.info(db_manager.select_by_snippet_id(Snippet, 1))
    logger.info(db_manager.select_all(Snippet))
