"""Database manager works with any SQLModel"""

from typing import Type

from decouple import config
from loguru import logger
from sqlalchemy.exc import (
    IntegrityError,
    MultipleResultsFound,
    NoResultFound,
    OperationalError,
)
from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
    select,
)


class DatabaseManager:
    def __init__(self, db_url: str | None = None, echo: bool = False):
        if db_url is None:
            db_url = config("DATABASE_URL", default="sqlite:///snippets.db")

        if db_url.strip() == "":
            raise ValueError("db_url cannot be empty")

        self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=echo)
        self.create_db_and_models()

    def create_db_and_models(self):
        """Create database and models/tables"""
        SQLModel.metadata.create_all(self.engine)
        logger.info("Database and models created")

    def select_by_id(self, model: Type[SQLModel], pk: int) -> SQLModel | None:
        """
        Fetch a single record by its primary key.

        Args:
            model: The SQLModel class to query
            pk: Primary key value of the record to retrieve

        Returns:
            The matching record if found, None otherwise

        Raises:
            OperationalError: If the database operation fails.
        """
        with Session(self.engine) as session:
            try:
                return session.get(model, pk)
            except OperationalError as err:
                logger.error(
                    f"Select by id {pk} on model {model.__name__} failed: {err}"
                )
                raise

    def select_all(
        self, model: Type[SQLModel], limit: int = None
    ) -> list[SQLModel] | None:
        """
        Fetch all records from a model table.

        Args:
            model: The SQLModel class to query
            limit: Maximum number of records to return (optional)

        Returns:
            List of all matching records, or empty list if none found

        Raises:
            OperationalError: If the database operation fails.
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
                raise
            except NoResultFound:  # pragma: no cover
                logger.warning(f"No result found in model {model.__name__}")

    @staticmethod
    def _load_batches(session, records: list[SQLModel]):
        """Load batches into table"""
        session.add_all(records)
        session.commit()
        for record in records:
            session.refresh(record)

    def insert_record(
        self,
        model: Type[SQLModel],
        record: SQLModel,
    ) -> bool:
        """
        Insert single record into the database with duplicate handling.

        Args:
            model: The SQLModel class to insert a single record
            record: Single model instance to insert

        Returns:
            bool
        """
        with Session(self.engine) as session:
            logger.debug("Inserting single model instance")
            try:
                self._load_batches(session, [record])
            except IntegrityError:
                logger.warning("Duplicate record found in table.")
                session.rollback()
                return False
            except OperationalError as err:
                logger.error(
                    f"Insert statement failed for model {model.__name__}: {err}"
                )
                session.rollback()
                return False

        logger.info(f"Successfully inserted record into model {model.__name__}")
        return True

    def insert_records(
        self,
        model: Type[SQLModel],
        records: list[SQLModel],
        batch_size: int = int(config("DEFAULT_BATCH_SIZE", 1)),
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
                    self._load_batches(session, records[row : row + batch_size])
                except IntegrityError:
                    logger.warning(
                        f"Duplicate record found in batch {row}..{row + batch_size}."
                    )
                    session.rollback()
                    logger.info("Retrying failed batches")
                    failed_batches = records[row : row + batch_size]
                    for record in failed_batches:
                        try:
                            self._load_batches(session, [record])
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

    def delete_record(self, model: SQLModel, id: int) -> bool:
        """
        Delete single record from the database.

        Args:
            model: The SQLModel class to insert a single record
            id: Unique record identifer

        Returns:
            bool
        """
        with Session(self.engine) as session:
            logger.debug("Deleting single model instance")
            try:
                statement = select(model).where(model.id == id)
                record = session.exec(statement)
                to_delete = record.one()
                logger.debug(f"Record to delete {to_delete}")
                session.delete(to_delete)
                session.commit()
            except NoResultFound:
                logger.warning(
                    f"Record with id {id} does not exist in model {model.__name__}"
                )
                return False
            except MultipleResultsFound as err:
                session.rollback()
                logger.error(
                    f"Multiple results found for id {id} in. model {model.__name__}: {err}"
                )
                raise
            except OperationalError as err:
                logger.error(
                    f"Delete statement failed for id {id} in model {model.__name__}: {err}"
                )
                session.rollback()
                return False

        logger.info(f"Successfully deleted record id {id} from model {model.__name__}")
        return True


if __name__ == "__main__":  # pragma: no cover
    snippet_db = DatabaseManager()
