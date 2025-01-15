import os
from sqlalchemy import create_engine, event, Table, MetaData, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configurations from environment variables
PRIMARY_DB_URL = os.getenv("PRIMARY_DB_URL", "postgresql+psycopg2://user:password@localhost/primary_db")
SECONDARY_DB_URL = os.getenv("SECONDARY_DB_URL", "postgresql+psycopg2://user:password@localhost/secondary_db")

# Create engines for both databases
primary_engine = create_engine(PRIMARY_DB_URL)
secondary_engine = create_engine(SECONDARY_DB_URL)

# Create session factories
PrimarySession = sessionmaker(bind=primary_engine)
SecondarySession = sessionmaker(bind=secondary_engine)

# Metadata instances
primary_metadata = MetaData(bind=primary_engine)
secondary_metadata = MetaData(bind=secondary_engine)

def create_table_if_not_exists(table_name):
    """Ensure the table exists in the secondary database."""
    if table_name not in secondary_metadata.tables:
        logger.info(f"Table '{table_name}' does not exist in secondary database. Creating...")
        primary_table = Table(table_name, primary_metadata, autoload_with=primary_engine)
        primary_table.metadata.create_all(secondary_engine)
        logger.info(f"Table '{table_name}' created in secondary database.")

def create_sync_tracking_table():
    """Create a table to track synchronization data."""
    tracking_table_name = 'sync_tracking'
    if tracking_table_name not in secondary_metadata.tables:
        logger.info(f"Creating sync tracking table '{tracking_table_name}' in secondary database...")
        tracking_table = Table(
            tracking_table_name,
            secondary_metadata,
            Column('id', Integer, primary_key=True),
            Column('table_name', String, nullable=False),
            Column('last_synced_at', DateTime, nullable=False)
        )
        tracking_table.create(secondary_engine)
        logger.info(f"Sync tracking table '{tracking_table_name}' created.")

def is_first_run():
    """Check if this is the first run based on sync_tracking table."""
    tracking_table = Table('sync_tracking', secondary_metadata, autoload_with=secondary_engine)
    secondary_session = SecondarySession()
    try:
        result = secondary_session.execute(tracking_table.select()).fetchall()
        return len(result) == 0
    except Exception as e:
        logger.error(f"Error checking first run status: {e}")
        return True
    finally:
        secondary_session.close()

def update_sync_tracking(table_name):
    """Update the sync tracking table with the last sync time."""
    tracking_table = Table('sync_tracking', secondary_metadata, autoload_with=secondary_engine)
    secondary_session = SecondarySession()
    try:
        now = datetime.utcnow()
        existing_entry = secondary_session.execute(
            tracking_table.select().where(tracking_table.c.table_name == table_name)
        ).fetchone()

        if existing_entry:
            secondary_session.execute(
                tracking_table.update()
                .where(tracking_table.c.table_name == table_name)
                .values(last_synced_at=now)
            )
        else:
            secondary_session.execute(
                tracking_table.insert().values(table_name=table_name, last_synced_at=now)
            )

        secondary_session.commit()
        logger.info(f"Sync tracking updated for table '{table_name}'.")
    except Exception as e:
        secondary_session.rollback()
        logger.error(f"Failed to update sync tracking for table '{table_name}': {e}")
    finally:
        secondary_session.close()

def sync_table_changes(table_names):
    """Sync changes from primary to secondary for an array of tables."""
    primary_session = PrimarySession()
    secondary_session = SecondarySession()

    try:
        for table_name in table_names:
            create_table_if_not_exists(table_name)
            primary_table = Table(table_name, primary_metadata, autoload_with=primary_engine)
            secondary_table = Table(table_name, secondary_metadata, autoload_with=secondary_engine)

            primary_data = primary_session.execute(primary_table.select()).fetchall()
            secondary_session.execute(secondary_table.delete())  # Clear secondary table

            for row in primary_data:
                secondary_session.execute(secondary_table.insert().values(**row._asdict()))

            update_sync_tracking(table_name)  # Track sync time for this table

        secondary_session.commit()
        logger.info(f"Tables {table_names} synchronized successfully.")
    except Exception as e:
        secondary_session.rollback()
        logger.error(f"Error syncing tables {table_names}: {e}")
    finally:
        primary_session.close()
        secondary_session.close()

# Listen to events on primary database
def after_insert(mapper, connection, table_name):
    logger.info(f"Insert detected on table '{table_name}'. Syncing...")
    sync_table_changes([table_name])

def after_update(mapper, connection, table_name):
    logger.info(f"Update detected on table '{table_name}'. Syncing...")
    sync_table_changes([table_name])

def after_delete(mapper, connection, table_name):
    logger.info(f"Delete detected on table '{table_name}'. Syncing...")
    sync_table_changes([table_name])

if __name__ == "__main__":
    # Specify tables to sync
    tables_to_sync = ['example_table', 'another_table']

    # Ensure tables exist in both databases
    primary_metadata.reflect()
    secondary_metadata.reflect()

    create_sync_tracking_table()  # Create tracking table

    if is_first_run():
        logger.info("First run detected. Synchronizing all data...")
        sync_table_changes(tables_to_sync)
    else:
        logger.info("Not the first run. Regular synchronization setup.")

    for table_name in tables_to_sync:
        if table_name in primary_metadata.tables:
            logger.info(f"Setting up synchronization for table '{table_name}'")
        else:
            logger.error(f"Table '{table_name}' does not exist in the primary database.")

    logger.info("Synchronization setup complete.")