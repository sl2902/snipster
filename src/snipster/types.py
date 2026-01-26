from enum import Enum


class Language(str, Enum):
    """Supported programming languages for code snippets.

    Inherits from str to allow direct string comparison in queries
    and JSON serialization.
    """

    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
