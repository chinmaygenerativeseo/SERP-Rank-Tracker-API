import os
import sys
import logging
from typing import Optional, Generator, Any
from contextlib import contextmanager
import pyodbc
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
    A robust, production-grade connection manager for Microsoft SQL Server.
    Supports auto-driver detection, context managers, and dual auth modes.
    """
    
    def __init__(self):
        self.server = os.getenv("DB_SERVER")
        self.port = os.getenv("DB_PORT", "1433")
        self.database = os.getenv("DB_DATABASE")
        self.use_windows_auth = os.getenv("DB_USE_WINDOWS_AUTH", "false").lower() == "true"
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = os.getenv("DB_DRIVER")
        self.encrypt = os.getenv("DB_ENCRYPT", "yes")
        self.trust_server_certificate = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")
        
        # Auto-detect driver if not explicitly specified
        if not self.driver:
            self.driver = self._detect_best_driver()
            
    def _detect_best_driver(self) -> str:
        """
        Scans the system for installed Microsoft SQL Server ODBC drivers and returns the newest one.
        """
        try:
            drivers = pyodbc.drivers()
            # Filter for SQL Server drivers
            sql_drivers = [d for d in drivers if "SQL Server" in d or "ODBC Driver" in d]
            
            if not sql_drivers:
                raise RuntimeError(
                    "No SQL Server ODBC drivers found on this system! "
                    "Please install Microsoft ODBC Driver for SQL Server."
                )
                
            # Prioritize ODBC Driver 18, then 17, then standard SQL Server
            priorities = [
                "ODBC Driver 18 for SQL Server",
                "ODBC Driver 17 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server"
            ]
            
            for p in priorities:
                if p in sql_drivers:
                    logger.info(f"Auto-detected driver: {p}")
                    return p
                    
            # Fallback to the first available SQL driver
            logger.info(f"Auto-detected driver: {sql_drivers[0]}")
            return sql_drivers[0]
            
        except Exception as e:
            logger.error(f"Error detecting SQL Server ODBC drivers: {e}")
            # Fallback default
            return "ODBC Driver 18 for SQL Server"

    def build_connection_string(self) -> str:
        """
        Constructs the connection string based on configuration and auth mode.
        """
        if not self.server:
            raise ValueError("DB_SERVER environment variable is not defined.")
        if not self.database:
            raise ValueError("DB_DATABASE environment variable is not defined.")
            
        conn_parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server},{self.port}",
            f"DATABASE={self.database}",
            f"Encrypt={self.encrypt}",
            f"TrustServerCertificate={self.trust_server_certificate}",
            "Connection Timeout=30"
        ]
        
        if self.use_windows_auth:
            # Integrated Windows Authentication
            conn_parts.append("Trusted_Connection=yes")
            logger.info(f"Connecting to {self.server}/{self.database} using Windows Authentication.")
        else:
            # Standard SQL Server Authentication
            if not self.username or not self.password:
                raise ValueError("DB_USERNAME and DB_PASSWORD must be specified for SQL Server Authentication.")
            conn_parts.append(f"UID={self.username}")
            conn_parts.append(f"PWD={self.password}")
            logger.info(f"Connecting to {self.server}/{self.database} as user '{self.username}'.")
            
        return ";".join(conn_parts)

    @contextmanager
    def get_connection(self) -> Generator[pyodbc.Connection, None, None]:
        """
        Context manager for safely getting and releasing a connection.
        Ensures resources are cleaned up properly even in case of errors.
        """
        conn = None
        try:
            conn_str = self.build_connection_string()
            conn = pyodbc.connect(conn_str)
            yield conn
        except pyodbc.Error as e:
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
    def get_cursor(self) -> Generator[pyodbc.Cursor, None, None]:
        """
        Context manager for getting a cursor, executing operations, and committing changes.
        Rolls back transactions on exception.
        """
        with self.get_connection() as conn:
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
    Dependency injector that yields a thread-safe, pooled database cursor.
    Guarantees automatic commit on success and rollback on exception.
    """
    with db_manager.get_cursor() as cursor:
        yield cursor

