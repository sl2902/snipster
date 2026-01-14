"""Use FastAPI to inject repository into the endpoints"""

from fastapi import Request


def get_repo(request: Request):
    """Fetch the repository to serve to the FastAPI endpoint"""
    return request.app.state.repo
