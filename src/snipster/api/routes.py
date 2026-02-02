"""Define snipster routes"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic_core import ValidationError as PydanticValidationError

from snipster.api.dependencies import get_repo
from snipster.api.schemas import (
    GistCreate,
    GistResponse,
    MessageResponse,
    SnippetCreate,
    SnippetResponse,
)
from snipster.exceptions import (
    DatabaseConnectionError,
    DuplicateGistError,
    DuplicateSnippetError,
    GistNotFoundError,
    MultipleSnippetsFoundError,
    RepositoryError,
    SnippetNotFoundError,
)
from snipster.models import Snippet
from snipster.repositories.repository import SnippetRepository

SNIPPETS = APIRouter(tags=["Snippets"])
GISTS = APIRouter(tags=["Gists"])


@SNIPPETS.post(
    "/snippets/v1/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
def create_snippet(
    *, repo: SnippetRepository = Depends(get_repo), snippet: SnippetCreate
):
    snippet_data = snippet.model_dump()
    try:
        db_snippet = Snippet(**snippet_data)
    except PydanticValidationError as e:
        errors = {err["loc"][0]: err["msg"] for err in e.errors()}
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=errors
        )
    try:
        repo.add(db_snippet)
        logger.debug(f"Snippet with title '{db_snippet.title}' created")
    except DuplicateSnippetError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Snippet already exists"
        ) from err
    except RepositoryError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        ) from err
    return {"message": f"Successfully created Snippet with title '{db_snippet.title}'"}


@SNIPPETS.get("/snippets/v1/list/", response_model=list[SnippetResponse])
def list_snippets(*, repo: SnippetRepository = Depends(get_repo)):
    try:
        snippets = repo.list()
        if snippets:
            logger.debug(f"{len(snippets)} snippets found in repository")
            return snippets
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No snippets in repository"
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


@SNIPPETS.get("/snippets/v1/{snippet_id}", response_model=SnippetResponse)
def get_snippet(*, repo: SnippetRepository = Depends(get_repo), snippet_id: int):
    try:
        snippet = repo.get(snippet_id)
        if snippet:
            return snippet
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snippet '{snippet_id}' not found",
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


@SNIPPETS.delete("/snippets/v1/{snippet_id}", response_model=MessageResponse)
def delete_snippet(*, repo: SnippetRepository = Depends(get_repo), snippet_id: int):
    try:
        repo.delete(snippet_id)
        logger.debug(f"Snippet '{snippet_id}' deleted successfully")
    except SnippetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snippet '{snippet_id}' not found",
        )
    except MultipleSnippetsFoundError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Multiple snippets found for snippet {snippet_id}",
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )
    return {"message": f"Snippet '{snippet_id}' deleted successfully"}


@SNIPPETS.get("/snippets/v1/search/", response_model=list[SnippetResponse])
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
        logger.warning(
            f"Search found no matches for term '{term}' and language '{language}'"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Search yielded no snippets"
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


@SNIPPETS.post("/snippets/v1/{snippet_id}/favourite", response_model=MessageResponse)
def toggle_favourite(*, repo: SnippetRepository = Depends(get_repo), snippet_id: int):
    try:
        favourited = repo.toggle_favourite(snippet_id)
        action = "Favourited" if favourited else "Unfavourited"
        logger.debug(f"Snippet '{snippet_id}' {action}")
    except SnippetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snippet '{snippet_id}' not found",
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )
    return {"message": f"Snippet '{snippet_id}' is {action}"}


@SNIPPETS.post("/snippets/v1/{snippet_id}/tags", response_model=MessageResponse)
def tag_snippet(
    *,
    repo: SnippetRepository = Depends(get_repo),
    snippet_id: int,
    tags: list[str] = Query(...),
    remove: bool = False,
    sort: bool = True,
):
    try:
        repo.tags(snippet_id, *tags, remove=remove, sort=sort)
        logger.debug(f"Tag snippets for snippet '{snippet_id}'")
    except SnippetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snippet '{snippet_id}' not found",
        )
    except RepositoryError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )
    if remove:
        return {
            "message": f"Successfully removed the following tags '{", ".join(tags)}' for snippet '{snippet_id}'"
        }
    return {"message": f"Successfully tagged snippet '{snippet_id}'"}


@GISTS.post(
    "/gists/v1/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_gist(*, repo: SnippetRepository = Depends(get_repo), gist: GistCreate):
    gist_data = gist.model_dump()
    logger.debug(f"Gist create request {gist_data}")
    snippet_id = gist_data.get("snippet_id")
    is_public = gist_data.get("is_public")

    try:
        snippet = repo.get(snippet_id)
        if not snippet:
            logger.debug(f"Snippet '{snippet_id}' not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Snippet '{snippet_id}' not found",
            )
    except (DatabaseConnectionError, RepositoryError) as err:
        logger.debug("Repository error")
        if err.__cause__:
            logger.debug(f"{err.__cause__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gist creation failed due to repository error",
        )

    try:
        repo.create_gist(
            snippet_id,
            snippet.code,
            snippet.title,
            snippet.language,
            is_public=is_public,
        )
        logger.debug(f"Gist added for snippet '{snippet_id}'")
    except DuplicateGistError:
        logger.debug(f"Duplicate gist found for snippet '{snippet_id}'")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate gist found for snippet '{snippet_id}'",
        )
    except (DatabaseConnectionError, RepositoryError) as err:
        logger.debug("Repository error")
        if err.__cause__:
            logger.debug(f"{err.__cause__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gist creation failed due to repository error",
        )
    return {"message": f"Successfully created Gist with title '{snippet.title}'"}


@GISTS.get(
    "/gists/v1/list",
    response_model=list[GistResponse],
)
def list_gists(*, repo: SnippetRepository = Depends(get_repo), active: bool = True):
    try:
        gists = repo.list_gist()
        if gists:
            if active:
                active_gists = [gist for gist in gists if gist.status == "active"]
                logger.debug(
                    f"{len(active_gists)} active gists found in the repository"
                )
                return active_gists
            else:
                logger.debug(f"{len(gists)} gists found in the repository")
                return gists
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No gists in the repository"
        )
    except (DatabaseConnectionError, RepositoryError) as err:
        logger.debug("Repository error")
        if err.__cause__:
            logger.debug(f"{err.__cause__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository error",
        )


@GISTS.delete(
    "/gists/v1/{snippet_id}/",
    response_model=MessageResponse,
)
def delete_gist(*, repo: SnippetRepository = Depends(get_repo), snippet_id: int):
    try:
        repo.delete_gist(snippet_id)
        logger.debug(f"Gist with snippet id '{snippet_id}' deleted successfully")
    except GistNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gist with snippet id '{snippet_id}' not found",
        )
    except MultipleSnippetsFoundError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Multiple gists found for snippet id '{snippet_id}'",
        )
    except (DatabaseConnectionError, RepositoryError) as err:
        logger.debug("Repository error")
        if err.__cause__:
            logger.debug(f"{err.__cause__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Repository error"
        )
    return {"message": f"Gist with snippet id '{snippet_id}' deleted successfully"}
