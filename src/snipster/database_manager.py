"""Database manager works with any SQLModel"""

from typing import List, Type

from loguru import logger
from sqlalchemy.exc import IntegrityError, NoResultFound, OperationalError
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

    def select_by_snippet_id(self, model: Type[SQLModel], id: int) -> SQLModel:
        """Fetch snippet by id"""
        with Session(self.engine) as session:
            try:
                return session.get(model, id)
            except OperationalError as err:
                logger.error(
                    f"Select by id {id} on model {model.__name__} failed: {err}"
                )
            except NoResultFound:  # pragma: no cover
                logger.warning(
                    f"No result found for id {id} from model {model.__name__}"
                )

    def select_all(self, model: Type[SQLModel], limit: int = None) -> List[SQLModel]:
        """Fetch all (limit) records from the model"""
        with Session(self.engine) as session:
            try:
                statement = select(model)
                results = session.exec(statement)
                return results.all()
            except OperationalError as err:
                logger.error(
                    f"Select all records on model {model.__name__} failed: {err}"
                )
            except NoResultFound:  # pragma: no cover
                logger.warning(f"No result found in model {model.__name__}")

    def insert_records(
        self, model: Type[SQLModel], records: List[SQLModel], batch_size: int = 1
    ) -> int:
        """Insert or Create records in model"""
        n_rows_inserted, n_dups = 0, 0
        with Session(self.engine) as session:
            n_rows = len(records)
            for row in range(0, n_rows, batch_size):
                try:
                    session.add_all(records[row : row + batch_size])
                    session.commit()
                    n_rows_inserted += len(records[row : row + batch_size])
                    logger.debug(f"{n_rows_inserted} records successfully inserted")
                except IntegrityError:
                    n_dups += 1
                    logger.warning("Duplicate record found. Skipping")
                    session.rollback()
                except OperationalError as err:
                    logger.error(
                        f"Insert statement failed for model {model.__name__}: {err}"
                    )
                    session.rollback()
                    raise

        if n_dups > 0:
            logger.info(f"Number of duplicates skipped {n_dups}")
        logger.info(
            f"Successfully inserted {n_rows_inserted} records into model {model.__name__}"
        )

        return n_rows_inserted


if __name__ == "__main__":  # pragma: no cover
    snippet_db = DatabaseManager()
