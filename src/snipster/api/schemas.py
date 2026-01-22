"""Define FastAPI input and output model schemas"""

from datetime import datetime

from pydantic import BaseModel, Field
from sqlmodel import SQLModel

from snipster.models import SnippetBase
from snipster.types import Language


class SnippetCreate(SQLModel):
    """Schema for creating a snippet - only user-provided fields; exclude `favorite`"""

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


class SnippetResponse(SnippetBase):
    """Schema for API response - includes generated fields"""

    id: int
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Schema for API response - custom messages"""

    message: str = Field(..., description="Message to send to end user")
