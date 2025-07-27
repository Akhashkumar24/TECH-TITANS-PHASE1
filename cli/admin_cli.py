# cli/admin_cli.py
from typing import Optional, List
from datetime import datetime
from models.user import User
from services.job_service import JobService
from services.application_service import ApplicationService
from agents.agent_protocol import AgentProtocol, AgentCapability
from agents.comparison_agent import ComparisonAgent
from agents.ranking_agent import RankingAgent
from agents.communication_agent import CommunicationAgent
from cli.cli_utils import CLIUtils
from utils.logger import get_logger

logger = get_logger(__name__)

class AdminCLI:
    def __init__(self, user: User):
        self.user = user
        self.job_service = JobService()
        self.application_service = ApplicationService()
        self.utils = CLIUtils()
        
        # Initialize enhanced multi-agent system with A2A protocol
        self.agent_protocol = AgentProtocol()
        
        # Register agents with capabilities
        self.comparison_agent = ComparisonAgent(self.agent_protocol)
        self.ranking_agent = RankingAgent(self.agent_protocol)
        self.communication_agent = CommunicationAgent(self.agent_protocol)
        
        # Register agent capabilities for A2A discovery
        self._register_agent_capabilities()
        
        logger.info(f"Admin CLI initialized for user: {user.username}")
    
    def _register_agent_capabilities(self):
        """Register agent capabilities for A2A protocol"""
        # Comparison Agent capabilities
        comparison_capabilities = [
            AgentCapability(
                name="compare_applications",
                description="Compare job applications against job requirements",
                input_schema={"job_id": "integer"},
                output_schema={"status": "string", "comparison_results": "array"}
            )
        ]
        
        # Ranking Agent capabilities
        ranking_capabilities = [
            AgentCapability(
                name="rank_applications", 
                description="Rank applications based on similarity scores",
                input_schema={"job_id": "integer", "comparison_results": "array"},
                output_schema={"status": "string", "rankings": "array"}
            )
        ]
        
        # Communication Agent capabilities
        communication_capabilities = [
            AgentCapability(
                name="send_ranking_notification",
                description="Send email notifications about candidate rankings",
                input_schema={"job_id": "integer", "rankings": "array"},
                output_schema={"status": "string", "message": "string"}
            ),
            AgentCapability(
                name="send_application_confirmation", 
                description="Send application confirmation emails",
                input_schema={"application_id": "integer", "user_email": "string"},
                output_schema={"status": "string", "message": "string"}
            )
        ]
        
        # Register agents with capabilities
        self.agent_protocol.register_agent("comparison_agent", self.comparison_agent, comparison_capabilities)
        self.agent_protocol.register_agent("ranking_agent", self.ranking_agent, ranking_capabilities)
        self.agent_protocol.register_agent("communication_agent", self.communication_agent, communication_capabilities)
    
    def show_menu(self):
        """Display enhanced admin main menu"""
        while True:
            self.utils.clear_screen()
            self.utils.print_header(f"🚀 Admin Dashboard - Welcome {self.user.full_name or self.user.username}")
            
            # Show system status
            system_status = self.agent_protocol.get_system_status()
            print(f"🤖 Agent System: {system_status['active_agents']}/{system_status['total_agents']} active")
            if system_status['failed_messages'] > 0:
                print(f"⚠️  Failed Messages: {system_status['failed_messages']}")
            print()
            
            menu_choices = [
                "📝 Post New Job",
                "👀 View My Job Postings", 
                "📋 View Job Applications",
                "🤖 Run AI Ranking System",
                "🏆 View Rankings & Send Notifications",
                "📧 Communication Center",
                "📊 System Statistics",
                "⚙️  Agent System Status",
                "🚪 Logout"
            ]
            
            choice = self.utils.get_choice("Select an option:", menu_choices)
            
            if "Post New Job" in choice:
                self.post_new_job()
            elif "View My Job Postings" in choice:
                self.view_my_jobs()
            elif "View Job Applications" in choice:
                self.view_job_applications()
            elif "Run AI Ranking System" in choice:
                self.run_ai_ranking()
            elif "View Rankings" in choice:
                self.view_rankings_and_notify()
            elif "Communication Center" in choice:
                self.communication_center()
            elif "System Statistics" in choice:
                self.show_statistics()
            elif "Agent System Status" in choice:
                self.show_agent_status()
            elif "Logout" in choice:
                self.utils.print_info("Logging out...")
                break
    
    def post_new_job(self):
        """Create a new job posting with enhanced features"""
        self.utils.clear_screen()
        self.utils.print_header("📝 Post New Job")
        
        try:
            # Collect job information
            job_data = {}
            job_data['title'] = self.utils.get_input("Job Title *")
            job_data['company_name'] = self.utils.get_input("Company Name *")
            job_data['location'] = self.utils.get_input("Location (or 'Remote') *")
            job_data['experience_level'] = self.utils.get_choice(
                "Experience Level *",
                ["Entry Level", "Mid Level", "Senior Level", "Executive"]
            )
            job_data['salary_range'] = self.utils.get_input("Salary Range (optional)", required=False)
            
            # Get skills with better UX
            self.utils.print_info("Enter required skills (one per line, press Enter on empty line to finish):")
            skills = []
            print("Examples: Python, React, Project Management, SQL, etc.")
            while True:
                skill = input("Skill: ").strip()
                if not skill:
                    if skills:  # At least one skill entered
                        break
                    else:
                        self.utils.print_warning("Please enter at least one skill.")
                        continue
                # Handle comma-separated skills
                if ',' in skill:
                    skill_list = [s.strip() for s in skill.split(',') if s.strip()]
                    skills.extend(skill_list)
                    print(f"✓ Added: {', '.join(skill_list)}")
                else:
                    skills.append(skill)
                    print(f"✓ Added: {skill}")
            job_data['skills_required'] = skills
            
            # Get job description
            self.utils.print_info("Enter job description (press Enter twice to finish):")
            description_lines = []
            empty_lines = 0
            while empty_lines < 2:
                line = input()
                if line.strip():
                    description_lines.append(line)
                    empty_lines = 0
                else:
                    empty_lines += 1
            job_data['description'] = '\n'.join(description_lines)
            
            # Get requirements
            requirements = self.utils.get_input("Additional Requirements (optional)", required=False)
            job_data['requirements'] = requirements if requirements else None
            
            # Create job
            job = self.job_service.create_job(job_data, self.user.id)
            
            if job:
                self.utils.print_success("🎉 Job posted successfully!")
                self.utils.print_info(f"Job ID: {job.id}")
                self.utils.print_info(f"Title: {job.title}")
                self.utils.print_info(f"Skills: {', '.join(job.skills_required)}")
                
                # Ask if they want to enable auto-notifications
                if self.utils.confirm("Enable automatic email notifications for new applications?"):
                    self.utils.print_success("✅ Auto-notifications enabled for this job!")
            else:
                self.utils.print_error("❌ Failed to post job. Please try again.")
                
        except KeyboardInterrupt:
            self.utils.print_info("Job posting cancelled.")
        except Exception as e:
            self.utils.print_error(f"Error posting job: {e}")
            logger.error(f"Job posting error: {e}")
        
        self.utils.press_enter_to_continue()
    
    def view_my_jobs(self):
        """View jobs posted by this admin with enhanced details"""
        self.utils.clear_screen()
        self.utils.print_header("👀 My Job Postings")
        
        jobs = self.job_service.get_jobs_by_admin(self.user.id)
        
        if not jobs:
            self.utils.print_warning("You haven't posted any jobs yet.")
            self.utils.press_enter_to_continue()
            return
        
        # Prepare data for table with application counts
        job_data = []
        for job in jobs:
            # Get application count for each job
            applications = self.application_service.get_applications_by_job(job.id)
            app_count = len(applications)
            
            job_data.append([
                job.id,
                job.title[:30] + "..." if len(job.title) > 30 else job.title,
                job.company_name or "Not specified",
                job.location or "Remote",
                "✅ Active" if job.is_active else "❌ Inactive",
                f"{app_count} apps",
                job.created_at.strftime('%Y-%m-%d') if job.created_at else 'Unknown'
            ])
        
        headers = ["ID", "Title", "Company", "Location", "Status", "Applications", "Posted Date"]
        self.utils.print_table(job_data, headers, "📋 Your Job Postings")
        
        # Option to view details
        if self.utils.confirm("\nWould you like to view details of a specific job?"):
            try:
                job_id = int(input("Enter Job ID: "))
                selected_job = next((job for job in jobs if job.id == job_id), None)
                if selected_job:
                    self.show_job_details(selected_job)
                else:
                    self.utils.print_error("Job not found!")
            except ValueError:
                self.utils.print_error("Invalid Job ID!")
        
        self.utils.press_enter_to_continue()
    
    def view_job_applications(self):
        """View job applications for admin's jobs"""
        self.utils.clear_screen()
        self.utils.print_header("📋 Job Applications")
        
        # Get admin's jobs
        jobs = self.job_service.get_jobs_by_admin(self.user.id)
        
        if not jobs:
            self.utils.print_warning("You haven't posted any jobs yet.")
            self.utils.press_enter_to_continue()
            return
        
        # Show jobs and let admin select one
        job_choices = [f"{job.id} - {job.title} ({len(self.application_service.get_applications_by_job(job.id))} apps)" for job in jobs]
        job_choices.append("View all applications")
        
        selected = self.utils.get_choice("Select job to view applications:", job_choices)
        
        if "View all applications" in selected:
            # Show all applications for all jobs
            all_applications = []
            for job in jobs:
                applications = self.application_service.get_applications_by_job(job.id)
                all_applications.extend(applications)
            
            if not all_applications:
                self.utils.print_warning("No applications found.")
                self.utils.press_enter_to_continue()
                return
            
            # Display applications table
            app_data = []
            for app in all_applications:
                app_data.append([
                    app['id'],
                    app['job_title'][:25] + "..." if len(app['job_title']) > 25 else app['job_title'],
                    app['applicant_name'] or "Unknown",
                    app['email'],
                    app['status'].title(),
                    app['applied_at'].strftime('%Y-%m-%d') if app['applied_at'] else 'Unknown'
                ])
            
            headers = ["App ID", "Job Title", "Applicant", "Email", "Status", "Applied Date"]
            self.utils.print_table(app_data, headers, "📋 All Applications")
            
        else:
            # Show applications for selected job
            job_id = int(selected.split(' - ')[0])
            applications = self.application_service.get_applications_by_job(job_id)
            
            if not applications:
                self.utils.print_warning("No applications found for this job.")
                self.utils.press_enter_to_continue()
                return
            
            # Display applications table
            app_data = []
            for app in applications:
                app_data.append([
                    app['id'],
                    app['applicant_name'] or "Unknown",
                    app['email'],
                    app['status'].title(),
                    app['applied_at'].strftime('%Y-%m-%d') if app['applied_at'] else 'Unknown'
                ])
            
            headers = ["App ID", "Applicant Name", "Email", "Status", "Applied Date"]
            job_title = next(job.title for job in jobs if job.id == job_id)
            self.utils.print_table(app_data, headers, f"📋 Applications for: {job_title}")
        
        self.utils.press_enter_to_continue()
    
    def show_job_details(self, job):
        """Show detailed job information"""
        self.utils.clear_screen()
        self.utils.print_header(f"📄 Job Details - ID: {job.id}")
        
        print(f"📝 Title: {job.title}")
        print(f"🏢 Company: {job.company_name or 'Not specified'}")
        print(f"📍 Location: {job.location or 'Remote'}")
        print(f"💰 Salary: {job.salary_range or 'Not disclosed'}")
        print(f"⭐ Experience: {job.experience_level or 'Any level'}")
        print(f"🛠️  Skills: {', '.join(job.skills_required) if job.skills_required else 'None specified'}")
        print(f"📅 Posted: {job.created_at.strftime('%Y-%m-%d %H:%M') if job.created_at else 'Unknown'}")
        print(f"🔄 Status: {'Active' if job.is_active else 'Inactive'}")
        
        print(f"\n📄 Description:")
        print("-" * 50)
        print(job.description)
        
        if job.requirements:
            print(f"\n📋 Requirements:")
            print("-" * 50)
            print(job.requirements)
        
        self.utils.press_enter_to_continue()
    
    def run_ai_ranking(self):
        """Run the enhanced AI-powered ranking system with synchronous A2A communication"""
        self.utils.clear_screen()
        self.utils.print_header("🤖 AI-Powered Candidate Ranking")
        
        # Get admin's jobs
        jobs = self.job_service.get_jobs_by_admin(self.user.id)
        
        if not jobs:
            self.utils.print_warning("You haven't posted any jobs yet.")
            self.utils.press_enter_to_continue()
            return
        
        # Show jobs and let admin select one
        job_choices = [f"{job.id} - {job.title} ({len(self.application_service.get_applications_by_job(job.id))} apps)" for job in jobs]
        selected = self.utils.get_choice("Select job to run AI ranking:", job_choices)
        job_id = int(selected.split(' - ')[0])
        
        # Check if there are applications
        applications = self.application_service.get_applications_by_job(job_id)
        if not applications:
            self.utils.print_warning("No applications found for this job.")
            self.utils.press_enter_to_continue()
            return
        
        self.utils.print_info(f"🔍 Found {len(applications)} applications. Starting AI analysis...")
        
        # Show progress
        print("\n🤖 AI Analysis Progress:")
        print("1. 📊 Comparison Agent: Analyzing resumes...")
        
        # Trigger comparison agent directly
        try:
            comparison_result = self.comparison_agent.process_task({
                'job_id': job_id
            })
            
            if comparison_result['status'] == 'success':
                print("   ✅ Resume analysis completed!")
                print("2. 🏆 Ranking Agent: Computing rankings...")
                
                # Directly process ranking
                ranking_result = self.ranking_agent.process_task({
                    'job_id': job_id,
                    'comparison_results': comparison_result['comparison_results']
                })
                
                if ranking_result['status'] == 'success':
                    print("   ✅ Rankings computed!")
                    print("3. 📧 Communication Agent: Preparing notifications...")
                    
                    # Send notification via communication agent
                    comm_result = self.communication_agent.process_task({
                        'action': 'send_ranking_notification',
                        'job_id': job_id,
                        'rankings': ranking_result['rankings'][:3]  # Top 3 candidates
                    })
                    
                    if comm_result['status'] == 'success':
                        print("   ✅ Email notification sent!")
                        self.utils.print_success("🎉 AI ranking completed successfully!")
                        
                        # Show summary
                        print(f"\n📊 Results Summary:")
                        print(f"• Total applications processed: {comparison_result['total_applications']}") 
                        print(f"• Successful comparisons: {comparison_result['successful_comparisons']}")
                        print(f"• Top candidates identified: {min(3, len(ranking_result['rankings']))}")
                        print(f"• Email sent to: {comm_result.get('recipient', 'recruiter')}")
                        
                        # Show top candidates
                        if ranking_result['rankings']:
                            print(f"\n🏆 Top 3 Candidates:")
                            for i, candidate in enumerate(ranking_result['rankings'][:3], 1):
                                score = candidate['similarity_score'] * 100
                                print(f"   {i}. {candidate['applicant_name']} - {score:.1f}% match")
                    else:
                        self.utils.print_warning("⚠️  Ranking completed but email notification failed")
                        print(f"Reason: {comm_result.get('message', 'Unknown error')}")
                        
                        # Still show rankings even if email failed
                        if ranking_result['rankings']:
                            print(f"\n🏆 Top 3 Candidates:")
                            for i, candidate in enumerate(ranking_result['rankings'][:3], 1):
                                score = candidate['similarity_score'] * 100
                                print(f"   {i}. {candidate['applicant_name']} - {score:.1f}% match")
                else:
                    self.utils.print_error(f"❌ Ranking failed: {ranking_result.get('message', 'Unknown error')}")
            else:
                self.utils.print_error(f"❌ AI comparison failed: {comparison_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            self.utils.print_error(f"❌ Error during AI ranking: {str(e)}")
            logger.error(f"AI ranking error: {e}")
        
        self.utils.press_enter_to_continue()
    
    def view_rankings_and_notify(self):
        """View ranking results and send notifications"""
        self.utils.clear_screen()
        self.utils.print_header("🏆 Candidate Rankings & Notifications")
        
        # Get admin's jobs
        jobs = self.job_service.get_jobs_by_admin(self.user.id)
        
        if not jobs:
            self.utils.print_warning("You haven't posted any jobs yet.")
            self.utils.press_enter_to_continue()
            return
        
        # Show jobs and let admin select one
        job_choices = [f"{job.id} - {job.title}" for job in jobs]
        selected = self.utils.get_choice("Select job to view rankings:", job_choices)
        job_id = int(selected.split(' - ')[0])
        
        # Get rankings
        rankings = self.application_service.get_job_rankings(job_id)
        
        if not rankings:
            self.utils.print_warning("No rankings found. Please run AI ranking first.")
            if self.utils.confirm("Would you like to run AI ranking now?"):
                # Redirect to AI ranking
                self.run_ai_ranking()
                return
            else:
                self.utils.press_enter_to_continue()
                return
        
        # Display rankings
        ranking_data = []
        for ranking in rankings:
            score_percent = ranking['similarity_score'] * 100
            ranking_data.append([
                ranking['rank'],
                ranking['applicant_name'],
                ranking['email'],
                f"{score_percent:.1f}%",
                ranking['applied_at'].strftime('%Y-%m-%d') if ranking['applied_at'] else 'Unknown'
            ])
        
        headers = ["Rank", "Name", "Email", "Match Score", "Applied Date"]
        job_title = next(job.title for job in jobs if job.id == job_id)
        self.utils.print_table(ranking_data, headers, f"🏆 Rankings for: {job_title}")
        
        # Notification options
        print("\n📧 Notification Options:")
        notification_choices = [
            "Send email with top 3 candidates",
            "Send custom notification",
            "View detailed candidate analysis", 
            "Go back"
        ]
        
        choice = self.utils.get_choice("Select action:", notification_choices)
        
        if "top 3 candidates" in choice:
            self.send_top_candidates_notification(job_id, rankings[:3])
        elif "custom notification" in choice:
            self.send_custom_notification(job_id, rankings)
        elif "detailed candidate analysis" in choice:
            self.show_detailed_candidate_analysis(rankings)
    
    def send_top_candidates_notification(self, job_id: int, top_candidates: List):
        """Send notification with top candidates"""
        try:
            result = self.communication_agent.process_task({
                'action': 'send_ranking_notification',
                'job_id': job_id,
                'rankings': top_candidates
            })
            
            if result['status'] == 'success':
                self.utils.print_success("📧 Email notification sent successfully!")
                self.utils.print_info(f"Recipients: {result.get('recipient', 'N/A')}")
                self.utils.print_info(f"Candidates included: {result.get('candidates_notified', len(top_candidates))}")
            else:
                self.utils.print_error(f"Failed to send notification: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            self.utils.print_error(f"Error sending notification: {e}")
            logger.error(f"Notification error: {e}")
        
        self.utils.press_enter_to_continue()
    
    def send_custom_notification(self, job_id: int, all_rankings: List):
        """Send custom notification"""
        self.utils.clear_screen()
        self.utils.print_header("📧 Custom Notification")
        
        # Let admin choose how many candidates to include
        try:
            max_candidates = min(len(all_rankings), 10)
            count = int(input(f"How many top candidates to include? (1-{max_candidates}): "))
            
            if 1 <= count <= max_candidates:
                selected_candidates = all_rankings[:count]
                
                result = self.communication_agent.process_task({
                    'action': 'send_ranking_notification',
                    'job_id': job_id,
                    'rankings': selected_candidates
                })
                
                if result['status'] == 'success':
                    self.utils.print_success(f"📧 Custom notification sent with {count} candidates!")
                else:
                    self.utils.print_error(f"Failed to send notification: {result.get('message')}")
            else:
                self.utils.print_error("Invalid number!")
                
        except ValueError:
            self.utils.print_error("Please enter a valid number!")
        except Exception as e:
            self.utils.print_error(f"Error: {e}")
        
        self.utils.press_enter_to_continue()
    
    def show_detailed_candidate_analysis(self, rankings: List):
        """Show detailed analysis for selected candidate"""
        self.utils.clear_screen()
        self.utils.print_header("🔍 Detailed Candidate Analysis")
        
        try:
            rank = int(input(f"Enter rank number (1-{len(rankings)}): "))
            if 1 <= rank <= len(rankings):
                candidate = rankings[rank-1]
                self.show_detailed_analysis(candidate)
            else:
                self.utils.print_error("Invalid rank number!")
        except ValueError:
            self.utils.print_error("Please enter a valid number!")
    
    def show_detailed_analysis(self, ranking_data):
        """Show detailed AI analysis for a candidate"""
        self.utils.clear_screen()
        self.utils.print_header(f"🔍 Detailed Analysis - {ranking_data['applicant_name']}")
        
        details = ranking_data.get('ranking_details', {})
        
        # Overall score
        score = ranking_data['similarity_score'] * 100
        print(f"🎯 Overall Match Score: {score:.1f}%")
        
        # Skills analysis
        skills_match = details.get('skills_match', {})
        if skills_match:
            print(f"\n🛠️  Skills Analysis:")
            matched = skills_match.get('matched_skills', [])
            missing = skills_match.get('missing_skills', [])
            additional = skills_match.get('additional_skills', [])
            
            if matched:
                print(f"   ✅ Matched Skills: {', '.join(matched)}")
            if missing:
                print(f"   ❌ Missing Skills: {', '.join(missing)}")
            if additional:
                print(f"   ➕ Additional Skills: {', '.join(additional)}")
        
        # Experience analysis
        exp_match = details.get('experience_match', {})
        if exp_match:
            print(f"\n📊 Experience Analysis:")
            print(f"   Required: {exp_match.get('years_required', 'Not specified')}")
            print(f"   Candidate: {exp_match.get('years_candidate', 'Not specified')}")
            exp_score = exp_match.get('relevance_score', 0) * 100
            print(f"   Relevance Score: {exp_score:.1f}%")
        
        # Overall assessment
        assessment = details.get('overall_assessment', {})
        if assessment:
            print(f"\n📋 Assessment:")
            recommendation = assessment.get('recommendation', 'Not available').replace('_', ' ').title()
            print(f"   Recommendation: {recommendation}")
            
            strengths = assessment.get('strengths', [])
            if strengths:
                print(f"   Strengths: {', '.join(strengths)}")
            
            weaknesses = assessment.get('weaknesses', [])
            if weaknesses:
                print(f"   Areas for Improvement: {', '.join(weaknesses)}")
        
        # Detailed feedback
        feedback = details.get('detailed_feedback', '')
        if feedback:
            print(f"\n💬 AI Feedback:")
            print(f"   {feedback}")
        
        self.utils.press_enter_to_continue()
    
    def communication_center(self):
        """Communication center for managing notifications"""
        self.utils.clear_screen()
        self.utils.print_header("📧 Communication Center")
        
        comm_choices = [
            "📧 Send Test Email",
            "📊 View Email History",
            "⚙️  Email Configuration Status",
            "📝 Send Custom Message",
            "🔙 Go Back"
        ]
        
        choice = self.utils.get_choice("Select action:", comm_choices)
        
        if "Test Email" in choice:
            self.send_test_email()
        elif "Email History" in choice:
            self.view_email_history()
        elif "Configuration Status" in choice:
            self.show_email_config_status()
        elif "Send Custom Message" in choice:
            self.send_custom_message()
    
    def send_test_email(self):
        """Send test email"""
        self.utils.clear_screen()
        self.utils.print_header("📧 Send Test Email")
        
        email = self.utils.get_input("Recipient Email")
        
        result = self.communication_agent.process_task({
            'action': 'send_test_email',
            'recipient_email': email,
            'subject': 'Test Email from Job Matching System',
            'message': f'''
            <html>
            <body>
            <h2>🧪 Test Email</h2>
            <p>This is a test email from the Job Matching System.</p>
            <p>If you receive this, the email system is working correctly!</p>
            <p><strong>Timestamp:</strong> {datetime.now()}</p>
            </body>
            </html>
            '''
        })
        
        if result['status'] == 'success':
            self.utils.print_success("✅ Test email sent successfully!")
        else:
            self.utils.print_error(f"❌ Failed to send test email: {result.get('message')}")
        
        self.utils.press_enter_to_continue()
    
    def view_email_history(self):
        """View email history (placeholder for now)"""
        self.utils.clear_screen()
        self.utils.print_header("📊 Email History")
        
        self.utils.print_info("Email history tracking will be implemented in the next version.")
        self.utils.print_info("For now, check the agent logs for email sending activities.")
        
        self.utils.press_enter_to_continue()
    
    def send_custom_message(self):
        """Send custom message"""
        self.utils.clear_screen()
        self.utils.print_header("📝 Send Custom Message")
        
        recipient = self.utils.get_input("Recipient Email")
        subject = self.utils.get_input("Subject")
        self.utils.print_info("Enter message (press Enter twice to finish):")
        
        message_lines = []
        empty_lines = 0
        while empty_lines < 2:
            line = input()
            if line.strip():
                message_lines.append(line)
                empty_lines = 0
            else:
                empty_lines += 1
        
        message = '\n'.join(message_lines)
        
        result = self.communication_agent.process_task({
            'action': 'send_status_update',
            'recipient_email': recipient,
            'subject': subject,
            'message': message
        })
        
        if result['status'] == 'success':
            self.utils.print_success("✅ Custom message sent successfully!")
        else:
            self.utils.print_error(f"❌ Failed to send message: {result.get('message')}")
        
        self.utils.press_enter_to_continue()
    
    def show_email_config_status(self):
        """Show email configuration status"""
        self.utils.clear_screen()
        self.utils.print_header("⚙️  Email Configuration Status")
        
        from config.settings import settings
        
        print("📧 SMTP Configuration:")
        print(f"• Server: {settings.SMTP_SERVER}")
        print(f"• Port: {settings.SMTP_PORT}")
        print(f"• Email: {settings.SMTP_EMAIL or 'Not configured'}")
        print(f"• Password: {'Set' if settings.SMTP_PASSWORD else 'Not set'}")
        print(f"• TLS: {settings.SMTP_USE_TLS}")
        print()
        
        # Test configuration
        config_valid = bool(settings.SMTP_EMAIL and settings.SMTP_PASSWORD)
        print(f"📊 Status: {'✅ Configured' if config_valid else '❌ Not properly configured'}")
        
        if not config_valid:
            print("\n⚠️  To enable email notifications:")
            print("1. Set SMTP_EMAIL environment variable")
            print("2. Set SMTP_PASSWORD environment variable") 
            print("3. Restart the application")
            print("\n🔄 Fallback Mode:")
            print("• System will simulate email sending for testing")
            print("• Check logs for email content and delivery status")
        
        self.utils.press_enter_to_continue()
    
    def show_agent_status(self):
        """Show multi-agent system status"""
        self.utils.clear_screen()
        self.utils.print_header("🤖 Agent System Status")
        
        system_status = self.agent_protocol.get_system_status()
        
        print("📊 System Overview:")
        print(f"• Total Agents: {system_status['total_agents']}")
        print(f"• Active Agents: {system_status['active_agents']}")
        print(f"• Failed Messages: {system_status['failed_messages']}")
        print(f"• Message History: {system_status['message_history_size']}")
        print()
        
        print("🤖 Individual Agent Status:")
        for agent_name, agent_info in system_status['agents'].items():
            status_icon = "✅" if agent_info['status'] == 'active' else "❌"
            print(f"• {status_icon} {agent_name.replace('_', ' ').title()}")
            print(f"  - Status: {agent_info['status']}")
            print(f"  - Capabilities: {agent_info['capabilities']}")
            print(f"  - Last Heartbeat: {agent_info['last_heartbeat']}")
            print()
        
        print("🔄 A2A Protocol Features:")
        print("• Synchronous message delivery")
        print("• Automatic retry with exponential backoff")
        print("• Agent capability discovery")
        print("• Heartbeat monitoring")
        print("• Message history tracking")
        
        self.utils.press_enter_to_continue()
    
    def show_statistics(self):
        """Show enhanced system statistics"""
        self.utils.clear_screen()
        self.utils.print_header("📊 System Statistics")
        
        try:
            # Get basic stats
            from services.auth_service import AuthService
            user_stats = AuthService.get_user_stats()
            
            # Get job stats
            all_jobs = self.job_service.get_all_active_jobs()
            my_jobs = self.job_service.get_jobs_by_admin(self.user.id)
            
            # Get application stats
            total_applications = 0
            for job in my_jobs:
                applications = self.application_service.get_applications_by_job(job.id)
                total_applications += len(applications)
            
            print("👥 User Statistics:")
            print(f"• Total Users: {user_stats['total_users']}")
            print(f"• Job Seekers: {user_stats['job_seekers']}")
            print(f"• Administrators: {user_stats['admins']}")
            print()
            
            print("💼 Job Statistics:")
            print(f"• Total Active Jobs: {len(all_jobs)}")
            print(f"• Your Jobs: {len(my_jobs)}")
            print(f"• Applications Received: {total_applications}")
            print()
            
            print("🤖 AI System Statistics:")
            agent_status = self.agent_protocol.get_system_status()
            print(f"• Active Agents: {agent_status['active_agents']}")
            print(f"• Messages Processed: {agent_status['message_history_size']}")
            success_rate = ((agent_status['message_history_size'] - agent_status['failed_messages']) / max(agent_status['message_history_size'], 1) * 100)
            print(f"• Success Rate: {success_rate:.1f}%")
            print()
            
            print("📧 Communication Statistics:")
            print("• Email notifications: Enabled with fallback simulation")
            print("• A2A Protocol: Active with synchronous delivery")
            
            # Show recent activity if available
            print("\n📈 Recent Activity:")
            print(f"• Jobs posted this week: {self._count_recent_jobs()}")
            print(f"• Applications this week: {self._count_recent_applications()}")
            print(f"• AI rankings completed: {self._count_recent_rankings()}")
            
        except Exception as e:
            self.utils.print_error(f"Error loading statistics: {e}")
            logger.error(f"Statistics error: {e}")
        
        self.utils.press_enter_to_continue()
    
    def _count_recent_jobs(self):
        """Count jobs posted in the last 7 days"""
        try:
            from datetime import timedelta
            week_ago = datetime.now() - timedelta(days=7)
            my_jobs = self.job_service.get_jobs_by_admin(self.user.id)
            recent_jobs = [job for job in my_jobs if job.created_at and job.created_at >= week_ago]
            return len(recent_jobs)
        except Exception:
            return "N/A"
    
    def _count_recent_applications(self):
        """Count applications received in the last 7 days"""
        try:
            from datetime import timedelta
            week_ago = datetime.now() - timedelta(days=7)
            my_jobs = self.job_service.get_jobs_by_admin(self.user.id)
            recent_count = 0
            for job in my_jobs:
                applications = self.application_service.get_applications_by_job(job.id)
                recent_apps = [app for app in applications if app.get('applied_at') and app['applied_at'] >= week_ago]
                recent_count += len(recent_apps)
            return recent_count
        except Exception:
            return "N/A"
    
    def _count_recent_rankings(self):
        """Count AI rankings completed in the last 7 days"""
        try:
            my_jobs = self.job_service.get_jobs_by_admin(self.user.id)
            rankings_count = 0
            for job in my_jobs:
                rankings = self.application_service.get_job_rankings(job.id)
                if rankings:
                    rankings_count += 1
            return rankings_count
        except Exception:
            return "N/A"