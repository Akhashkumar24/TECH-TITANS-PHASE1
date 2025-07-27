# models/job.py
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class Job:
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    requirements: Optional[str] = None
    skills_required: List[str] = None
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    company_name: Optional[str] = None
    posted_by: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.skills_required is None:
            self.skills_required = []
