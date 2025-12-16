.PHONY: test coverage

test:
	uv run pytest

coverage:
	uv run pytest --cov=src --cov-report=term-missing

coverage-html:
	uv run pytest --cov=src --cov-report=html
