"""Use FastAPI to inject repository into the endpoints"""

from fastapi import Request

from snipster.repositories.repository import SnippetRepository


def get_repo(request: Request) -> SnippetRepository:  # pragma: no cover
    """Fetch the repository to serve to the FastAPI endpoint"""
    return request.app.state.repo
