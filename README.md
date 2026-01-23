# Snipster

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

## Installation
```bash
pip install snipster-app
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

## Requirements

- Python 3.13+
- SQLite (included)

## Use Cases

- 💼 **Interview Prep** - Store commonly used algorithms and patterns
- 🎓 **Learning** - Organize code examples from tutorials
- 🔧 **Daily Development** - Quick access to utility functions and snippets
- 📚 **Team Knowledge Base** - Share snippets via API

## Documentation

Full documentation available at: [your-docs-url]

## License

MIT License

## Contributing

Contributions welcome! Visit [your-repo-url] for guidelines.

## Author

Sun - [sl2902]
