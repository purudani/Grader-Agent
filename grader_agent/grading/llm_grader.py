"""Simple LLM grader."""

import json
import logging
from typing import Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class LLMGrader:
    """Simple LLM-based grader."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize LLM grader.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        if not OpenAI:
            raise ImportError("openai package required. Install with: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def grade_simple(self, base_content: str, student_content: str, filename: str, 
                     student_id: str = None, student_name: str = None, include_debug: bool = True) -> Dict:
        """
        Grade student submission against base solution.
        
        Args:
            base_content: Content from base solution file
            student_content: Content from student submission
            filename: Student filename
            student_id: Student NetID
            student_name: Student name
            include_debug: Whether to include debug information
        
        Returns:
            Dictionary with grading results and debug info
        """
        system_message = "You are a helpful grading assistant. Always respond with valid JSON."
        prompt = f"""You are a grading assistant. Compare the student submission against the base solution and provide a detailed grade.

BASE SOLUTION:
{base_content}

STUDENT SUBMISSION:
{student_content}

Please provide:
1. A score out of 100
2. A brief feedback (2-3 sentences)
3. Detailed breakdown of deductions: For each mistake or missing element, specify:
   - The specific issue or mistake
   - The number of points deducted for that issue
   - Which section/question it relates to (if applicable)

CRITICAL REQUIREMENT: The sum of ALL points_deducted values MUST EXACTLY equal (100 - score). 
For example, if score is 80, then the total of all points_deducted must be exactly 20.
Double-check your math before responding. If you find 6 issues worth 5 points each but only 20 points should be deducted total, 
you must adjust the point values proportionally (e.g., 3.33 points each) or combine some deductions.

Respond in JSON format:
{{
    "score": 85,
    "feedback": "Overall good work, but missed some edge cases.",
    "deductions": [
        {{
            "issue": "Missing error handling in Question 1",
            "points_deducted": 5,
            "section": "Question 1"
        }},
        {{
            "issue": "Incorrect calculation in part 2",
            "points_deducted": 7,
            "section": "Question 2"
        }},
        {{
            "issue": "Missing explanation",
            "points_deducted": 3,
            "section": "Question 3"
        }}
    ]
}}
"""
        
        # Prepare API request details
        api_request = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        
        try:
            # Log the full request
            logger.info(f"=== API Request for {filename} ===")
            logger.info(f"Model: {self.model}")
            logger.info(f"System Message: {system_message}")
            logger.info(f"User Prompt Length: {len(prompt)} characters")
            logger.info(f"Full Prompt:\n{prompt}")
            
            # Make API call
            response = self.client.chat.completions.create(**api_request)
            
            # Extract response details
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Get API response metadata
            api_response_details = {
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason,
                "raw_response": result_text
            }
            
            logger.info(f"=== API Response for {filename} ===")
            logger.info(f"Tokens Used: {api_response_details['usage']}")
            logger.info(f"Raw Response: {result_text}")
            logger.info(f"Parsed Result: {result}")
            
            # Build result
            result_dict = {
                'filename': filename,
                'student_id': student_id or 'Unknown',
                'student_name': student_name or 'Unknown',
                'score': result.get('score', 0),
                'feedback': result.get('feedback', ''),
                'deductions': result.get('deductions', [])
            }
            
            # Validate deductions format - convert old format to new format if needed
            deductions = result.get('deductions', [])
            if deductions and isinstance(deductions[0], str):
                # Old format: list of strings, convert to new format
                total_deducted = 100 - result_dict['score']
                points_per_deduction = total_deducted / len(deductions) if deductions else 0
                result_dict['deductions'] = [
                    {
                        'issue': d,
                        'points_deducted': round(points_per_deduction, 1),
                        'section': 'General'
                    }
                    for d in deductions
                ]
            else:
                # Validate that deductions add up correctly
                total_deducted_expected = 100 - result_dict['score']
                total_deducted_actual = sum(
                    d.get('points_deducted', 0) for d in deductions if isinstance(d, dict)
                )
                
                # If deductions don't add up, normalize them proportionally
                if deductions and abs(total_deducted_actual - total_deducted_expected) > 0.1:
                    logger.warning(
                        f"Deductions don't add up correctly for {filename}. "
                        f"Expected: {total_deducted_expected}, Got: {total_deducted_actual}. "
                        f"Normalizing proportionally."
                    )
                    
                    if total_deducted_actual > 0:
                        # Scale all deductions proportionally
                        scale_factor = total_deducted_expected / total_deducted_actual
                        for d in deductions:
                            if isinstance(d, dict):
                                d['points_deducted'] = round(d.get('points_deducted', 0) * scale_factor, 1)
                    else:
                        # If no deductions but score < 100, distribute evenly
                        if total_deducted_expected > 0:
                            points_per_deduction = total_deducted_expected / len(deductions)
                            for d in deductions:
                                if isinstance(d, dict):
                                    d['points_deducted'] = round(points_per_deduction, 1)
                
                result_dict['deductions'] = deductions
            
            # Add debug information if requested
            if include_debug:
                result_dict['debug'] = {
                    'api_request': {
                        'model': api_request['model'],
                        'system_message': system_message,
                        'user_prompt': prompt,
                        'temperature': api_request['temperature'],
                        'prompt_length': len(prompt),
                        'base_content_length': len(base_content),
                        'student_content_length': len(student_content)
                    },
                    'api_response': api_response_details,
                    'parsed_result': result
                }
            
            return result_dict
        
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}", exc_info=True)
            error_result = {
                'filename': filename,
                'student_id': student_id or 'Unknown',
                'student_name': student_name or 'Unknown',
                'error': str(e),
                'score': 0,
                'feedback': f'Error during grading: {str(e)}',
                'deductions': []
            }
            
            if include_debug:
                error_result['debug'] = {
                    'api_request': api_request,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            
            return error_result
