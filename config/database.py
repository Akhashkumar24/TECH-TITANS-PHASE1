# config/database.py
from database.connection import DatabaseConnection

# Global database instance
try:
    db_connection = DatabaseConnection()
except Exception as e:
    print(f"Warning: Could not initialize database connection: {e}")
    db_connection = None