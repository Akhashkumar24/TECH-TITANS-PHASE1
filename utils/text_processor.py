# utils/text_processor.py
import re
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class TextProcessor:
    def __init__(self):
        # Common technical skills keywords
        self.technical_skills = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'mongodb',
            'aws', 'docker', 'kubernetes', 'git', 'linux', 'html', 'css',
            'machine learning', 'data science', 'artificial intelligence'
        ]
        
        # Experience level keywords
        self.experience_levels = {
            'entry': ['entry', 'junior', 'fresher', '0-2 years', 'graduate'],
            'mid': ['mid', 'intermediate', '2-5 years', '3-6 years'],
            'senior': ['senior', 'lead', '5+ years', '7+ years', 'principal']
        }
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.technical_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Extract additional skills using patterns
        skill_patterns = [
            r'\b\w+(?:\.js|\.py|\.java)\b',  # File extensions
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text)
            found_skills.extend(matches)
        
        return list(set(found_skills))
    
    def extract_experience_level(self, text: str) -> str:
        """Extract experience level from text"""
        text_lower = text.lower()
        
        for level, keywords in self.experience_levels.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
        
        # Try to extract years of experience
        years_match = re.search(r'(\d+)\+?\s*years?', text_lower)
        if years_match:
            years = int(years_match.group(1))
            if years <= 2:
                return 'entry'
            elif years <= 5:
                return 'mid'
            else:
                return 'senior'
        
        return 'unknown'
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters except basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
        
        return text.strip()
    
    def calculate_text_similarity_basic(self, text1: str, text2: str) -> float:
        """Basic text similarity calculation (Jaccard similarity)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return 0.0
        
        return len(intersection) / len(union)