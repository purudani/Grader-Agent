"""Simple parser for Jupyter notebook files."""

import re
import logging
from typing import Tuple, Dict, Optional
import nbformat

logger = logging.getLogger(__name__)


class NotebookParser:
    """Parse Jupyter notebooks to extract text content."""
    
    def __init__(self, path: str):
        """Initialize parser with notebook path."""
        self.path = path
        self.notebook = None
    
    def parse(self, use_llm_extraction: bool = True, api_key: Optional[str] = None) -> Tuple[str, str, Dict[str, str]]:
        """
        Parse the notebook and extract content.
        
        Returns:
            Tuple of (student_id, student_name, answers_dict)
        """
        try:
            self.notebook = nbformat.read(self.path, as_version=4)
        except Exception as e:
            logger.error(f"Failed to read notebook {self.path}: {e}")
            raise
        
        # Extract all text content
        student_id = "unknown"
        student_name = None
        answers = {}
        
        current_question = None
        current_content = []
        
        for cell in self.notebook.cells:
            source = cell.get("source", "")
            
            # Try to find student info in markdown cells
            if cell.cell_type == "markdown":
                netid_match = re.search(r"NetID\s*:\s*(\S+)", source, re.IGNORECASE)
                if netid_match:
                    student_id = netid_match.group(1).strip()
                
                author_match = re.search(r"Author\s*:\s*(.+)", source, re.IGNORECASE)
                if author_match:
                    student_name = author_match.group(1).strip()
                
                # Check for question markers
                question_match = re.search(
                    r"(?:Question|Problem|Q)\s*(\d+(?:\.\w+)?)",
                    source,
                    re.IGNORECASE
                )
                if question_match:
                    # Save previous question
                    if current_question:
                        answers[current_question] = "\n".join(current_content)
                    
                    # Start new question
                    current_question = question_match.group(1)
                    current_content = [source]
                elif current_question:
                    current_content.append(source)
            
            elif cell.cell_type == "code":
                if current_question:
                    current_content.append(source)
                else:
                    # If no question marker yet, use a default
                    if "default" not in answers:
                        answers["default"] = []
                    answers["default"].append(source)
        
        # Save last question
        if current_question:
            answers[current_question] = "\n".join(current_content)
        
        # If no questions found, combine all content
        if not answers:
            all_content = []
            for cell in self.notebook.cells:
                all_content.append(cell.get("source", ""))
            answers["all"] = "\n\n".join(all_content)
        
        # Try LLM extraction if enabled and regex didn't find both
        if use_llm_extraction and (student_id == "unknown" or student_name is None):
            try:
                from .student_info_extractor import StudentInfoExtractor
                extractor = StudentInfoExtractor(api_key=api_key)
                # Get all text content for LLM
                all_text = "\n\n".join([cell.get("source", "") for cell in self.notebook.cells])
                llm_id, llm_name = extractor.extract_from_text(all_text, self.path)
                
                # Use LLM results if regex didn't find them
                if student_id == "unknown" and llm_id != "unknown":
                    student_id = llm_id
                    logger.info(f"LLM found student_id: {student_id}")
                
                if student_name is None and llm_name:
                    student_name = llm_name
                    logger.info(f"LLM found student_name: {student_name}")
            except Exception as e:
                logger.warning(f"LLM extraction failed, using regex results: {e}")
        
        return student_id, student_name, answers
