# config/gemini_config.py
from services.gemini_service import GeminiService

# Global Gemini service instance
try:
    gemini_service = GeminiService()
    if gemini_service.model is None:
        print("Warning: Gemini service initialized with fallback methods only")
except Exception as e:
    print(f"Warning: Could not initialize Gemini service: {e}")
    gemini_service = None = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean the response to extract JSON
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            # Parse JSON response
            try:
                result = json.loads(result_text)
                logger.info(f"Resume-job comparison completed with similarity score: {result.get('similarity_score', 0)}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                return self._create_fallback_comparison(resume_text, job_description)
                
        except Exception as e:
            logger.error(f"Error comparing resume with job: {e}")
            return self._create_fallback_comparison(resume_text, job_description)
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using Gemini API"""
        if not self.model:
            return self._extract_skills_fallback(text)
        
        try:
            prompt = f"""
            Extract all technical skills, soft skills, and professional competencies from the following text.
            Return the result as a JSON array of strings.
            
            TEXT:
            {text}
            
            Example format: ["Python", "Project Management", "Communication", "SQL", "Leadership"]
            """
            
            response