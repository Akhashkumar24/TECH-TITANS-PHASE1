# services/job_service.py
from typing import List, Optional, Dict, Any
from models.job import Job
from config.database import db_connection
from utils.logger import get_logger

logger = get_logger(__name__)

class JobService:
    @staticmethod
    def create_job(job_data: Dict[str, Any], posted_by: int) -> Optional[Job]:
        """Create a new job posting"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO jobs (title, description, requirements, skills_required,
                                    experience_level, salary_range, location, company_name, posted_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """, (
                    job_data.get('title'),
                    job_data.get('description'),
                    job_data.get('requirements'),
                    job_data.get('skills_required', []),
                    job_data.get('experience_level'),
                    job_data.get('salary_range'),
                    job_data.get('location'),
                    job_data.get('company_name'),
                    posted_by
                ))
                
                result = cursor.fetchone()
                if result:
                    job = Job(
                        id=result['id'],
                        title=job_data.get('title'),
                        description=job_data.get('description'),
                        requirements=job_data.get('requirements'),
                        skills_required=job_data.get('skills_required', []),
                        experience_level=job_data.get('experience_level'),
                        salary_range=job_data.get('salary_range'),
                        location=job_data.get('location'),
                        company_name=job_data.get('company_name'),
                        posted_by=posted_by,
                        created_at=result['created_at']
                    )
                    logger.info(f"Job created successfully: {job.title}")
                    return job
                    
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None
    
    @staticmethod
    def get_all_active_jobs() -> List[Job]:
        """Get all active job postings"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, description, requirements, skills_required,
                           experience_level, salary_range, location, company_name,
                           posted_by, is_active, created_at
                    FROM jobs WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """)
                
                jobs = []
                for row in cursor.fetchall():
                    job = Job(
                        id=row['id'],
                        title=row['title'],
                        description=row['description'],
                        requirements=row['requirements'],
                        skills_required=row['skills_required'] or [],
                        experience_level=row['experience_level'],
                        salary_range=row['salary_range'],
                        location=row['location'],
                        company_name=row['company_name'],
                        posted_by=row['posted_by'],
                        is_active=row['is_active'],
                        created_at=row['created_at']
                    )
                    jobs.append(job)
                
                return jobs
                
        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            return []
    
    @staticmethod
    def get_job_by_id(job_id: int) -> Optional[Job]:
        """Get job by ID"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, description, requirements, skills_required,
                           experience_level, salary_range, location, company_name,
                           posted_by, is_active, created_at
                    FROM jobs WHERE id = %s
                """, (job_id,))
                
                row = cursor.fetchone()
                if row:
                    return Job(
                        id=row['id'],
                        title=row['title'],
                        description=row['description'],
                        requirements=row['requirements'],
                        skills_required=row['skills_required'] or [],
                        experience_level=row['experience_level'],
                        salary_range=row['salary_range'],
                        location=row['location'],
                        company_name=row['company_name'],
                        posted_by=row['posted_by'],
                        is_active=row['is_active'],
                        created_at=row['created_at']
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {e}")
            return None
    
    @staticmethod
    def get_jobs_by_admin(admin_id: int) -> List[Job]:
        """Get all jobs posted by a specific admin"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, description, requirements, skills_required,
                           experience_level, salary_range, location, company_name,
                           posted_by, is_active, created_at
                    FROM jobs WHERE posted_by = %s
                    ORDER BY created_at DESC
                """, (admin_id,))
                
                jobs = []
                for row in cursor.fetchall():
                    job = Job(
                        id=row['id'],
                        title=row['title'],
                        description=row['description'],
                        requirements=row['requirements'],
                        skills_required=row['skills_required'] or [],
                        experience_level=row['experience_level'],
                        salary_range=row['salary_range'],
                        location=row['location'],
                        company_name=row['company_name'],
                        posted_by=row['posted_by'],
                        is_active=row['is_active'],
                        created_at=row['created_at']
                    )
                    jobs.append(job)
                
                return jobs
                
        except Exception as e:
            logger.error(f"Error fetching admin jobs: {e}")
            return []
