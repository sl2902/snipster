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


class DatabaseConnectionError(SnipsterError):
    """Database connection/operational issues"""

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


class DuplicateGistError(SnipsterError):
    """Raised when attempting to create a gist for a snippet that already has one"""

    pass


class GistNotFoundError(SnipsterError):
    """Raised when gist associated to a snippet with given ID doesn't exist"""

    pass
