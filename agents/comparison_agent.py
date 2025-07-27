# agents/comparison_agent.py
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.agent_protocol import AgentMessage, MessageType
from services.gemini_service import GeminiService
from config.database import db_connection
from utils.logger import get_logger
from utils.file_handler import FileHandler
import json
import time

class ComparisonAgent(BaseAgent):
    def __init__(self, protocol):
        super().__init__("comparison_agent", protocol)
        self.gemini_service = GeminiService()
        self.file_handler = FileHandler()
        
        # Send periodic heartbeats to maintain A2A connection
        self._start_heartbeat()
        
    def _start_heartbeat(self):
        """Start heartbeat to maintain agent status"""
        import threading
        def heartbeat_loop():
            while True:
                try:
                    self.protocol.send_heartbeat(self.name)
                    time.sleep(30)  # Heartbeat every 30 seconds
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {e}")
                    time.sleep(30)
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
    def receive_message(self, message: AgentMessage):
        """Process incoming messages following A2A protocol"""
        try:
            self.logger.info(f"Received message from {message.sender}: {message.message_type.value}")
            
            if message.message_type == MessageType.REQUEST:
                if message.payload.get('action') == 'compare_applications':
                    result = self.compare_job_applications(message.payload)
                    
                    # Send response back to sender
                    self.send_message(
                        message.sender,
                        MessageType.RESPONSE,
                        result,
                        message.message_id
                    )
                    
                    # If comparison was successful, automatically trigger ranking
                    if result['status'] == 'success' and result.get('comparison_results'):
                        self.logger.info("Triggering ranking agent with comparison results")
                        
                        # Send message to ranking agent with immediate processing
                        ranking_message = AgentMessage(
                            sender=self.name,
                            receiver='ranking_agent',
                            message_type=MessageType.REQUEST,
                            payload={
                                'action': 'rank_applications',
                                'job_id': message.payload.get('job_id'),
                                'comparison_results': result['comparison_results']
                            },
                            correlation_id=message.message_id
                        )
                        
                        # Send synchronously to ensure ranking happens
                        ranking_success = self.protocol.send_message(ranking_message)
                        if ranking_success:
                            self.logger.info("Successfully triggered ranking agent")
                        else:
                            self.logger.error("Failed to trigger ranking agent")
                        
                else:
                    # Unknown action
                    error_result = {'status': 'error', 'message': f'Unknown action: {message.payload.get("action")}'}
                    self.send_message(
                        message.sender,
                        MessageType.ERROR,
                        error_result,
                        message.message_id
                    )
                    
            elif message.message_type == MessageType.NOTIFICATION:
                # Handle notifications from other agents
                self.handle_notification(message.payload)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            # Send error response
            self.send_message(
                message.sender,
                MessageType.ERROR,
                {'status': 'error', 'message': str(e)},
                message.message_id
            )
    
    def handle_notification(self, payload: Dict[str, Any]):
        """Handle notifications from other agents"""
        notification_type = payload.get('event_type')
        
        if notification_type == 'agent_registered':
            agent_name = payload.get('agent_name')
            self.logger.info(f"New agent registered: {agent_name}")
        elif notification_type == 'agent_unregistered':
            agent_name = payload.get('agent_name')
            self.logger.info(f"Agent unregistered: {agent_name}")
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process comparison task"""
        return self.compare_job_applications(task_data)
    
    def compare_job_applications(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare all applications for a specific job with enhanced error handling"""
        job_id = task_data.get('job_id')
        
        if not job_id:
            return {'status': 'error', 'message': 'Job ID required'}
        
        try:
            # Get job details and applications
            job_details = self._get_job_details(job_id)
            if not job_details:
                return {'status': 'error', 'message': f'Job {job_id} not found'}
                
            applications = self._get_job_applications(job_id)
            
            if not applications:
                return {'status': 'error', 'message': 'No applications found for this job'}
            
            self.logger.info(f"Processing {len(applications)} applications for job {job_id}")
            comparison_results = []
            
            # Process each application
            for i, app in enumerate(applications, 1):
                self.logger.info(f"Processing application {i}/{len(applications)}: {app['id']} for user {app['user_id']}")
                
                try:
                    # Get or extract resume text
                    resume_text = self._get_resume_text(app)
                    
                    if not resume_text or len(resume_text.strip()) < 10:
                        self.logger.warning(f"No valid resume text for application {app['id']}")
                        # Create a minimal comparison result
                        comparison = self._create_minimal_comparison_result()
                    else:
                        # Compare resume with job description
                        self.logger.info(f"Analyzing resume text ({len(resume_text)} chars) against job description")
                        comparison = self.gemini_service.compare_resume_job(
                            resume_text,
                            job_details['description'] or 'No job description available'
                        )
                    
                    # Ensure comparison has required fields
                    comparison = self._validate_comparison_result(comparison)
                    
                    comparison_results.append({
                        'application_id': app['id'],
                        'user_id': app['user_id'],
                        'applicant_name': app['full_name'],
                        'similarity_score': comparison['similarity_score'],
                        'comparison_details': comparison
                    })
                    
                    # Log the comparison
                    self.log_activity('resume_comparison', {
                        'job_id': job_id,
                        'application_id': app['id'],
                        'similarity_score': comparison['similarity_score']
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error processing application {app['id']}: {e}")
                    # Add failed application with minimal data
                    comparison_results.append({
                        'application_id': app['id'],
                        'user_id': app['user_id'],
                        'applicant_name': app['full_name'],
                        'similarity_score': 0.0,
                        'comparison_details': self._create_error_comparison_result(str(e))
                    })
            
            self.logger.info(f"Completed comparison for {len(comparison_results)} applications")
            
            return {
                'status': 'success',
                'job_id': job_id,
                'total_applications': len(applications),
                'successful_comparisons': len([r for r in comparison_results if r['similarity_score'] > 0]),
                'comparison_results': comparison_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in comparison process: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _create_minimal_comparison_result(self) -> Dict[str, Any]:
        """Create minimal comparison result when text extraction fails"""
        return {
            'similarity_score': 0.0,
            'skills_match': {
                'matched_skills': [],
                'missing_skills': [],
                'additional_skills': []
            },
            'experience_match': {
                'level_match': False,
                'years_required': 'Unknown',
                'years_candidate': 'Unknown',
                'relevance_score': 0.0
            },
            'education_match': {
                'meets_requirements': False,
                'education_score': 0.0
            },
            'overall_assessment': {
                'strengths': ['Resume submitted'],
                'weaknesses': ['Text extraction failed'],
                'recommendation': 'not_recommended'
            },
            'detailed_feedback': 'Unable to analyze resume - text extraction failed'
        }
    
    def _create_error_comparison_result(self, error_message: str) -> Dict[str, Any]:
        """Create comparison result for processing errors"""
        return {
            'similarity_score': 0.0,
            'skills_match': {
                'matched_skills': [],
                'missing_skills': [],
                'additional_skills': []
            },
            'experience_match': {
                'level_match': False,
                'years_required': 'Unknown',
                'years_candidate': 'Unknown',
                'relevance_score': 0.0
            },
            'education_match': {
                'meets_requirements': False,
                'education_score': 0.0
            },
            'overall_assessment': {
                'strengths': [],
                'weaknesses': ['Processing error'],
                'recommendation': 'not_recommended'
            },
            'detailed_feedback': f'Error during analysis: {error_message}'
        }
    
    def _validate_comparison_result(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure comparison result has all required fields"""
        # Ensure similarity_score is valid
        if 'similarity_score' not in comparison or not isinstance(comparison['similarity_score'], (int, float)):
            comparison['similarity_score'] = 0.0
        
        # Clamp similarity score between 0 and 1
        comparison['similarity_score'] = max(0.0, min(1.0, float(comparison['similarity_score'])))
        
        # Ensure required nested structures exist
        if 'skills_match' not in comparison:
            comparison['skills_match'] = {
                'matched_skills': [],
                'missing_skills': [],
                'additional_skills': []
            }
        
        if 'experience_match' not in comparison:
            comparison['experience_match'] = {
                'level_match': False,
                'years_required': 'Not specified',
                'years_candidate': 'Not specified',
                'relevance_score': 0.0
            }
        
        if 'education_match' not in comparison:
            comparison['education_match'] = {
                'meets_requirements': False,
                'education_score': 0.0
            }
        
        if 'overall_assessment' not in comparison:
            comparison['overall_assessment'] = {
                'strengths': [],
                'weaknesses': [],
                'recommendation': 'not_recommended'
            }
        
        if 'detailed_feedback' not in comparison:
            comparison['detailed_feedback'] = 'Analysis completed'
        
        return comparison
    
    def _get_resume_text(self, app: Dict[str, Any]) -> str:
        """Get resume text from application, extracting if necessary"""
        resume_text = app.get('resume_text', '')
        
        # If we have valid resume text, use it
        if resume_text and len(resume_text.strip()) > 10:
            self.logger.info(f"Using stored resume text ({len(resume_text)} chars)")
            return resume_text.strip()
        
        # Try to extract from file
        resume_path = app.get('resume_path', '')
        if resume_path:
            self.logger.info(f"Attempting to extract text from file: {resume_path}")
            try:
                extracted_text = self.file_handler.extract_text_from_file(resume_path)
                if extracted_text and len(extracted_text.strip()) > 10:
                    self.logger.info(f"Successfully extracted {len(extracted_text)} characters")
                    
                    # Update the database with extracted text
                    self._update_application_resume_text(app['id'], extracted_text)
                    return extracted_text.strip()
                else:
                    self.logger.warning(f"Text extraction returned empty or too short text")
            except Exception as e:
                self.logger.error(f"Error extracting text from {resume_path}: {e}")
        
        # Fallback: create basic resume text from user info
        fallback_text = self._create_fallback_resume_text(app)
        self.logger.info(f"Using fallback resume text: {fallback_text}")
        return fallback_text
    
    def _create_fallback_resume_text(self, app: Dict[str, Any]) -> str:
        """Create basic resume text from available user information"""
        fallback_parts = []
        
        # Add basic info
        if app.get('full_name'):
            fallback_parts.append(f"Name: {app['full_name']}")
        
        if app.get('email'):
            fallback_parts.append(f"Email: {app['email']}")
        
        # Add a note about the issue
        fallback_parts.append("Note: Resume text could not be extracted from uploaded file.")
        fallback_parts.append("This is a basic profile generated from available information.")
        
        return "\n".join(fallback_parts)
    
    def _update_application_resume_text(self, application_id: int, resume_text: str):
        """Update application with extracted resume text"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE applications 
                    SET resume_text = %s 
                    WHERE id = %s
                """, (resume_text, application_id))
                self.logger.info(f"Updated resume text for application {application_id}")
        except Exception as e:
            self.logger.error(f"Error updating resume text: {e}")
    
    def _get_job_details(self, job_id: int) -> Dict[str, Any]:
        """Get job details from database"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, description, requirements, skills_required
                    FROM jobs WHERE id = %s
                """, (job_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return dict(result)
        except Exception as e:
            self.logger.error(f"Error fetching job details: {e}")
            return None
    
    def _get_job_applications(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all applications for a job"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT a.id, a.user_id, a.resume_text, a.resume_path, a.cover_letter,
                           u.full_name, u.email
                    FROM applications a
                    JOIN users u ON a.user_id = u.id
                    WHERE a.job_id = %s AND a.status = 'submitted'
                    ORDER BY a.applied_at DESC
                """, (job_id,))
                
                applications = []
                for row in cursor.fetchall():
                    applications.append(dict(row))
                
                return applications
        except Exception as e:
            self.logger.error(f"Error fetching applications: {e}")
            return []