# main.py
#!/usr/bin/env python3
"""
Enhanced Job Matching System with Multi-Agent Architecture
- Comparison Agent: Compare JD with consultant profiles
- Ranking Agent: Rank profiles based on similarity scores  
- Communication Agent: Send automated emails to recruiters
- A2A Protocol: Agent-to-Agent communication standard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.migrations import DatabaseMigrator
from services.auth_service import AuthService
from cli.job_seeker_cli import JobSeekerCLI
from cli.admin_cli import AdminCLI
from cli.cli_utils import CLIUtils
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class JobMatchingSystem:
    def __init__(self):
        self.utils = CLIUtils()
        self.auth_service = AuthService()
        
    def run(self):
        """Main entry point for the system"""
        try:
            # Initialize system
            self.initialize_system()
            
            # Show welcome and main menu
            self.show_welcome()
            self.main_menu()
            
        except KeyboardInterrupt:
            self.utils.print_info("\nGoodbye! Thank you for using Job Matching System.")
        except Exception as e:
            self.utils.print_error(f"System error: {e}")
            logger.error(f"System error: {e}")
    
    def initialize_system(self):
        """Initialize database and system components"""
        self.utils.print_info("Initializing Job Matching System...")
        
        try:
            # Run database migrations
            migrator = DatabaseMigrator()
            migrator.run_migrations()
            
            # Initialize admin user
            if not self.auth_service.initialize_admin():
                self.utils.print_warning("Failed to initialize admin user")
            
            self.utils.print_success("System initialized successfully!")
            
        except Exception as e:
            self.utils.print_error(f"System initialization failed: {e}")
            sys.exit(1)
    
    def show_welcome(self):
        """Display welcome message"""
        self.utils.clear_screen()
        self.utils.print_header("🚀 AI-Powered Job Matching System")
        
        print("Welcome to the advanced job matching platform featuring:")
        print("• 🤖 Multi-Agent AI System (A2A Protocol)")
        print("• 📊 Intelligent Resume-Job Matching")
        print("• 🏆 Automated Candidate Ranking")
        print("• 📧 Smart Email Notifications")
        print("• 🔐 Secure Authentication System")
        print()
        
        # Show system status
        stats = self.auth_service.get_user_stats()
        print(f"📈 System Stats: {stats['job_seekers']} Job Seekers | {stats['admins']} Admin")
        print()
    
    def main_menu(self):
        """Display main menu and handle user selection"""
        while True:
            try:
                self.utils.print_header("Main Menu")
                
                menu_choices = [
                    "🔑 Login",
                    "📝 Register as Job Seeker", 
                    "ℹ️  System Information",
                    "🚪 Exit"
                ]
                
                choice = self.utils.get_choice("Please select an option:", menu_choices)
                
                if "Login" in choice:
                    self.handle_login()
                elif "Register" in choice:
                    self.handle_registration()
                elif "System Information" in choice:
                    self.show_system_info()
                elif "Exit" in choice:
                    self.utils.print_info("Thank you for using Job Matching System!")
                    break
                    
            except KeyboardInterrupt:
                self.utils.print_info("\nGoodbye!")
                break
            except Exception as e:
                self.utils.print_error(f"An error occurred: {e}")
                self.utils.press_enter_to_continue()
    
    def handle_login(self):
        """Handle user login with role-based redirection"""
        self.utils.clear_screen()
        self.utils.print_header("🔑 User Login")
        
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            try:
                username = self.utils.get_input("Username")
                password = self.utils.get_input("Password")
                
                # Authenticate user
                user = self.auth_service.login_user(username, password)
                
                if user:
                    self.utils.print_success(f"Welcome back, {user.full_name or user.username}!")
                    
                    # Route to appropriate interface based on role
                    if user.role == 'admin':
                        self.utils.print_info("Redirecting to Admin Dashboard...")
                        admin_cli = AdminCLI(user)
                        admin_cli.show_menu()
                    elif user.role == 'job_seeker':
                        self.utils.print_info("Redirecting to Job Seeker Dashboard...")
                        job_seeker_cli = JobSeekerCLI(user)
                        job_seeker_cli.show_menu()
                    else:
                        self.utils.print_error(f"Unknown user role: {user.role}")
                    
                    break
                else:
                    attempts += 1
                    remaining = max_attempts - attempts
                    
                    if remaining > 0:
                        self.utils.print_error(f"Invalid credentials! {remaining} attempts remaining.")
                    else:
                        self.utils.print_error("Maximum login attempts exceeded!")
                        self.utils.press_enter_to_continue()
                        break
                        
            except KeyboardInterrupt:
                self.utils.print_info("Login cancelled.")
                break
    
    def handle_registration(self):
        """Handle new user registration (job seekers only)"""
        self.utils.clear_screen()
        self.utils.print_header("📝 Register as Job Seeker")
        
        self.utils.print_info("Create your job seeker account:")
        print("• Only job seekers can register through this interface")
        print("• Admin accounts are pre-configured for security")
        print("• All fields marked with * are required")
        print()
        
        try:
            # Collect user information
            username = self.utils.get_input("Username *")
            email = self.utils.get_input("Email Address *")
            
            # Password with confirmation
            while True:
                password = self.utils.get_input("Password *")
                confirm_password = self.utils.get_input("Confirm Password *")
                
                if password == confirm_password:
                    break
                else:
                    self.utils.print_error("Passwords do not match! Please try again.")
            
            # Optional information
            full_name = self.utils.get_input("Full Name (optional)", required=False)
            
            # Validate inputs
            if not self._validate_registration_data(username, email, password):
                return
            
            # Attempt registration
            user = self.auth_service.register_user(username, email, password, full_name)
            
            if user:
                self.utils.print_success("Registration successful!")
                self.utils.print_info(f"Welcome {user.full_name or user.username}!")
                self.utils.print_info("You can now login with your credentials.")
                
                # Option to login immediately
                if self.utils.confirm("Would you like to login now?"):
                    job_seeker_cli = JobSeekerCLI(user)
                    job_seeker_cli.show_menu()
            else:
                self.utils.print_error("Registration failed!")
                self.utils.print_info("Possible reasons:")
                print("• Username or email already exists")
                print("• Invalid email format")
                print("• System error")
                
        except KeyboardInterrupt:
            self.utils.print_info("Registration cancelled.")
        except Exception as e:
            self.utils.print_error(f"Registration error: {e}")
        
        self.utils.press_enter_to_continue()
    
    def _validate_registration_data(self, username: str, email: str, password: str) -> bool:
        """Validate registration data"""
        errors = []
        
        # Username validation
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        
        if username.lower() == 'admin':
            errors.append("Username 'admin' is reserved")
        
        # Email validation (basic)
        if '@' not in email or '.' not in email:
            errors.append("Invalid email format")
        
        if email.lower() == 'admin@jobmatch.com':
            errors.append("Admin email cannot be used for registration")
        
        # Password validation
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        if errors:
            self.utils.print_error("Registration validation failed:")
            for error in errors:
                print(f"• {error}")
            self.utils.press_enter_to_continue()
            return False
        
        return True
    
    def show_system_info(self):
        """Display system information"""
        self.utils.clear_screen() 
        self.utils.print_header("🔧 System Information")
        
        print("📋 System Configuration:")
        print(f"• Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        print(f"• AI Engine: {'Gemini API' if settings.GEMINI_API_KEY else 'Fallback Mode'}")
        print(f"• Email Service: {'Enabled' if settings.SMTP_EMAIL else 'Disabled'}")
        print(f"• Max Resume Size: {settings.MAX_RESUME_SIZE_MB}MB")
        print(f"• Supported Files: {', '.join(settings.SUPPORTED_FILE_TYPES)}")
        print()
        
        print("🤖 Multi-Agent System:")
        print("• Comparison Agent: Analyzes resume-job compatibility")
        print("• Ranking Agent: Ranks candidates by match scores")
        print("• Communication Agent: Sends automated notifications")
        print("• A2A Protocol: Ensures reliable agent communication")
        print()
        
        print("🔐 Security Features:")
        print("• Role-based access control")
        print("• Secure password hashing")
        print("• Single admin account policy")
        print("• Session management")
        print()
        
        # Show user statistics
        stats = self.auth_service.get_user_stats()
        print("📊 Current Statistics:")
        print(f"• Total Users: {stats['total_users']}")
        print(f"• Job Seekers: {stats['job_seekers']}")
        print(f"• Administrators: {stats['admins']}")
        print()
        
        print("🚀 Getting Started:")
        print("1. Register as a job seeker to browse and apply for jobs")
        print("2. Login as admin (username: admin, password: admin123) to manage jobs")
        print("3. Use the AI ranking system to find the best candidates")
        print("4. Receive email notifications about top matches")
        print()
        
        self.utils.press_enter_to_continue()

def main():
    """Main entry point"""
    try:
        # Validate settings before starting
        if not settings.validate_settings():
            print("❌ Critical configuration missing. Please check your environment variables.")
            print("\nRequired variables:")
            print("• DB_PASSWORD: Database password")
            print("• GEMINI_API_KEY: Google Gemini API key for AI features")
            print("\nOptional variables:")
            print("• SMTP_EMAIL: Email for notifications")
            print("• SMTP_PASSWORD: Email password")
            
            if input("\nContinue anyway? (y/N): ").lower() != 'y':
                sys.exit(1)
        
        # Start the system
        system = JobMatchingSystem()
        system.run()
        
    except Exception as e:
        print(f"❌ Failed to start system: {e}")
        logger.error(f"System startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()