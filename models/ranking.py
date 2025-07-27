# models/ranking.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Ranking:
    id: Optional[int] = None
    job_id: int = 0
    application_id: int = 0
    similarity_score: float = 0.0
    rank_position: int = 0
    ranking_details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    # Additional fields for display
    applicant_name: Optional[str] = None
    job_title: Optional[str] = None
    
    def __post_init__(self):
        if self.ranking_details is None:
            self.ranking_details = {}