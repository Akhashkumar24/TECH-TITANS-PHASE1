# cli/job_seeker_cli.py
from typing import Optional
from models.user import User
from services.job_service import JobService
from services.application_service import ApplicationService
from cli.cli_utils import CLIUtils
from utils.logger import get_logger
from utils.file_handler import FileHandler
import os

logger = get_logger(__name__)

class JobSeekerCLI:
    def __init__(self, user: User):
        self.user = user
        self.job_service = JobService()
        self.application_service = ApplicationService()
        self.file_handler = FileHandler()
        self.utils = CLIUtils()
    
    def show_menu(self):
        """Display job seeker main menu"""
        while True:
            self.utils.clear_screen()
            self.utils.print_header(f"Job Seeker Dashboard - Welcome {self.user.full_name or self.user.username}")
            
            menu_choices = [
                "View Available Jobs",
                "Apply to Job",
                "View My Applications",
                "Test Resume Text Extraction",
                "Update Profile",
                "Logout"
            ]
            
            choice = self.utils.get_choice("Select an option:", menu_choices)
            
            if choice == "View Available Jobs":
                self.view_available_jobs()
            elif choice == "Apply to Job":
                self.apply_to_job()
            elif choice == "View My Applications":
                self.view_my_applications()
            elif choice == "Test Resume Text Extraction":
                self.test_resume_extraction()
            elif choice == "Update Profile":
                self.update_profile()
            elif choice == "Logout":
                self.utils.print_info("Logging out...")
                break
    
    def view_available_jobs(self):
        """Display all available jobs"""
        self.utils.clear_screen()
        self.utils.print_header("Available Job Openings")
        
        jobs = self.job_service.get_all_active_jobs()
        
        if not jobs:
            self.utils.print_warning("No jobs available at the moment.")
            self.utils.press_enter_to_continue()
            return
        
        # Prepare data for table display
        job_data = []
        for job in jobs:
            skills_str = ", ".join(job.skills_required[:3]) if job.skills_required else "Not specified"
            if len(job.skills_required) > 3:
                skills_str += "..."
            
            job_data.append([
                job.id,
                job.title[:30] + "..." if len(job.title) > 30 else job.title,
                job.company_name or "Not specified",
                job.location or "Remote",
                job.experience_level or "Any",
                skills_str
            ])
        
        headers = ["ID", "Title", "Company", "Location", "Experience", "Key Skills"]
        self.utils.print_table(job_data, headers, "📋 Available Positions")
        
        # Option to view detailed job description
        if self.utils.confirm("\nWould you like to view details of a specific job?"):
            try:
                job_id = int(input("Enter Job ID: "))
                self.view_job_details(job_id)
            except ValueError:
                self.utils.print_error("Invalid Job ID")
        
        self.utils.press_enter_to_continue()
    
    def view_job_details(self, job_id: int):
        """Display detailed job information"""
        job = self.job_service.get_job_by_id(job_id)
        
        if not job:
            self.utils.print_error("Job not found!")
            return
        
        self.utils.clear_screen()
        self.utils.print_header(f"Job Details - {job.title}")
        
        print(f"🏢 Company: {job.company_name or 'Company Name Not Specified'}")
        print(f"📅 Posted: {job.created_at.strftime('%Y-%m-%d') if job.created_at else 'Unknown'}")
        print(f"📍 Location: {job.location or 'Remote/Not specified'}")
        print(f"💰 Salary: {job.salary_range or 'Not disclosed'}")
        print(f"⭐ Experience Level: {job.experience_level or 'Any level'}")
        
        if job.skills_required:
            print(f"🛠️  Required Skills: {', '.join(job.skills_required)}")
        
        print(f"\n📄 Job Description:")
        print("-" * 50)
        print(job.description)
        
        if job.requirements:
            print(f"\n📋 Requirements:")
            print("-" * 50)
            print(job.requirements)
        
        # Check if user already applied
        if self.application_service.check_existing_application(self.user.id, job_id):
            self.utils.print_warning("You have already applied to this job!")
        else:
            if self.utils.confirm("\nWould you like to apply to this job?"):
                self.apply_to_specific_job(job_id)
    
    def apply_to_job(self):
        """Apply to a specific job"""
        self.utils.clear_screen()
        self.utils.print_header("Apply to Job")
        
        try:
            job_id = int(self.utils.get_input("Enter Job ID you want to apply to"))
            self.apply_to_specific_job(job_id)
        except ValueError:
            self.utils.print_error("Invalid Job ID")
            self.utils.press_enter_to_continue()
    
    def apply_to_specific_job(self, job_id: int):
        """Apply to a specific job with enhanced resume handling"""
        # Check if job exists
        job = self.job_service.get_job_by_id(job_id)
        if not job:
            self.utils.print_error("Job not found!")
            return
        
        # Check if already applied
        if self.application_service.check_existing_application(self.user.id, job_id):
            self.utils.print_error("You have already applied to this job!")
            return
        
        self.utils.print_info(f"Applying to: {job.title}")
        print(f"Company: {job.company_name or 'Not specified'}")
        
        # Get resume file path with validation
        resume_path = self.get_resume_file_path()
        if not resume_path:
            return
        
        # Preview extracted text
        if self.utils.confirm("Would you like to preview the extracted text from your resume?"):
            self.preview_resume_text(resume_path)
        
        # Get cover letter (optional)
        cover_letter = self.get_cover_letter()
        
        # Confirm application
        if not self.utils.confirm("Submit your application?"):
            self.utils.print_info("Application cancelled.")
            return
        
        # Submit application
        self.utils.print_info("Submitting application...")
        application = self.application_service.submit_application(
            user_id=self.user.id,
            job_id=job_id,
            resume_path=resume_path,
            cover_letter=cover_letter
        )
        
        if application:
            self.utils.print_success("Application submitted successfully!")
            self.utils.print_info(f"Application ID: {application.id}")
            self.utils.print_info("You will be notified when the employer reviews your application.")
        else:
            self.utils.print_error("Failed to submit application. Please try again.")
        
        self.utils.press_enter_to_continue()
    
    def get_resume_file_path(self) -> Optional[str]:
        """Get and validate resume file path"""
        while True:
            self.utils.print_info("Resume File Selection:")
            print("1. Enter full file path")
            print("2. Browse current directory")
            print("3. Cancel")
            
            choice = input("Select option (1-3): ").strip()
            
            if choice == "1":
                resume_path = self.utils.get_input("Enter full path to your resume file (PDF/DOCX/TXT)")
                
                if not os.path.exists(resume_path):
                    self.utils.print_error("File not found! Please check the path.")
                    continue
                
                if not self.file_handler.validate_file(resume_path):
                    self.utils.print_error("Invalid file! Please ensure it's a PDF, DOCX, or TXT file under 10MB.")
                    continue
                
                # Show file info
                file_info = self.file_handler.get_file_info(resume_path)
                self.utils.print_success(f"File validated: {file_info['name']} ({file_info['size_mb']}MB)")
                return resume_path
                
            elif choice == "2":
                resume_path = self.browse_files()
                if resume_path:
                    return resume_path
                    
            elif choice == "3":
                self.utils.print_info("Resume selection cancelled.")
                return None
                
            else:
                self.utils.print_error("Invalid choice!")
    
    def browse_files(self) -> Optional[str]:
        """Simple file browser for current directory"""
        current_dir = os.getcwd()
        self.utils.print_info(f"Current directory: {current_dir}")
        
        # List files in current directory
        try:
            files = []
            for item in os.listdir(current_dir):
                if os.path.isfile(item):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ['.pdf', '.docx', '.txt', '.doc']:
                        files.append(item)
            
            if not files:
                self.utils.print_warning("No resume files found in current directory.")
                return None
            
            files.append("Go back")
            selected = self.utils.get_choice("Select a resume file:", files)
            
            if selected == "Go back":
                return None
            
            full_path = os.path.join(current_dir, selected)
            if self.file_handler.validate_file(full_path):
                return full_path
            else:
                self.utils.print_error("Selected file is not valid.")
                return None
                
        except Exception as e:
            self.utils.print_error(f"Error browsing files: {e}")
            return None
    
    def preview_resume_text(self, resume_path: str):
        """Preview extracted text from resume"""
        self.utils.print_info("Extracting text from resume...")
        
        extracted_text = self.file_handler.extract_text_from_file(resume_path)
        
        if extracted_text:
            self.utils.print_success(f"Successfully extracted {len(extracted_text)} characters")
            
            # Show preview (first 500 characters)
            preview = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")
            
            print("\n" + "="*50)
            print("RESUME TEXT PREVIEW:")
            print("="*50)
            print(preview)
            print("="*50)
            
            if self.utils.confirm("Does the extracted text look correct?"):
                return True
            else:
                self.utils.print_warning("Text extraction may not be perfect. The system will still process your application.")
                return True
        else:
            self.utils.print_error("Failed to extract text from resume.")
            self.utils.print_info("The system will still accept your application, but AI matching may be limited.")
            return self.utils.confirm("Continue anyway?")
    
    def get_cover_letter(self) -> Optional[str]:
        """Get cover letter from user"""
        if not self.utils.confirm("Would you like to include a cover letter?"):
            return None
        
        self.utils.print_info("Enter your cover letter (press Enter twice when finished):")
        
        lines = []
        empty_lines = 0
        
        while empty_lines < 2:
            line = input()
            if line.strip():
                lines.append(line)
                empty_lines = 0
            else:
                empty_lines += 1
                if lines:  # Don't add empty lines at the beginning
                    lines.append("")
        
        cover_letter = '\n'.join(lines).strip()
        
        if cover_letter:
            self.utils.print_success(f"Cover letter added ({len(cover_letter)} characters)")
            return cover_letter
        else:
            return None
    
    def test_resume_extraction(self):
        """Test resume text extraction functionality"""
        self.utils.clear_screen()
        self.utils.print_header("Test Resume Text Extraction")
        
        resume_path = self.get_resume_file_path()
        if not resume_path:
            return
        
        self.utils.print_info("Testing text extraction...")
        
        # Get file info
        file_info = self.file_handler.get_file_info(resume_path)
        print(f"\nFile Information:")
        print(f"- Name: {file_info.get('name', 'Unknown')}")
        print(f"- Size: {file_info.get('size_mb', 'Unknown')} MB")
        print(f"- Extension: {file_info.get('extension', 'Unknown')}")
        if 'pages' in file_info:
            print(f"- Pages: {file_info['pages']}")
        
        # Extract text
        extracted_text = self.file_handler.extract_text_from_file(resume_path)
        
        if extracted_text:
            self.utils.print_success(f"Text extraction successful!")
            print(f"Extracted {len(extracted_text)} characters")
            
            # Show full text with pagination
            if self.utils.confirm("Would you like to view the full extracted text?"):
                self.show_paginated_text(extracted_text)
        else:
            self.utils.print_error("Text extraction failed!")
            self.utils.print_info("This could be due to:")
            print("- Encrypted or password-protected PDF")
            print("- Scanned image-based PDF (OCR required)")
            print("- Corrupted file")
            print("- Unsupported file format")
        
        self.utils.press_enter_to_continue()
    
    def show_paginated_text(self, text: str, lines_per_page: int = 20):
        """Show text with pagination"""
        lines = text.split('\n')
        total_pages = (len(lines) + lines_per_page - 1) // lines_per_page
        current_page = 1
        
        while current_page <= total_pages:
            self.utils.clear_screen()
            self.utils.print_header(f"Extracted Text - Page {current_page}/{total_pages}")
            
            start_idx = (current_page - 1) * lines_per_page
            end_idx = min(start_idx + lines_per_page, len(lines))
            
            for line in lines[start_idx:end_idx]:
                print(line)
            
            print(f"\n--- Page {current_page} of {total_pages} ---")
            
            if current_page < total_pages:
                choice = input("Press Enter for next page, 'q' to quit: ").strip().lower()
                if choice == 'q':
                    break
                current_page += 1
            else:
                input("Press Enter to continue...")
                break
    
    def view_my_applications(self):
        """View user's job applications"""
        self.utils.clear_screen()
        self.utils.print_header("My Job Applications")
        
        applications = self.application_service.get_applications_by_user(self.user.id)
        
        if not applications:
            self.utils.print_warning("You haven't applied to any jobs yet.")
            self.utils.press_enter_to_continue()
            return
        
        # Prepare data for table
        app_data = []
        for app in applications:
            app_data.append([
                app['job_id'],
                app['job_title'][:30] + "..." if len(app['job_title']) > 30 else app['job_title'],
                app['company_name'] or "Not specified",
                app['location'] or "Remote",
                app['status'].title(),
                app['applied_at'].strftime('%Y-%m-%d') if app['applied_at'] else 'Unknown'
            ])
        
        headers = ["Job ID", "Position", "Company", "Location", "Status", "Applied Date"]
        self.utils.print_table(app_data, headers, "📝 Your Applications")
        
        self.utils.press_enter_to_continue()
    
    def update_profile(self):
        """Update user profile information"""
        self.utils.clear_screen()
        self.utils.print_header("Update Profile")
        
        self.utils.print_info("Current Profile Information:")
        print(f"Username: {self.user.username}")
        print(f"Email: {self.user.email}")
        print(f"Full Name: {self.user.full_name or 'Not set'}")
        print(f"Phone: {self.user.phone or 'Not set'}")
        
        # For now, just show current info
        # Profile update functionality can be extended
        self.utils.print_warning("Profile update feature will be available in the next version.")
        self.utils.press_enter_to_continue()