"""Define FastAPI input and output model schemas"""

from datetime import datetime

from snipster.models import SnippetBase


class SnippetCreate(SnippetBase):
    """Schema for creating a snippet - only user-provided fields"""

    pass


class SnippetResponse(SnippetBase):
    """Schema for API response - includes generated fields"""

    id: int
    created_at: datetime
    updated_at: datetime
