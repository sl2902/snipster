"""Define snipster routes"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from snipster import Snippet
from snipster.api.dependencies import get_repo
from snipster.api.schemas import SnippetCreate, SnippetResponse
from snipster.exceptions import (
    DuplicateSnippetError,
    MultipleSnippetsFoundError,
    RepositoryError,
    SnippetNotFoundError,
)
from snipster.repositories.repository import SnippetRepository

router = APIRouter()


@router.post("/snippets/v1/")
def create_snippet(
    *, repo: SnippetRepository = Depends(get_repo), snippet: SnippetCreate
):
    snippet_data = snippet.model_dump()
    db_snippet = Snippet(**snippet_data)
    try:
        repo.add(db_snippet)
        logger.debug(f"Snippet with title '{db_snippet.title}' created")
    except DuplicateSnippetError:
        raise HTTPException(status_code=409, detail="Snippet already exists")
    except RepositoryError:
        raise HTTPException(status_code=500, detail="Database error")
    return {"message": f"Successfully created Snippet with title '{db_snippet.title}'"}


@router.get("/snippets/v1/list/", response_model=list[SnippetResponse])
def list_snippets(*, repo: SnippetRepository = Depends(get_repo)):
    try:
        snippets = repo.list()
        if snippets:
            logger.debug(f"{len(snippets)} found in repository")
            return snippets
        raise HTTPException(status_code=404, detail="No snippets in repository")
    except RepositoryError:
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/snippets/v1/{snippet_id}", response_model=SnippetResponse)
def get_snippet(*, repo: SnippetRepository = Depends(get_repo), snippet_id: int):
    try:
        snippet = repo.get(snippet_id)
        if snippet:
            return snippet
        raise HTTPException(status_code=404, detail=f"Snippet '{snippet_id}' not found")
    except RepositoryError:
        raise HTTPException(status_code=500, detail="Database error")


@router.delete("/snippets/v1/{snippet_id}")
def delete_snippet(*, repo: SnippetRepository = Depends(get_repo), snippet_id: int):
    try:
        repo.delete(snippet_id)
        logger.debug(f"Snippet '{snippet_id}' is available for deletion")
        return {"message": "Snippet deleted successfully"}
    except SnippetNotFoundError:
        raise HTTPException(status_code=404, detail=f"Snippet '{snippet_id}' not found")
    except MultipleSnippetsFoundError:
        raise HTTPException(
            status_code=409, detail=f"Multiple snippets found for snippet {snippet_id}"
        )
    except RepositoryError:
        raise HTTPException(status_code=500, detail="Database error")


@router.get("/snippets/v1/search/", response_model=list[SnippetResponse])
def search_snippets(
    *,
    repo: SnippetRepository = Depends(get_repo),
    term: str,
    language: str | None = None,
):
    try:
        snippets = repo.search(term, language=language)
        if snippets:
            logger.debug(f"Matches found for search term '{term}'")
            return snippets
    except ValueError:
        raise HTTPException(status_code=404, detail="Search yielded no snippets")
    except RepositoryError:
        raise HTTPException(status_code=500, detail="Database error")
