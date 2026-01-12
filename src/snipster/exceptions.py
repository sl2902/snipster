"""Custom exceptions for Snipster application"""


class SnipsterError(Exception):
    """Base exception for all Snipster errors."""

    pass


class SnippetNotFoundError(Exception):
    """Raised when snippet with given ID doesn't exist"""

    pass


class RepositoryError(Exception):
    """Base exception for repository operations"""

    pass


class DuplicateSnippetError(SnipsterError):
    """
    Raised when attempting to add a snippet that already exists.
    """

    pass
