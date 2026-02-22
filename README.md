# Simple Assignment Grader

Grade student assignments using Azure OpenAI.

## Setup

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create .env file with your Azure OpenAI credentials:**
   ```bash
   AZURE_OPENAI_API_KEY=your-key-here
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
   AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
   AZURE_OPENAI_API_VERSION=2024-12-01-preview
   ```

   **Important:** 
   - The `AZURE_OPENAI_DEPLOYMENT_NAME` must match exactly the deployment name in Azure Portal
   - The `AZURE_OPENAI_ENDPOINT` should NOT have a trailing slash
   - To find your deployment name: Azure Portal → Your Resource → Model deployments

4. **Run:**
   ```bash
   python app.py
   ```

5. **Open:** http://localhost:4040

## Finding Your Deployment Name

1. Go to Azure Portal
2. Navigate to your Azure OpenAI resource
3. Click on "Model deployments" or "Deployments"
4. Copy the exact deployment name (e.g., "gpt-4", "gpt-4o", "gpt-35-turbo")
5. Use that exact name in your `.env` file

## Usage

1. Upload base solution file (supports notebooks, Word, PDF, PPTX, XLSX, and common text/code formats)
2. Upload student submission files (same format support)
3. Click "Grade"
4. View results with scores and feedback
