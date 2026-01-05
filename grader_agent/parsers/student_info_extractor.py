"""LLM-based student information extractor."""

import json
import logging
import os
from typing import Tuple, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class StudentInfoExtractor:
    """Extract student name and ID using LLM."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize extractor.
        
        Args:
            api_key: OpenAI API key (if None, tries to get from env)
        """
        if not OpenAI:
            raise ImportError("openai package required. Install with: pip install openai")
        
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Use cheaper model for simple extraction
    
    def extract_from_text(self, text: str, filename: str = "") -> Tuple[str, Optional[str]]:
        """
        Extract student ID and name from text using LLM.
        
        Args:
            text: Text content from document (first 2000 chars is usually enough)
            filename: Optional filename for logging
        
        Returns:
            Tuple of (student_id, student_name)
        """
        # Use first 2000 characters - student info is usually at the top
        sample_text = text[:2000] if len(text) > 2000 else text
        
        prompt = f"""Extract the student's name and NetID/Student ID from the following document text.

Document text:
{sample_text}

Look for:
- Student name (could be labeled as "Name", "Author", "Student Name", "Submitted by", or just appear as a name)
- NetID or Student ID (could be labeled as "NetID", "Net ID", "Student ID", "ID", or appear as a pattern like "abc12345")

Respond in JSON format only:
{{
    "student_id": "abc12345" or "unknown" if not found,
    "student_name": "John Doe" or null if not found
}}

Be flexible with formats. The name might just appear without a label. The ID might be in various formats."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts student information from documents. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            student_id = result.get('student_id', 'unknown')
            student_name = result.get('student_name')
            
            # Clean up student_id
            if student_id and student_id.lower() != 'unknown':
                student_id = student_id.strip()
            else:
                student_id = 'unknown'
            
            # Clean up student_name
            if student_name:
                student_name = student_name.strip()
                if len(student_name) < 2:
                    student_name = None
            
            logger.info(f"LLM extracted from {filename}: student_id={student_id}, student_name={student_name}")
            
            return student_id, student_name
        
        except Exception as e:
            logger.error(f"Error extracting student info with LLM: {e}")
            return 'unknown', None

