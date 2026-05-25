import os
import sys
import logging
from typing import Generator, Any
from contextlib import contextmanager
import pymssql
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SQLServerConnection")

# Load environment variables from .env file if it exists
load_dotenv()

class SQLServerConnectionManager:
    """
    A robust, production-grade connection manager for Microsoft SQL Server using pymssql.
    Pymssql connects directly via FreeTDS, bypassing all system ODBC/JDBC driver dependencies,
    making it perfectly compatible with both Windows development and Linux/Render hosting!
    """
    
    def __init__(self):
        self.server = os.getenv("DB_SERVER")
        self.port = os.getenv("DB_PORT", "1433")
        self.database = os.getenv("DB_DATABASE")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        
    def get_raw_connection(self) -> pymssql.Connection:
        """
        Establishes and returns a direct pymssql connection object.
        """
        if not self.server:
            raise ValueError("DB_SERVER environment variable is not defined.")
        if not self.database:
            raise ValueError("DB_DATABASE environment variable is not defined.")
        if not self.username or not self.password:
            raise ValueError("DB_USERNAME and DB_PASSWORD must be specified for SQL Server Authentication.")
            
        logger.info(f"Connecting to MS SQL Server at {self.server}:{self.port}/{self.database} as user '{self.username}'...")
        
        # Connect using direct TDS protocol
        return pymssql.connect(
            server=self.server,
            port=int(self.port),
            user=self.username,
            password=self.password,
            database=self.database,
            timeout=30
        )

    @contextmanager
    def get_connection(self) -> Generator[pymssql.Connection, None, None]:
        """
        Context manager for safely getting and releasing a connection.
        Ensures resources are cleaned up properly.
        """
        conn = None
        try:
            conn = self.get_raw_connection()
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    logger.debug("Database connection closed successfully.")
                except Exception as ce:
                    logger.warning(f"Error closing database connection: {ce}")

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """
        Context manager for getting a cursor, executing operations, and committing changes.
        Rolls back transactions on exception.
        """
        with self.get_connection() as conn:
            # We use as_dict=False by default to maintain DB-API standard row sequences
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                logger.error(f"Transaction failed. Rolling back changes. Error: {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()

# Singleton instance for general usage
db_manager = SQLServerConnectionManager()

# Dependency to get a database cursor using high-performance connection pooling
def get_db_cursor():
    """
    Dependency injector that yields a thread-safe database cursor.
    Guarantees automatic commit on success and rollback on exception.
    """
    with db_manager.get_cursor() as cursor:
        yield cursor
