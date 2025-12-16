"""Database manager works with any SQLModel"""

from typing import List, Optional, Type

from loguru import logger
from sqlalchemy.exc import IntegrityError, NoResultFound, OperationalError
from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
    select,
)


class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///snippets.db", echo: bool = False):
        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=echo)
        self.create_db_and_models()

    def create_db_and_models(self):
        """Create databse and models/tables"""
        SQLModel.metadata.create_all(self.engine)
        logger.info("Database and models created")

    def select_by_id(self, model: Type[SQLModel], id: int) -> Optional[SQLModel | None]:
        """
        Fetch a single record by its primary key.

        Args:
            model: The SQLModel class to query
            id: Primary key value of the record to retrieve

        Returns:
            The matching record if found, None otherwise
        """
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

    def select_all(
        self, model: Type[SQLModel], limit: int = None
    ) -> Optional[List[SQLModel] | None]:
        """
        Fetch all records from a model table.

        Args:
            model: The SQLModel class to query
            limit: Maximum number of records to return (optional)

        Returns:
            List of all matching records, or empty list if none found
        """
        with Session(self.engine) as session:
            try:
                statement = select(model).limit(limit)
                results = session.exec(statement)
                return results.all()
            except OperationalError as err:
                logger.error(
                    f"Select all records on model {model.__name__} failed: {err}"
                )
            except NoResultFound:  # pragma: no cover
                logger.warning(f"No result found in model {model.__name__}")

    @staticmethod
    def _retry_failed_batches(session, records: List[SQLModel]):
        """Attempt failed batches"""
        session.add_all(records)
        session.commit()

    def insert_records(
        self,
        model: Type[SQLModel],
        records: List[SQLModel],
        batch_size: int = 1,
    ) -> int:
        """
        Insert records into the database with duplicate handling.

        Args:
            model: The SQLModel class to insert records into
            records: List of model instances to insert
            batch_size: Number of records to insert per transaction

        Returns:
            Number of records successfully inserted
        """
        n_rows_inserted, n_dups = 0, 0
        with Session(self.engine) as session:
            n_rows = len(records)
            for row in range(0, n_rows, batch_size):
                logger.debug(f"Processing batch {row}..{row + batch_size}")
                try:
                    self._retry_failed_batches(session, records[row : row + batch_size])
                except IntegrityError:
                    logger.warning(
                        f"Duplicate record found in batch {row}..{row + batch_size}. Skipping"
                    )
                    session.rollback()
                    logger.info("Retrying failed batches")
                    failed_batches = records[row : row + batch_size]
                    for record in failed_batches:
                        try:
                            self._retry_failed_batches(session, [record])
                        except IntegrityError:
                            session.rollback()
                            n_dups += 1
                except OperationalError as err:
                    logger.error(
                        f"Insert statement failed for model {model.__name__}: {err}"
                    )
                    session.rollback()

        if n_dups > 0:
            logger.info(f"Number of duplicates skipped {n_dups}")
        n_rows_inserted = n_rows - n_dups
        logger.info(
            f"Successfully inserted {n_rows_inserted} records into model {model.__name__}"
        )

        return n_rows_inserted


if __name__ == "__main__":  # pragma: no cover
    snippet_db = DatabaseManager()
