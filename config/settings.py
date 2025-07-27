# config/settings.py
import os

# Try to load dotenv, but continue without it if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not installed. Using system environment variables only.")

class Settings:
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'job_matching_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # Gemini API settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Email/SMTP settings for Communication Agent
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # Application settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_RESUME_SIZE_MB = int(os.getenv('MAX_RESUME_SIZE_MB', '10'))
    SUPPORTED_FILE_TYPES = os.getenv('SUPPORTED_FILE_TYPES', 'pdf,docx,txt,doc').split(',')
    
    # Agent settings
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.6'))
    MAX_RANKING_RESULTS = int(os.getenv('MAX_RANKING_RESULTS', '50'))
    
    # A2A Protocol settings
    A2A_MESSAGE_TIMEOUT = int(os.getenv('A2A_MESSAGE_TIMEOUT', '30'))  # seconds
    A2A_MAX_RETRIES = int(os.getenv('A2A_MAX_RETRIES', '3'))
    A2A_ENABLE_LOGGING = os.getenv('A2A_ENABLE_LOGGING', 'true').lower() == 'true'
    
    # Security settings
    ADMIN_ONLY_MODE = os.getenv('ADMIN_ONLY_MODE', 'false').lower() == 'true'
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    
    @classmethod
    def validate_settings(cls):
        """Validate critical settings"""
        missing_settings = []
        warnings = []
        
        # Critical settings
        if not cls.GEMINI_API_KEY:
            missing_settings.append("GEMINI_API_KEY")
        
        if not cls.DB_PASSWORD and cls.DB_USER != 'postgres':
            missing_settings.append("DB_PASSWORD")
        
        # Email settings (optional but recommended)
        if not cls.SMTP_EMAIL:
            warnings.append("SMTP_EMAIL - Email notifications will be disabled")
        
        if not cls.SMTP_PASSWORD and cls.SMTP_EMAIL:
            warnings.append("SMTP_PASSWORD - Email authentication may fail")
        
        # Print results
        if missing_settings:
            print(f"ERROR: Missing critical environment variables: {', '.join(missing_settings)}")
            if not DOTENV_AVAILABLE:
                print("Consider installing python-dotenv and creating a .env file")
            return False
        
        if warnings:
            print(f"WARNING: Missing optional settings: {', '.join(warnings)}")
        
        print("✅ Settings validation completed")
        return True
    
    @classmethod
    def get_email_config(cls):
        """Get email configuration for Communication Agent"""
        return {
            'smtp_server': cls.SMTP_SERVER,
            'smtp_port': cls.SMTP_PORT,
            'email': cls.SMTP_EMAIL,
            'password': cls.SMTP_PASSWORD,
            'use_tls': cls.SMTP_USE_TLS,
            'enabled': bool(cls.SMTP_EMAIL and cls.SMTP_PASSWORD)
        }
    
    @classmethod
    def get_a2a_config(cls):
        """Get A2A protocol configuration"""
        return {
            'message_timeout': cls.A2A_MESSAGE_TIMEOUT,
            'max_retries': cls.A2A_MAX_RETRIES,
            'enable_logging': cls.A2A_ENABLE_LOGGING
        }

settings = Settings()

# Validate settings on import
settings.validate_settings()