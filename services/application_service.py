# services/application_service.py
from typing import List, Optional, Dict, Any
from models.application import Application
from config.database import db_connection
from utils.logger import get_logger
from utils.file_handler import FileHandler
import os
import json

logger = get_logger(__name__)

class ApplicationService:
    def __init__(self):
        self.file_handler = FileHandler()
    
    def submit_application(self, user_id: int, job_id: int, resume_path: str, 
                          resume_text: str = None, cover_letter: str = None) -> Optional[Application]:
        """Submit a job application with enhanced text extraction"""
        try:
            # Validate and save resume file
            if not self.file_handler.validate_file(resume_path):
                logger.error("Invalid resume file")
                return None
            
            # Extract text from resume file if not provided
            if not resume_text or resume_text.strip() == "":
                logger.info("Extracting text from resume file...")
                extracted_text = self.file_handler.extract_text_from_file(resume_path)
                
                if extracted_text:
                    resume_text = extracted_text
                    logger.info(f"Successfully extracted {len(resume_text)} characters from resume")
                else:
                    logger.warning("Failed to extract text from resume, using empty text")
                    resume_text = "Text extraction failed. Please review manually."
            
            # Save the resume file
            saved_path = self.file_handler.save_resume(resume_path, user_id, job_id)
            if not saved_path:
                logger.error("Failed to save resume file")
                return None
            
            # Store in database
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO applications (user_id, job_id, resume_path, resume_text, cover_letter)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, applied_at
                """, (user_id, job_id, saved_path, resume_text, cover_letter))
                
                result = cursor.fetchone()
                if result:
                    application = Application(
                        id=result['id'],
                        user_id=user_id,
                        job_id=job_id,
                        resume_path=saved_path,
                        resume_text=resume_text,
                        cover_letter=cover_letter,
                        applied_at=result['applied_at']
                    )
                    logger.info(f"Application submitted successfully: User {user_id} -> Job {job_id}")
                    return application
                    
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return None
    
    def get_applications_by_job(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all applications for a specific job"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT a.id, a.user_id, a.job_id, a.resume_path, a.resume_text, 
                           a.status, a.applied_at,
                           u.full_name, u.email, u.phone,
                           j.title as job_title
                    FROM applications a
                    JOIN users u ON a.user_id = u.id
                    JOIN jobs j ON a.job_id = j.id
                    WHERE a.job_id = %s
                    ORDER BY a.applied_at DESC
                """, (job_id,))
                
                applications = []
                for row in cursor.fetchall():
                    # Ensure we have resume text for AI processing
                    resume_text = row['resume_text']
                    
                    # If no resume text and we have a file path, try to extract
                    if (not resume_text or len(resume_text.strip()) < 10) and row['resume_path']:
                        logger.info(f"Extracting text for application {row['id']} from {row['resume_path']}")
                        
                        try:
                            extracted_text = self.file_handler.extract_text_from_file(row['resume_path'])
                            if extracted_text and len(extracted_text.strip()) > 10:
                                resume_text = extracted_text
                                # Update database with extracted text
                                self._update_resume_text(row['id'], resume_text)
                                logger.info(f"Successfully extracted and updated resume text for application {row['id']}")
                            else:
                                logger.warning(f"Text extraction failed or returned insufficient content for {row['resume_path']}")
                                resume_text = f"Resume file: {row['resume_path']} - Text extraction failed"
                        except Exception as e:
                            logger.error(f"Error extracting text from {row['resume_path']}: {e}")
                            resume_text = f"Resume file: {row['resume_path']} - Extraction error: {str(e)}"
                    
                    applications.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'job_id': row['job_id'],
                        'applicant_name': row['full_name'],
                        'email': row['email'],
                        'phone': row['phone'],
                        'job_title': row['job_title'],
                        'resume_path': row['resume_path'],
                        'resume_text': resume_text or "No resume text available",
                        'status': row['status'],
                        'applied_at': row['applied_at']
                    })
                
                logger.info(f"Retrieved {len(applications)} applications for job {job_id}")
                return applications
                
        except Exception as e:
            logger.error(f"Error fetching applications for job {job_id}: {e}")
            return []
    
    def _update_resume_text(self, application_id: int, resume_text: str):
        """Update resume text in database"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE applications 
                    SET resume_text = %s 
                    WHERE id = %s
                """, (resume_text, application_id))
                logger.info(f"Updated resume text for application {application_id}")
        except Exception as e:
            logger.error(f"Error updating resume text: {e}")
    
    def get_applications_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all applications by a user"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT a.id, a.user_id, a.job_id, a.status, a.applied_at,
                           j.title, j.company_name, j.location
                    FROM applications a
                    JOIN jobs j ON a.job_id = j.id
                    WHERE a.user_id = %s
                    ORDER BY a.applied_at DESC
                """, (user_id,))
                
                applications = []
                for row in cursor.fetchall():
                    applications.append({
                        'id': row['id'],
                        'job_id': row['job_id'],
                        'job_title': row['title'],
                        'company_name': row['company_name'],
                        'location': row['location'],
                        'status': row['status'],
                        'applied_at': row['applied_at']
                    })
                
                return applications
                
        except Exception as e:
            logger.error(f"Error fetching user applications: {e}")
            return []
    
    def check_existing_application(self, user_id: int, job_id: int) -> bool:
        """Check if user has already applied to this job"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count FROM applications 
                    WHERE user_id = %s AND job_id = %s
                """, (user_id, job_id))
                
                result = cursor.fetchone()
                return result['count'] > 0
                
        except Exception as e:
            logger.error(f"Error checking existing application: {e}")
            return True  # Assume exists to prevent duplicates
    
    def get_job_rankings(self, job_id: int) -> List[Dict[str, Any]]:
        """Get rankings for a specific job with enhanced data retrieval"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT r.id, r.similarity_score, r.rank_position, r.ranking_details,
                           u.full_name as applicant_name, u.email, a.applied_at, a.id as application_id
                    FROM rankings r
                    JOIN applications a ON r.application_id = a.id
                    JOIN users u ON a.user_id = u.id
                    WHERE r.job_id = %s
                    ORDER BY r.rank_position ASC
                """, (job_id,))
                
                rankings = []
                for row in cursor.fetchall():
                    # Parse ranking_details if it's a JSON string
                    ranking_details = row['ranking_details']
                    if isinstance(ranking_details, str):
                        try:
                            ranking_details = json.loads(ranking_details)
                        except json.JSONDecodeError:
                            ranking_details = {'raw_data': ranking_details}
                    elif ranking_details is None:
                        ranking_details = {}
                    
                    rankings.append({
                        'rank': row['rank_position'],
                        'applicant_name': row['applicant_name'],
                        'email': row['email'],
                        'similarity_score': float(row['similarity_score']) if row['similarity_score'] else 0.0,
                        'applied_at': row['applied_at'],
                        'ranking_details': ranking_details,
                        'application_id': row['application_id']
                    })
                
                logger.info(f"Retrieved {len(rankings)} rankings for job {job_id}")
                return rankings
                
        except Exception as e:
            logger.error(f"Error fetching job rankings: {e}")
            return []
    
    def get_application_details(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific application"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT a.id, a.user_id, a.job_id, a.resume_path, a.resume_text,
                           a.cover_letter, a.status, a.applied_at,
                           u.full_name, u.email, u.phone,
                           j.title as job_title, j.company_name
                    FROM applications a
                    JOIN users u ON a.user_id = u.id
                    JOIN jobs j ON a.job_id = j.id
                    WHERE a.id = %s
                """, (application_id,))
                
                row = cursor.fetchone()
                if row:
                    # Ensure we have resume text
                    resume_text = row['resume_text']
                    if not resume_text and row['resume_path']:
                        resume_text = self.file_handler.extract_text_from_file(row['resume_path'])
                        if resume_text:
                            self._update_resume_text(application_id, resume_text)
                    
                    return {
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'job_id': row['job_id'],
                        'applicant_name': row['full_name'],
                        'email': row['email'],
                        'phone': row['phone'],
                        'job_title': row['job_title'],
                        'company_name': row['company_name'],
                        'resume_path': row['resume_path'],
                        'resume_text': resume_text or "Text extraction failed",
                        'cover_letter': row['cover_letter'],
                        'status': row['status'],
                        'applied_at': row['applied_at']
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching application details: {e}")
            return None
    
    def get_ranking_by_job_and_user(self, job_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get ranking for a specific job and user combination"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT r.id, r.similarity_score, r.rank_position, r.ranking_details,
                           u.full_name as applicant_name, u.email, a.applied_at
                    FROM rankings r
                    JOIN applications a ON r.application_id = a.id
                    JOIN users u ON a.user_id = u.id
                    WHERE r.job_id = %s AND a.user_id = %s
                """, (job_id, user_id))
                
                row = cursor.fetchone()
                if row:
                    ranking_details = row['ranking_details']
                    if isinstance(ranking_details, str):
                        try:
                            ranking_details = json.loads(ranking_details)
                        except json.JSONDecodeError:
                            ranking_details = {'raw_data': ranking_details}
                    
                    return {
                        'rank': row['rank_position'],
                        'applicant_name': row['applicant_name'],
                        'email': row['email'],
                        'similarity_score': float(row['similarity_score']) if row['similarity_score'] else 0.0,
                        'applied_at': row['applied_at'],
                        'ranking_details': ranking_details or {}
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error fetching ranking for job {job_id} and user {user_id}: {e}")
            return None
    
    def update_application_status(self, application_id: int, status: str) -> bool:
        """Update application status"""
        try:
            valid_statuses = ['submitted', 'reviewed', 'shortlisted', 'rejected', 'hired']
            if status not in valid_statuses:
                logger.error(f"Invalid status: {status}")
                return False
            
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE applications 
                    SET status = %s 
                    WHERE id = %s
                """, (status, application_id))
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated application {application_id} status to {status}")
                    return True
                else:
                    logger.warning(f"No application found with ID {application_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            return False
    
    def get_application_statistics(self, job_id: int = None) -> Dict[str, Any]:
        """Get application statistics"""
        try:
            with db_connection.get_cursor() as cursor:
                if job_id:
                    # Statistics for specific job
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_applications,
                            COUNT(*) FILTER (WHERE status = 'submitted') as submitted,
                            COUNT(*) FILTER (WHERE status = 'reviewed') as reviewed,
                            COUNT(*) FILTER (WHERE status = 'shortlisted') as shortlisted,
                            COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
                            COUNT(*) FILTER (WHERE status = 'hired') as hired
                        FROM applications 
                        WHERE job_id = %s
                    """, (job_id,))
                else:
                    # Global statistics
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_applications,
                            COUNT(*) FILTER (WHERE status = 'submitted') as submitted,
                            COUNT(*) FILTER (WHERE status = 'reviewed') as reviewed,
                            COUNT(*) FILTER (WHERE status = 'shortlisted') as shortlisted,
                            COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
                            COUNT(*) FILTER (WHERE status = 'hired') as hired
                        FROM applications
                    """)
                
                result = cursor.fetchone()
                if result:
                    return {
                        'total_applications': result['total_applications'],
                        'submitted': result['submitted'],
                        'reviewed': result['reviewed'],
                        'shortlisted': result['shortlisted'],
                        'rejected': result['rejected'],
                        'hired': result['hired']
                    }
                else:
                    return {
                        'total_applications': 0,
                        'submitted': 0,
                        'reviewed': 0,
                        'shortlisted': 0,
                        'rejected': 0,
                        'hired': 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting application statistics: {e}")
            return {
                'total_applications': 0,
                'submitted': 0,
                'reviewed': 0,
                'shortlisted': 0,
                'rejected': 0,
                'hired': 0,
                'error': str(e)
            }