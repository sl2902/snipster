"""Custom exceptions for Snipster application"""


class SnipsterError(Exception):
    """Base exception for all Snipster errors."""

    pass


class SnippetNotFoundError(SnipsterError):
    """Raised when snippet with given ID doesn't exist"""

    pass


class RepositoryError(SnipsterError):
    """Base exception for repository operations"""

    pass


class DuplicateSnippetError(SnipsterError):
    """
    Raised when attempting to add a snippet that already exists.
    """

    pass


class MultipleSnippetsFoundError(SnipsterError):
    """
    Raised when attempting to delete multiple snippets against a single snippet id.
    """

    pass
