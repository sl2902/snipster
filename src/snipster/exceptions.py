"""Custom exceptions"""


class SnippetNotFoundError(Exception):
    """Raised when snippet with given ID doesn't exist"""

    pass


class RepositoryError(Exception):
    """Base exception for repository operations"""

    pass
