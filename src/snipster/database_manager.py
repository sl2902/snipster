"""Database manager works with any SQLModel"""

from datetime import datetime, timezone
from typing import Any, Type

from decouple import config
from loguru import logger
from sqlalchemy import func
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

from snipster.exceptions import (
    DuplicateSnippetError,
    RepositoryError,
    SnippetNotFoundError,
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
            RepositoryError: If the database operation fails.
        """
        with Session(self.engine) as session:
            try:
                return session.get(model, pk)
            except OperationalError as err:
                logger.error(
                    f"Select by id {pk} on model {model.__name__} failed: {err}"
                )
                raise RepositoryError(
                    f"Select by id {pk} on model {model.__name__} failed: {err}"
                ) from err

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
            RepositoryError: If the database operation fails.
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
                raise RepositoryError(
                    f"Select all records on model {model.__name__} failed: {err}"
                ) from err
            except NoResultFound:  # pragma: no cover
                logger.warning(f"No result found in model {model.__name__}")

    def select_with_filter(
        self, model: Type[SQLModel], col: str, term: str = ""
    ) -> list[SQLModel] | None:
        """
        Filter records by partial matching from a model table.

        Args:
            model: The SQLModel class to query
            col: Model field to filter on
            term: Pattern to match (optional)

        Returns:
            List of all matching records, or empty list if none found

        Raises:
            RepositoryError: If the database operation fails.
        """
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        with Session(self.engine) as session:
            try:
                if not hasattr(model, col):
                    raise ValueError(
                        f"Column '{col}' does not exist in model {model.__name__}"
                    )

                column = getattr(model, col)
                statement = select(model).filter(
                    func.coalesce(column, "").ilike(f"%{escaped}%", escape="\\")
                )
                results = session.exec(statement)
                return results.all()
            except OperationalError as err:
                logger.error(
                    f"Select by filter on model {model.__name__} failed: {err}"
                )
                raise RepositoryError(
                    f"Select by filter on model {model.__name__} failed: {err}"
                ) from err

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
            None

        Raises:
            DuplicateSnippetError: If a duplicate snippet was inserted.
            RepositoryError: If the database operation fails.
        """
        with Session(self.engine) as session:
            logger.debug("Inserting single model instance")
            try:
                self._load_batches(session, [record])
            except IntegrityError as err:
                logger.warning(f"Duplicate record found in model {model.__name__}.")
                session.rollback()
                raise DuplicateSnippetError(
                    f"Duplicate record found in model {model.__name__}."
                ) from err
            except OperationalError as err:
                logger.error(
                    f"Insert statement failed for model {model.__name__}: {err}"
                )
                session.rollback()
                raise RepositoryError(
                    f"Insert statement failed for model {model.__name__}: {err}"
                ) from err

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

    def delete_record(self, model: SQLModel, pk: int) -> None:
        """
        Delete single record from the database.

        Args:
            model: The SQLModel class to insert a single record
            pk: Unique record identifer

        Returns:
            None

        Raises:
            RepositoryError: If the database operation fails.
        """
        with Session(self.engine) as session:
            logger.debug("Deleting single model instance")
            try:
                statement = select(model).where(model.id == pk)
                record = session.exec(statement)
                to_delete = record.one()
                logger.debug(f"Record to delete {to_delete}")
                session.delete(to_delete)
                session.commit()
            except NoResultFound as err:
                logger.error(
                    f"Record with id {pk} does not exist in model {model.__name__}"
                )
                raise SnippetNotFoundError(
                    f"Record with id {pk} does not exist in model {model.__name__}"
                ) from err
            except MultipleResultsFound as err:
                session.rollback()
                logger.error(
                    f"Multiple results found for id {pk} in. model {model.__name__}: {err}"
                )
                raise
            except OperationalError as err:
                session.rollback()
                logger.error(
                    f"Delete statement failed for id {pk} in model {model.__name__}: {err}"
                )
                raise RepositoryError(
                    f"Delete statement failed for id {pk} in model {model.__name__}: {err}"
                ) from err

        logger.info(f"Successfully deleted record id {pk} from model {model.__name__}")

    def update(self, model: SQLModel, pk: int, col: str, value: Any) -> None:
        """
        Update single record from the database.

        Args:
            model: The SQLModel class to update a single record
            pk: Unique record identifer
            col: Model field to update
            value: New value to replace the old value

        Returns:
            None

        Raises:
            RepositoryError: If the database operation fails.
        """
        with Session(self.engine) as session:
            logger.debug(f"Updating single model instance id {pk}")
            try:
                if not hasattr(model, col):
                    raise ValueError(
                        f"Column '{col}' does not exist in model {model.__name__}"
                    )
                statement = select(model).where(model.id == pk)
                record = session.exec(statement)
                model_obj = record.one()

                setattr(model_obj, col, value)
                setattr(model_obj, "updated_at", datetime.now(timezone.utc))
                session.add(model_obj)
                session.commit()
                session.refresh(model_obj)
            except NoResultFound as err:
                logger.error(
                    f"Record with id {pk} does not exist in model {model.__name__}"
                )
                raise SnippetNotFoundError(
                    f"Record with id {pk} does not exist in model {model.__name__}"
                ) from err
            except OperationalError as err:
                logger.error(
                    f"Update statement failed for id {pk} in model {model.__name__}: {err}"
                )
                session.rollback()
                raise RepositoryError(
                    f"Update failed for {model.__name__} id {pk}: {err}"
                ) from err


if __name__ == "__main__":  # pragma: no cover
    snippet_db = DatabaseManager()
