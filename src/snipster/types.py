from enum import Enum  # pragma: no cover


class Language(str, Enum):  # pragma: no cover
    """Supported programming languages for code snippets.

    Inherits from str to allow direct string comparison in queries
    and JSON serialization.
    """

    PYTHON = "Python"
    JAVASCRIPT = "JavaScript"
    TYPESCRIPT = "TypeScript"
