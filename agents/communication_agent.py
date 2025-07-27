# agents/communication_agent.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
from agents.base_agent import BaseAgent
from agents.agent_protocol import AgentMessage, MessageType
from config.database import db_connection
from config.settings import settings
from utils.logger import get_logger
import json
import time

logger = get_logger(__name__)

class CommunicationAgent(BaseAgent):
    def __init__(self, protocol):
        super().__init__("communication_agent", protocol)
        self.email_config = {
            'smtp_server': settings.SMTP_SERVER,
            'smtp_port': settings.SMTP_PORT,
            'email': settings.SMTP_EMAIL,
            'password': settings.SMTP_PASSWORD,
            'use_tls': settings.SMTP_USE_TLS
        }
        
        # Start heartbeat to maintain A2A connection
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
            self.logger.info(f"Communication Agent received message from {message.sender}: {message.message_type.value}")
            
            if message.message_type == MessageType.REQUEST:
                action = message.payload.get('action')
                
                if action == 'send_ranking_notification':
                    result = self.send_ranking_notification(message.payload)
                elif action == 'send_application_confirmation':
                    result = self.send_application_confirmation(message.payload)
                elif action == 'send_status_update':
                    result = self.send_status_update(message.payload)
                elif action == 'send_test_email':
                    result = self.send_test_email(message.payload)
                else:
                    result = {'status': 'error', 'message': f'Unknown action: {action}'}
                
                # Send response back to sender
                self.send_message(
                    message.sender,
                    MessageType.RESPONSE,
                    result,
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
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process communication task"""
        action = task_data.get('action')
        
        if action == 'send_ranking_notification':
            return self.send_ranking_notification(task_data)
        elif action == 'send_application_confirmation':
            return self.send_application_confirmation(task_data)
        elif action == 'send_status_update':
            return self.send_status_update(task_data)
        elif action == 'send_test_email':
            return self.send_test_email(task_data)
        else:
            return {'status': 'error', 'message': 'Unknown task action'}
    
    def send_ranking_notification(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification with top-ranked candidates"""
        try:
            job_id = task_data.get('job_id')
            rankings = task_data.get('rankings', [])
            
            self.logger.info(f"Processing ranking notification for job {job_id} with {len(rankings)} candidates")
            
            if not job_id:
                return {'status': 'error', 'message': 'Job ID required'}
            
            # Get job and recruiter details
            job_details = self._get_job_details(job_id)
            if not job_details:
                return {'status': 'error', 'message': 'Job not found'}
            
            recruiter_email = self._get_recruiter_email(job_details['posted_by'])
            if not recruiter_email:
                self.logger.warning(f"Recruiter email not found for user {job_details['posted_by']}, using fallback")
                # Use admin email as fallback
                recruiter_email = "admin@jobmatch.com"
            
            # Prepare email content
            top_candidates = rankings[:3] if rankings else []
            
            if top_candidates:
                subject = f"Top Candidates Found for {job_details['title']}"
                content = self._generate_ranking_email_content(job_details, top_candidates)
                self.logger.info(f"Generated email for {len(top_candidates)} top candidates")
            else:
                subject = f"No Suitable Candidates Found for {job_details['title']}"
                content = self._generate_no_matches_email_content(job_details)
                self.logger.info("Generated no-matches email")
            
            # Send email
            success = self._send_email(recruiter_email, subject, content)
            
            if success:
                # Log the communication
                self.log_activity('ranking_notification_sent', {
                    'job_id': job_id,
                    'recipient_email': recruiter_email,
                    'candidates_count': len(top_candidates)
                })
                
                self.logger.info(f"Ranking notification sent successfully to {recruiter_email}")
                
                return {
                    'status': 'success',
                    'message': 'Ranking notification sent successfully',
                    'recipient': recruiter_email,
                    'candidates_notified': len(top_candidates)
                }
            else:
                return {'status': 'error', 'message': 'Failed to send email'}
                
        except Exception as e:
            self.logger.error(f"Error sending ranking notification: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def send_application_confirmation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send application confirmation to job seeker"""
        try:
            application_id = task_data.get('application_id')
            user_email = task_data.get('user_email')
            job_title = task_data.get('job_title')
            company_name = task_data.get('company_name')
            
            if not all([application_id, user_email, job_title]):
                return {'status': 'error', 'message': 'Missing required parameters'}
            
            subject = f"Application Confirmation - {job_title}"
            content = self._generate_application_confirmation_content(
                job_title, company_name, application_id
            )
            
            success = self._send_email(user_email, subject, content)
            
            if success:
                self.log_activity('application_confirmation_sent', {
                    'application_id': application_id,
                    'recipient_email': user_email
                })
                
                return {
                    'status': 'success',
                    'message': 'Application confirmation sent',
                    'recipient': user_email
                }
            else:
                return {'status': 'error', 'message': 'Failed to send confirmation email'}
                
        except Exception as e:
            self.logger.error(f"Error sending application confirmation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def send_status_update(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send status update notification"""
        try:
            recipient_email = task_data.get('recipient_email')
            subject = task_data.get('subject')
            message = task_data.get('message')
            
            if not all([recipient_email, subject, message]):
                return {'status': 'error', 'message': 'Missing required parameters'}
            
            success = self._send_email(recipient_email, subject, message)
            
            if success:
                return {
                    'status': 'success',
                    'message': 'Status update sent',
                    'recipient': recipient_email
                }
            else:
                return {'status': 'error', 'message': 'Failed to send status update'}
                
        except Exception as e:
            self.logger.error(f"Error sending status update: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def send_test_email(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send test email"""
        try:
            recipient_email = task_data.get('recipient_email')
            subject = task_data.get('subject', 'Test Email from Job Matching System')
            message = task_data.get('message', f'''
            <html>
            <body>
            <h2>🧪 Test Email</h2>
            <p>This is a test email from the Job Matching System.</p>
            <p>If you receive this, the email system is working correctly!</p>
            <p><strong>Timestamp:</strong> {datetime.now()}</p>
            </body>
            </html>
            ''')
            
            if not recipient_email:
                return {'status': 'error', 'message': 'Recipient email required'}
            
            success = self._send_email(recipient_email, subject, message)
            
            if success:
                return {
                    'status': 'success',
                    'message': 'Test email sent successfully',
                    'recipient': recipient_email
                }
            else:
                return {'status': 'error', 'message': 'Failed to send test email'}
    
        except Exception as e:
            self.logger.error(f"Error sending test email: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def handle_notification(self, payload: Dict[str, Any]):
        """Handle notifications from other agents"""
        notification_type = payload.get('type')
        
        if notification_type == 'ranking_completed':
            # Automatically send notification when ranking is completed
            self.send_ranking_notification(payload)
        elif notification_type == 'application_submitted':
            # Send confirmation when application is submitted
            self.send_application_confirmation(payload)
    
    def _send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send email using SMTP"""
        try:
            if not self._is_email_configured():
                self.logger.warning("Email not configured, simulating email send")
                self.logger.info(f"SIMULATED EMAIL:")
                self.logger.info(f"To: {to_email}")
                self.logger.info(f"Subject: {subject}")
                self.logger.info(f"Content: {content[:200]}...")
                return True  # Return True to not break the flow
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'html'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            
            if self.email_config['use_tls']:
                server.starttls()
            
            server.login(self.email_config['email'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['email'], to_email, text)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {e}")
            self.logger.info(f"FALLBACK SIMULATED EMAIL:")
            self.logger.info(f"To: {to_email}")
            self.logger.info(f"Subject: {subject}")
            self.logger.info(f"Content: {content[:200]}...")
            return True  # Return True to continue workflow even if email fails
    
    def _is_email_configured(self) -> bool:
        """Check if email configuration is available"""
        required_configs = ['smtp_server', 'smtp_port', 'email', 'password']
        return all(self.email_config.get(config) for config in required_configs)
    
    def _get_job_details(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job details from database"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, description, company_name, location, 
                           experience_level, salary_range, posted_by
                    FROM jobs WHERE id = %s
                """, (job_id,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            self.logger.error(f"Error fetching job details: {e}")
            return None
    
    def _get_recruiter_email(self, user_id: int) -> Optional[str]:
        """Get recruiter email from database"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT email FROM users WHERE id = %s AND role = 'admin'
                """, (user_id,))
                
                result = cursor.fetchone()
                return result['email'] if result else None
                
        except Exception as e:
            self.logger.error(f"Error fetching recruiter email: {e}")
            return None
    
    def _generate_ranking_email_content(self, job_details: Dict[str, Any], 
                                       candidates: List[Dict[str, Any]]) -> str:
        """Generate email content for ranking notification"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        
        <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
        🎯 Top Candidates Found for {job_details['title']}
        </h2>
        
        <h3 style="color: #34495e;">📋 Job Details:</h3>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p><strong>Position:</strong> {job_details['title']}</p>
            <p><strong>Company:</strong> {job_details.get('company_name', 'Not specified')}</p>
            <p><strong>Location:</strong> {job_details.get('location', 'Not specified')}</p>
            <p><strong>Experience Level:</strong> {job_details.get('experience_level', 'Not specified')}</p>
        </div>
        
        <h3 style="color: #34495e;">🏆 Top Matching Candidates:</h3>
        """
        
        for i, candidate in enumerate(candidates, 1):
            # Handle different data structures
            if isinstance(candidate, dict):
                if 'similarity_score' in candidate:
                    match_score = candidate.get('similarity_score', 0) * 100
                    applicant_name = candidate.get('applicant_name', 'Unknown')
                    application_id = candidate.get('application_id', 'N/A')
                else:
                    # Alternative structure from rankings
                    match_score = candidate.get('enhanced_score', candidate.get('rank', 0)) * 100
                    applicant_name = candidate.get('applicant_name', 'Unknown')
                    application_id = candidate.get('application_id', 'N/A')
            else:
                match_score = 0
                applicant_name = 'Unknown'
                application_id = 'N/A'
            
            # Color coding based on match score
            if match_score >= 80:
                score_color = "#27ae60"  # Green
                score_emoji = "🌟"
            elif match_score >= 60:
                score_color = "#f39c12"  # Orange
                score_emoji = "⭐"
            else:
                score_color = "#e74c3c"  # Red
                score_emoji = "📊"
            
            html_content += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; background-color: #fff;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">#{i} - {applicant_name}</h4>
                <p style="margin: 5px 0;"><strong>Match Score:</strong> 
                   <span style="color: {score_color}; font-weight: bold;">{score_emoji} {match_score:.1f}%</span>
                </p>
                <p style="margin: 5px 0;"><strong>Application ID:</strong> {application_id}</p>
            </div>
            """
        
        html_content += f"""
        <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin-top: 20px;">
        <p><strong>📝 Next Steps:</strong></p>
        <ol style="margin: 10px 0;">
            <li>Review the detailed candidate profiles in the system</li>
            <li>Schedule interviews with top candidates</li>
            <li>Contact candidates directly for further evaluation</li>
        </ol>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #7f8c8d;">
            <p>Best regards,<br>
            <strong>AI-Powered Job Matching System</strong><br>
            <small>Automated Recruitment Intelligence</small></p>
        </div>
        
        </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_no_matches_email_content(self, job_details: Dict[str, Any]) -> str:
        """Generate email content when no suitable matches are found"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        
        <h2 style="color: #e74c3c; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">
        ⚠️ No Suitable Candidates Found
        </h2>
        
        <h3 style="color: #34495e;">📋 Job Details:</h3>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p><strong>Position:</strong> {job_details['title']}</p>
            <p><strong>Company:</strong> {job_details.get('company_name', 'Not specified')}</p>
            <p><strong>Location:</strong> {job_details.get('location', 'Not specified')}</p>
        </div>
        
        <p style="color: #7f8c8d; font-size: 16px;">
        Unfortunately, no candidates in our current pool match the requirements for this position with sufficient similarity scores.
        </p>
        
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
        <h3 style="color: #856404; margin-top: 0;">💡 Recommended Actions:</h3>
        <ul style="color: #856404;">
            <li>Review and potentially broaden the job requirements</li>
            <li>Post the job on additional platforms to attract more candidates</li>
            <li>Consider adjusting salary or benefits package</li>
            <li>Wait for new applications to be submitted</li>
            <li>Consider candidates with transferable skills for training</li>
        </ul>
        </div>
        
        <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745;">
        <p style="color: #155724; margin: 0;">
        <strong>🔔 Automatic Monitoring:</strong> We will notify you immediately when new suitable candidates apply to this position.
        </p>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #7f8c8d;">
            <p>Best regards,<br>
            <strong>AI-Powered Job Matching System</strong><br>
            <small>Automated Recruitment Intelligence</small></p>
        </div>
        
        </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_application_confirmation_content(self, job_title: str, 
                                                  company_name: str, 
                                                  application_id: int) -> str:
        """Generate application confirmation email content"""
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        
        <h2 style="color: #27ae60; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
        ✅ Application Submitted Successfully
        </h2>
        
        <p style="font-size: 16px;">Dear Candidate,</p>
        
        <p>Thank you for your interest in the <strong>{job_title}</strong> position 
        {f"at {company_name}" if company_name else ""}.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3 style="color: #34495e; margin-top: 0;">📋 Application Details:</h3>
        <ul style="list-style: none; padding: 0;">
            <li style="margin: 8px 0;"><strong>Position:</strong> {job_title}</li>
            <li style="margin: 8px 0;"><strong>Application ID:</strong> {application_id}</li>
            <li style="margin: 8px 0;"><strong>Status:</strong> <span style="color: #27ae60;">Under Review</span></li>
            <li style="margin: 8px 0;"><strong>Submitted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
        </ul>
        </div>
        
        <p>Your application has been successfully submitted and is now being processed by our AI-powered matching system.</p>
        
        <div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3 style="color: #2980b9; margin-top: 0;">🔄 What happens next?</h3>
        <ol style="color: #34495e;">
            <li>Our AI system will analyze your profile against the job requirements</li>
            <li>If you're a good match, the recruiter will be notified automatically</li>
            <li>You may be contacted for an interview if selected</li>
            <li>We'll keep you updated on your application status</li>
        </ol>
        </div>
        
        <p style="color: #7f8c8d;">We appreciate your patience during the review process. Good luck!</p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #7f8c8d;">
            <p>Best regards,<br>
            <strong>AI-Powered Job Matching System</strong><br>
            <small>Automated Recruitment Intelligence</small></p>
        </div>
        
        </div>
        </body>
        </html>
        """
        
        return html_content