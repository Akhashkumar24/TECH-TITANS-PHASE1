# services/auth_service.py
import hashlib
from typing import Optional
from models.user import User
from config.database import db_connection
from utils.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    # Fixed admin credentials - only one admin allowed
    ADMIN_USERNAME = "admin"
    ADMIN_EMAIL = "admin@jobmatch.com"
    ADMIN_PASSWORD_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # "admin123"
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return AuthService.hash_password(password) == hashed
    
    @staticmethod
    def initialize_admin() -> bool:
        """Initialize the single admin user in database"""
        try:
            with db_connection.get_cursor() as cursor:
                # Check if admin already exists
                cursor.execute("""
                    SELECT id FROM users WHERE username = %s OR role = 'admin'
                """, (AuthService.ADMIN_USERNAME,))
                
                if cursor.fetchone():
                    logger.info("Admin user already exists")
                    return True
                
                # Create the admin user
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, full_name)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    AuthService.ADMIN_USERNAME,
                    AuthService.ADMIN_EMAIL,
                    AuthService.ADMIN_PASSWORD_HASH,
                    'admin',
                    'System Administrator'
                ))
                
                logger.info("Admin user created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize admin: {e}")
            return False
    
    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: str = None) -> Optional[User]:
        """Register a new job seeker (admin registration is not allowed)"""
        try:
            # Prevent admin registration
            if username.lower() == AuthService.ADMIN_USERNAME.lower():
                logger.warning(f"Attempted admin registration blocked for username: {username}")
                return None
            
            # Check if email is admin email
            if email.lower() == AuthService.ADMIN_EMAIL.lower():
                logger.warning(f"Attempted registration with admin email blocked: {email}")
                return None
            
            # Check for existing users
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM users WHERE username = %s OR email = %s
                """, (username, email))
                
                if cursor.fetchone():
                    logger.warning(f"User already exists: {username} or {email}")
                    return None
                
                # Create new job seeker
                password_hash = AuthService.hash_password(password)
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, full_name)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username, email, role, full_name, created_at
                """, (username, email, password_hash, 'job_seeker', full_name))
                
                result = cursor.fetchone()
                if result:
                    user = User(
                        id=result['id'],
                        username=result['username'],
                        email=result['email'],
                        role=result['role'],
                        full_name=result['full_name'],
                        created_at=result['created_at']
                    )
                    logger.info(f"Job seeker registered successfully: {username}")
                    return user
                    
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return None
    
    @staticmethod
    def login_user(username: str, password: str) -> Optional[User]:
        """Authenticate user login with separate admin/job seeker validation"""
        try:
            # Special handling for admin login
            if username.lower() == AuthService.ADMIN_USERNAME.lower():
                if AuthService.verify_password(password, AuthService.ADMIN_PASSWORD_HASH):
                    # Return admin user (create if doesn't exist in DB)
                    admin_user = AuthService._get_or_create_admin_user()
                    if admin_user:
                        logger.info("Admin logged in successfully")
                        return admin_user
                else:
                    logger.warning("Invalid admin login attempt")
                    return None
            
            # Job seeker login
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, username, email, password_hash, role, full_name, created_at
                    FROM users WHERE username = %s AND role = 'job_seeker'
                """, (username,))
                
                result = cursor.fetchone()
                if result and AuthService.verify_password(password, result['password_hash']):
                    user = User(
                        id=result['id'],
                        username=result['username'],
                        email=result['email'],
                        role=result['role'],
                        full_name=result['full_name'],
                        created_at=result['created_at']
                    )
                    logger.info(f"Job seeker logged in: {username}")
                    return user
                else:
                    logger.warning(f"Invalid job seeker login attempt: {username}")
                    return None
                    
        except Exception as e:
            logger.error(f"Login error: {e}")
            return None
    
    @staticmethod
    def _get_or_create_admin_user() -> Optional[User]:
        """Get admin user from database or create if doesn't exist"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, username, email, role, full_name, created_at
                    FROM users WHERE username = %s AND role = 'admin'
                """, (AuthService.ADMIN_USERNAME,))
                
                result = cursor.fetchone()
                if result:
                    return User(
                        id=result['id'],
                        username=result['username'],
                        email=result['email'],
                        role=result['role'],
                        full_name=result['full_name'],
                        created_at=result['created_at']
                    )
                else:
                    # Create admin user in database
                    if AuthService.initialize_admin():
                        return AuthService._get_or_create_admin_user()
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting/creating admin user: {e}")
            return None
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT password_hash FROM users WHERE id = %s
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                # Verify old password
                if not AuthService.verify_password(old_password, result['password_hash']):
                    return False
                
                # Update with new password
                new_hash = AuthService.hash_password(new_password)
                cursor.execute("""
                    UPDATE users SET password_hash = %s WHERE id = %s
                """, (new_hash, user_id))
                
                logger.info(f"Password changed for user ID: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return False
    
    @staticmethod
    def get_user_stats() -> dict:
        """Get user statistics"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE role = 'job_seeker') as job_seekers,
                        COUNT(*) FILTER (WHERE role = 'admin') as admins,
                        COUNT(*) as total_users
                    FROM users
                """)
                
                result = cursor.fetchone()
                return {
                    'job_seekers': result['job_seekers'],
                    'admins': result['admins'],
                    'total_users': result['total_users']
                }
                
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'job_seekers': 0, 'admins': 0, 'total_users': 0}