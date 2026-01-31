from enum import Enum


class Language(str, Enum):
    """Supported programming languages for code snippets.

    Inherits from str to allow direct string comparison in queries
    and JSON serialization.
    """

    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"

    def get_extension(self):
        """Get file extension for this language"""
        extensions = {
            Language.PYTHON: "py",
            Language.JAVASCRIPT: "js",
            Language.TYPESCRIPT: "ts",
        }

        return extensions[self]

    @classmethod
    def extension_for(cls, language: str) -> str:
        """Get extension from language string"""
        return cls(language).get_extension()


class GistStatus(str, Enum):
    """Supported status values for snippet gists"""

    ACTIVE = "active"
    DELETED_ON_GITHUB = "deleted_on_github"
    UNKNOWN = "unknown"
