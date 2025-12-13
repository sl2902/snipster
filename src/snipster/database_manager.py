"""Database manager works with any SQLModel"""

from typing import Type

from loguru import logger
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
    select,
)


class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///snippets.db"):
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=True)
        self.create_db_and_models()

    def create_db_and_models(self):
        """Create databse and models/tables"""
        SQLModel.metadata.create_all(self.engine)
        logger.info("Database and models created")

    def select_by_snippet_id(self, model: Type[SQLModel], id: int):
        """Fetch snippet by id"""
        with Session(self.engine) as session:
            try:
                return session.get(model, id)
            except OperationalError as err:
                logger.error(f"Select by id {id} on model {model} failed: {err}")
            except NoResultFound:
                logger.warning(f"No result found for id {id} from model {model}")

    def select_all(self, model: Type[SQLModel], limit: int = None):
        """Fetch all (limit) records from the model"""
        with Session(self.engine) as session:
            try:
                statement = select(model)
                return session.exec(statement)
            except OperationalError as err:
                logger.error(f"Select all records on model {model} failed: {err}")
            except NoResultFound:
                logger.warning(f"No result found in model {model}")


if __name__ == "__main__":
    snippet_db = DatabaseManager()
