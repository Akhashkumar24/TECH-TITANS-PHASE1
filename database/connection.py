# database/connection.py
import os
from contextlib import contextmanager

# Try to import psycopg2 with helpful error message
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("ERROR: psycopg2 not installed!")
    print("Please install it using: pip install psycopg2-binary")

# Try to load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseConnection:
    def __init__(self):
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required but not installed. Run: pip install psycopg2-binary")
        
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'job_matching_db')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self):
        """Validate database configuration"""
        if not self.user:
            raise ValueError("Database user not configured. Set DB_USER environment variable.")
        
        if not self.password and self.user != 'postgres':
            logger.warning("Database password not set. This may cause connection issues.")
        
        if not self.database:
            raise ValueError("Database name not configured. Set DB_NAME environment variable.")
    
    def get_connection_string(self):
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(
                self.get_connection_string(),
                cursor_factory=RealDictCursor
            )
            conn.autocommit = False
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Unexpected database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation error: {e}")
                raise
            finally:
                cursor.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
