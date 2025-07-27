# models/application.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Application:
    id: Optional[int] = None
    user_id: int = 0
    job_id: int = 0
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str = "submitted"
    applied_at: Optional[datetime] = None
