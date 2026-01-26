# Snipster

[![PyPI version](https://badge.fury.io/py/snipster-app.svg)](https://badge.fury.io/py/snipster-app)
[![Python Version](https://img.shields.io/pypi/pyversions/snipster-app.svg)](https://pypi.org/project/snipster-app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/snipster-app)](https://pepy.tech/project/snipster-app)
[![Downloads](https://static.pepy.tech/badge/snipster-app/month)](https://pepy.tech/project/snipster-app)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![GitHub stars](https://img.shields.io/github/stars/sl2902/snipster.svg)](https://github.com/sl2902/snipster/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/sl2902/snipster.svg)](https://github.com/sl2902/snipster/issues)

[![Tests](https://github.com/sl2902/snipster/workflows/Tests/badge.svg)](https://github.com/sl2902/snipster/actions)
[![codecov](https://codecov.io/gh/sl2902/snipster/branch/main/graph/badge.svg)](https://codecov.io/gh/sl2902/snipster)

**A lightweight, developer-friendly code snippet management system**

Snipster helps developers organize, search, and manage code snippets efficiently through both a CLI and API interface. Built with FastAPI, SQLModel, and Typer.

## Features

✨ **Multiple Interfaces**
- 🖥️ Command-line interface (CLI) for quick snippet management
- 🌐 REST API for integration with other tools
- 📊 Streamlit web interface for visual browsing

🔍 **Powerful Search**
- Full-text search across titles, code, descriptions, and tags
- Filter by programming language
- Toggle favorites for quick access

📝 **Rich Metadata**
- Support for Python, JavaScript, and TypeScript
- Tagging system for organization
- Automatic timestamps for creation and updates
- Favorite snippets for quick retrieval

## uv installation link

> **Don't have uv?** Install it with: `curl -LsSf https://astral.sh/uv/install.sh | sh`<br>
> Learn more at https://github.com/astral-sh/uv

## Installation

### Using pip (recommended for most users)
```bash
pip install snipster-app
```

### Using uv (faster alternative)
```bash
uv pip install snipster-app
```

### From source
```bash
git clone https://github.com/sl2902/snipster.git
cd snipster
uv venv --python 3.13
uv pip install -e .
```

## Quick Start

### CLI Usage
```bash
# Add a snippet
snipster add --title "Quick Sort" --code "def quicksort(arr): ..." --language Python --tags "algorithm,sorting"

# List all snippets
snipster list

# Search snippets
snipster search --term "sort" --language Python

# Get specific snippet
snipster get --snippet-id 1

# Toggle favorite
snipster favourite --snippet-id 1

# Delete snippet
snipster delete --snippet-id 1
```

### Python API
```python
from snipster import Language, Snippet

# Create a snippet
snippet = Snippet(
    title="Hello World",
    code="print('Hello, World!')",
    language=Language.PYTHON,
    tags="beginner,tutorial"
)
```

### REST API

Start the API server:
```bash
# The API runs as a separate service
uvicorn snipster.api.main:app --reload
```

Endpoints available at `http://localhost:8000/docs`

### Run app locally
```bash
uv run snipster-web
```

## Requirements

- Python 3.13+
- uv (Recommended) or pip package manager
- SQLite (included)

## Use Cases

- 💼 **Interview Prep** - Store commonly used algorithms and patterns
- 🎓 **Learning** - Organize code examples from tutorials
- 🔧 **Daily Development** - Quick access to utility functions and snippets
- 📚 **Team Knowledge Base** - Share snippets via API

## Documentation

Full documentation available at: [GitHub](https://github.com/sl2902/snipster.git)

## License

MIT License

## Author

Sun - [GitHub](https://github.com/sl2902/snipster.git)
