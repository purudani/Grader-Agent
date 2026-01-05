# Simple Assignment Grader

A simple web-based tool to grade student assignments using LLM. Upload a base solution file and student submissions, and get AI-powered grading results.

## Features

- **Simple Web UI**: Easy-to-use interface for file uploads
- **Multi-format Support**: Handles Jupyter notebooks (`.ipynb`) and Word documents (`.docx`)
- **LLM Grading**: Uses OpenAI GPT to compare student submissions against base solution
- **Batch Processing**: Grade multiple student files at once

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. **Set up OpenAI API Key** (REQUIRED):
   
   **Option 1: Environment Variable**
   ```bash
   export OPENAI_API_KEY="sk-..."
   python app.py
   ```
   
   **Option 2: .env file** (recommended)
   ```bash
   # Create a .env file in the Grader-Agent directory
   echo 'OPENAI_API_KEY=sk-your-key-here' > .env
   python app.py
   ```
   
   Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

2. **Run the app**:
   ```bash
   python app.py
   ```

3. **Open in browser**:
   Navigate to `http://localhost:4040`

4. **Upload files**:
   - Upload the base solution file (with correct answers)
   - Upload one or more student submission files
   - Click "Grade Assignments"

5. **View results**:
   - See scores out of 100 for each submission
   - Read feedback and deductions
   - Results are displayed immediately

## How It Works

1. Extracts text content from base solution file
2. Extracts text content from each student submission
3. Sends base solution + student submission to OpenAI GPT
4. LLM compares and grades, providing:
   - Score out of 100
   - Brief feedback
   - List of deductions (where marks were lost)
5. Displays results in the web UI

## File Formats

### Jupyter Notebooks (.ipynb)
- Extracts all markdown and code cells
- Looks for student info (NetID, Author) in markdown cells
- Identifies questions by patterns like "Question 1", "Problem 2.b"

### Word Documents (.docx)
- Extracts all paragraphs and table content
- Looks for student info and question markers
- Combines all text for grading

## API Key Setup

**Yes, you need an OpenAI API key** - this tool makes API calls to OpenAI's GPT models to grade assignments.

**Security Note:** The API key is now only accepted via environment variables (not through the UI) for better security.

### Setup Methods:

1. **Using .env file (Recommended)**:
   ```bash
   # Create .env file in the Grader-Agent directory
   echo 'OPENAI_API_KEY=sk-your-key-here' > .env
   python app.py
   ```

2. **Using Environment Variable**:
   ```bash
   export OPENAI_API_KEY="sk-..."
   python app.py
   ```

### Getting an API Key:
- Sign up at [OpenAI Platform](https://platform.openai.com)
- Go to [API Keys](https://platform.openai.com/api-keys)
- Create a new secret key
- Copy and use it (starts with `sk-`)

### Notes:
- API calls cost money based on OpenAI's pricing
- GPT-4o is used by default for better accuracy
- You can change the model in `grader_agent/grading/llm_grader.py` if needed
- The app will show an error if the API key is not set

## Notes

- Maximum file size: 50MB
- Files are temporarily stored during processing
- The app uses GPT-4o-mini by default (can be changed in code)
- All grading is done via LLM API calls
