# services/gemini_service.py
import os
from typing import Dict, Any, List
from utils.logger import get_logger
import json
import re

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-generativeai not installed!")
    print("Please install it using: pip install google-generativeai")

logger = get_logger(__name__)

class GeminiService:
    def __init__(self):
        if not GENAI_AVAILABLE:
            logger.warning("Google Generative AI not available. Using fallback methods.")
            self.model = None
            return
        
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. AI features will use fallback methods.")
            self.model = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            # Use the newer Gemini 2.0 Flash model
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Configure generation settings for better JSON responses
            self.generation_config = genai.GenerationConfig(
                temperature=0.3,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
            
            logger.info("Gemini 2.0 Flash service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            # Fallback to older model if 2.0 Flash is not available
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.generation_config = genai.GenerationConfig(
                    temperature=0.3,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
                logger.info("Fallback to Gemini 1.5 Flash successful")
            except Exception as e2:
                logger.error(f"Fallback model also failed: {e2}")
                self.model = None
    
    def compare_resume_job(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Compare resume with job description using Gemini API"""
        if not self.model:
            logger.warning("Gemini API not available, using fallback comparison")
            return self._create_fallback_comparison(resume_text, job_description)
        
        # Clean and validate inputs
        resume_text = self._clean_text_for_analysis(resume_text)
        job_description = self._clean_text_for_analysis(job_description)
        
        if not resume_text or not job_description:
            logger.error("Empty resume text or job description")
            return self._create_fallback_comparison(resume_text, job_description)
        
        try:
            prompt = self._create_comparison_prompt(resume_text, job_description)
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if not response or not response.text:
                logger.error("Empty response from Gemini API")
                return self._create_fallback_comparison(resume_text, job_description)
            
            result_text = response.text.strip()
            logger.info(f"Raw Gemini response length: {len(result_text)} characters")
            
            # Parse the JSON response with better error handling
            parsed_result = self._parse_gemini_response(result_text)
            
            if parsed_result:
                logger.info(f"Resume-job comparison completed with similarity score: {parsed_result.get('similarity_score', 0)}")
                return parsed_result
            else:
                logger.error("Failed to parse Gemini response, using fallback")
                return self._create_fallback_comparison(resume_text, job_description)
                
        except Exception as e:
            logger.error(f"Error comparing resume with job: {e}")
            return self._create_fallback_comparison(resume_text, job_description)
    
    def _create_comparison_prompt(self, resume_text: str, job_description: str) -> str:
        """Create a well-structured prompt for resume-job comparison"""
        return f"""
You are an expert HR analyst. Analyze the resume and job description below to provide a comprehensive comparison.

**IMPORTANT**: Respond ONLY with valid JSON. Do not include any markdown formatting, explanations, or additional text.

JOB DESCRIPTION:
{job_description[:2000]}

RESUME:
{resume_text[:2000]}

Provide analysis in this exact JSON format:
{{
    "similarity_score": 0.75,
    "skills_match": {{
        "matched_skills": ["Python", "SQL", "Project Management"],
        "missing_skills": ["Java", "AWS"],
        "additional_skills": ["Docker", "React"]
    }},
    "experience_match": {{
        "level_match": true,
        "years_required": "3-5 years",
        "years_candidate": "4 years",
        "relevance_score": 0.8
    }},
    "education_match": {{
        "meets_requirements": true,
        "education_score": 0.9
    }},
    "overall_assessment": {{
        "strengths": ["Strong technical skills", "Relevant experience"],
        "weaknesses": ["Missing cloud experience"],
        "recommendation": "recommended"
    }},
    "detailed_feedback": "Candidate shows strong technical foundation with relevant experience..."
}}

Rules:
- similarity_score: float between 0.0 and 1.0
- recommendation: one of ["highly_recommended", "recommended", "consider", "not_recommended"]
- All scores: float between 0.0 and 1.0
- Provide realistic, helpful analysis based on the actual content
"""
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response with multiple fallback strategies"""
        try:
            # Strategy 1: Direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        try:
            # Strategy 2: Extract JSON from code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        try:
            # Strategy 3: Find JSON-like structure
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        try:
            # Strategy 4: Clean common formatting issues
            cleaned = response_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            # Remove any leading/trailing whitespace and newlines
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        logger.error(f"Failed to parse Gemini response: {response_text[:500]}...")
        return None
    
    def _clean_text_for_analysis(self, text: str) -> str:
        """Clean text for better AI analysis"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might confuse the model
        text = re.sub(r'[^\w\s\.\,\!\?\-\(\)\[\]\:\;]', '', text)
        
        # Limit length to prevent token overflow
        if len(text) > 3000:
            text = text[:3000] + "..."
        
        return text.strip()
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using Gemini API"""
        if not self.model:
            return self._extract_skills_fallback(text)
        
        try:
            prompt = f"""
Extract all technical skills, programming languages, frameworks, tools, and professional competencies from the following text.

TEXT:
{text[:2000]}

Respond with ONLY a JSON array of strings. No explanations or markdown formatting.

Example: ["Python", "Project Management", "SQL", "React", "Leadership"]
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if not response or not response.text:
                return self._extract_skills_fallback(text)
            
            result_text = response.text.strip()
            
            # Parse JSON array
            try:
                # Clean the response
                if result_text.startswith('```json'):
                    result_text = result_text[7:]
                elif result_text.startswith('```'):
                    result_text = result_text[3:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                
                result_text = result_text.strip()
                skills = json.loads(result_text)
                
                if isinstance(skills, list):
                    return [skill for skill in skills if isinstance(skill, str)]
                else:
                    return self._extract_skills_fallback(text)
                    
            except json.JSONDecodeError:
                logger.error(f"Failed to parse skills response: {result_text}")
                return self._extract_skills_fallback(text)
            
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return self._extract_skills_fallback(text)
    
    def generate_ranking_insights(self, rankings: List[Dict[str, Any]]) -> str:
        """Generate insights about the ranking results"""
        if not self.model:
            return self._generate_insights_fallback(rankings)
        
        try:
            prompt = f"""
Analyze the following candidate rankings and provide concise insights about the applicant pool.

RANKINGS DATA:
{json.dumps(rankings[:10], indent=2)}

Provide a brief analysis covering:
1. Overall quality of applicant pool
2. Common strengths across candidates
3. Skill gaps or areas for improvement
4. Hiring recommendations

Keep response under 300 words and actionable for hiring managers.
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                return self._generate_insights_fallback(rankings)
            
        except Exception as e:
            logger.error(f"Error generating ranking insights: {e}")
            return self._generate_insights_fallback(rankings)
    
    def _create_fallback_comparison(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Create a basic fallback comparison when Gemini API fails"""
        from utils.text_processor import TextProcessor
        
        processor = TextProcessor()
        basic_similarity = processor.calculate_text_similarity_basic(resume_text, job_description)
        
        # Extract basic skills from both texts
        resume_skills = processor.extract_skills(resume_text)
        job_skills = processor.extract_skills(job_description)
        
        matched_skills = list(set(resume_skills) & set(job_skills))
        missing_skills = list(set(job_skills) - set(resume_skills))
        additional_skills = list(set(resume_skills) - set(job_skills))
        
        return {
            "similarity_score": basic_similarity,
            "skills_match": {
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "additional_skills": additional_skills
            },
            "experience_match": {
                "level_match": basic_similarity > 0.5,
                "years_required": "Not specified",
                "years_candidate": "Not specified",
                "relevance_score": min(basic_similarity + 0.1, 1.0)
            },
            "education_match": {
                "meets_requirements": basic_similarity > 0.3,
                "education_score": min(basic_similarity + 0.2, 1.0)
            },
            "overall_assessment": {
                "strengths": ["Profile reviewed", "Basic skills analysis completed"] + matched_skills[:3],
                "weaknesses": ["Detailed AI analysis unavailable"] + missing_skills[:3] if missing_skills else ["No major gaps identified"],
                "recommendation": "recommended" if basic_similarity > 0.4 else "consider" if basic_similarity > 0.2 else "not_recommended"
            },
            "detailed_feedback": f"Basic similarity analysis completed with {basic_similarity:.1%} match. {len(matched_skills)} skills matched. AI-powered detailed analysis temporarily unavailable."
        }
    
    def _extract_skills_fallback(self, text: str) -> List[str]:
        """Fallback method for skill extraction"""
        from utils.text_processor import TextProcessor
        processor = TextProcessor()
        return processor.extract_skills(text)
    
    def _generate_insights_fallback(self, rankings: List[Dict[str, Any]]) -> str:
        """Fallback method for generating insights"""
        if not rankings:
            return "No rankings data available for analysis."
        
        total_candidates = len(rankings)
        avg_score = sum(r.get('similarity_score', 0) for r in rankings) / total_candidates if total_candidates > 0 else 0
        
        high_quality = sum(1 for r in rankings if r.get('similarity_score', 0) > 0.7)
        good_quality = sum(1 for r in rankings if 0.5 <= r.get('similarity_score', 0) <= 0.7)
        low_quality = sum(1 for r in rankings if r.get('similarity_score', 0) < 0.5)
        
        insights = f"""
CANDIDATE POOL ANALYSIS:

📊 Overview:
- Total Candidates: {total_candidates}
- Average Match Score: {avg_score:.1%}

📈 Quality Distribution:
- High-quality matches (>70%): {high_quality} candidates
- Good matches (50-70%): {good_quality} candidates
- Lower matches (<50%): {low_quality} candidates

💡 Recommendations:
- Focus on top {min(5, high_quality)} candidates for immediate interviews
- Consider second-tier candidates if more options needed
- Review job requirements if all scores are consistently low

📋 Next Steps:
- Schedule interviews with top-ranked candidates
- Prepare targeted questions based on skill gaps
- Consider skills training for high-potential candidates with minor gaps

Note: Enhanced AI insights available with full API access.
"""
        
        return insights