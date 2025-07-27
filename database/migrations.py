# database/migrations.py
import os
from database.connection import DatabaseConnection
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def run_migrations(self):
        """Run database migrations"""
        try:
            # Test connection first
            if not self.db.test_connection():
                raise Exception("Cannot connect to database. Check your configuration.")
            
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if not os.path.exists(schema_path):
                # Create schema content inline if file doesn't exist
                schema_sql = self._get_inline_schema()
            else:
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
            
            with self.db.get_cursor() as cursor:
                cursor.execute(schema_sql)
                logger.info("Database migrations completed successfully")
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def _get_inline_schema(self):
        """Return inline schema if file doesn't exist"""
        return """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) CHECK (role IN ('job_seeker', 'admin')) NOT NULL,
            full_name VARCHAR(200),
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Jobs table
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT,
            skills_required TEXT[],
            experience_level VARCHAR(50),
            salary_range VARCHAR(100),
            location VARCHAR(200),
            company_name VARCHAR(200),
            posted_by INTEGER REFERENCES users(id),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Applications table
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            job_id INTEGER REFERENCES jobs(id),
            resume_path VARCHAR(500),
            resume_text TEXT,
            cover_letter TEXT,
            status VARCHAR(50) DEFAULT 'submitted',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, job_id)
        );

        -- Rankings table
        CREATE TABLE IF NOT EXISTS rankings (
            id SERIAL PRIMARY KEY,
            job_id INTEGER REFERENCES jobs(id),
            application_id INTEGER REFERENCES applications(id),
            similarity_score DECIMAL(5,4),
            rank_position INTEGER,
            ranking_details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_id, application_id)
        );

        -- Agent logs table
        CREATE TABLE IF NOT EXISTS agent_logs (
            id SERIAL PRIMARY KEY,
            agent_type VARCHAR(50),
            action VARCHAR(100),
            job_id INTEGER REFERENCES jobs(id),
            application_id INTEGER REFERENCES applications(id),
            message TEXT,
            status VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(is_active);
        CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
        CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
        CREATE INDEX IF NOT EXISTS idx_rankings_job_id ON rankings(job_id);
        CREATE INDEX IF NOT EXISTS idx_rankings_similarity_score ON rankings(similarity_score DESC);
        """
    
    def create_admin_user(self):
        """Create default admin user"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, full_name)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, ('admin', 'admin@jobmatch.com', 'admin123', 'admin', 'System Administrator'))
                
                if cursor.rowcount > 0:
                    logger.info("Default admin user created (username: admin, password: admin123)")
                else:
                    logger.info("Admin user already exists")
                    
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
