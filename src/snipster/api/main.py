"""FastAPI entrypoint"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from snipster.api.routes import router
from snipster.repositories.backend import create_repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create repository"""
    app.state.repo = create_repository()
    yield
    app.state.repo.db_manager.engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(router)
