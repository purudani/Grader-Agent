"""Simple Flask web app for grading assignments."""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import shutil

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

from grader_agent.parsers import NotebookParser, DocxParser
from grader_agent.grading.llm_grader import LLMGrader

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_and_info(file_path: str, api_key: str = None):
    """Extract text content and student info from a file."""
    if file_path.endswith('.ipynb'):
        parser = NotebookParser(file_path)
        student_id, student_name, answers = parser.parse(use_llm_extraction=True, api_key=api_key)
        # Combine all answers into one text
        content = "\n\n".join([f"Question {qid}:\n{answer}" for qid, answer in answers.items()])
        return content, student_id, student_name
    elif file_path.endswith('.docx'):
        parser = DocxParser(file_path)
        student_id, student_name, answers = parser.parse(use_llm_extraction=True, api_key=api_key)
        content = "\n\n".join([f"Question {qid}:\n{answer}" for qid, answer in answers.items()])
        return content, student_id, student_name
    else:
        raise ValueError(f"Unsupported file type: {file_path}")


@app.route('/')
def index():
    """Render the main page."""
    # Check if API key is set via environment variable
    has_env_key = bool(os.getenv('OPENAI_API_KEY'))
    if not has_env_key:
        logger.warning("OPENAI_API_KEY not set in environment variables")
    return render_template('index.html', has_env_key=has_env_key)


@app.route('/grade', methods=['POST'])
def grade():
    """Handle file uploads and grading."""
    try:
        # Get files
        if 'base_file' not in request.files:
            return jsonify({'error': 'No base file provided'}), 400
        
        base_file = request.files['base_file']
        student_files = request.files.getlist('student_files')
        
        if base_file.filename == '':
            return jsonify({'error': 'Base file is empty'}), 400
        
        if not student_files or all(f.filename == '' for f in student_files):
            return jsonify({'error': 'No student files provided'}), 400
        
        # Save base file
        base_filename = secure_filename(base_file.filename)
        base_path = os.path.join(app.config['UPLOAD_FOLDER'], base_filename)
        base_file.save(base_path)
        
        # Initialize grader - only use environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'OPENAI_API_KEY environment variable not set. Please set it before running the app.'
            }), 400
        
        # Extract base solution
        logger.info(f"Extracting base solution from {base_filename}")
        base_content, _, _ = extract_text_and_info(base_path, api_key=api_key)
        
        grader = LLMGrader(api_key=api_key)
        
        # Grade each student file
        results = []
        for student_file in student_files:
            if student_file.filename == '':
                continue
            
            try:
                # Save student file
                student_filename = secure_filename(student_file.filename)
                student_path = os.path.join(app.config['UPLOAD_FOLDER'], student_filename)
                student_file.save(student_path)
                
                # Extract student submission and info (with LLM extraction)
                logger.info(f"Extracting student info and content from {student_filename}")
                student_content, student_id, student_name = extract_text_and_info(student_path, api_key=api_key)
                logger.info(f"Extracted: student_id={student_id}, student_name={student_name}")
                
                # Grade using LLM (include debug info)
                grade_result = grader.grade_simple(
                    base_content, 
                    student_content, 
                    student_filename,
                    student_id=student_id,
                    student_name=student_name,
                    include_debug=True
                )
                results.append(grade_result)
                
            except Exception as e:
                logger.error(f"Error grading {student_file.filename}: {e}")
                # Try to extract student info even if grading fails
                try:
                    _, student_id, student_name = extract_text_and_info(student_path)
                except:
                    student_id = 'Unknown'
                    student_name = 'Unknown'
                
                results.append({
                    'filename': student_filename,
                    'student_id': student_id,
                    'student_name': student_name,
                    'error': str(e)
                })
        
        return jsonify({'results': results})
    
    except Exception as e:
        logger.error(f"Error in grade endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4040)

