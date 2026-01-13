#!/bin/bash
# Quick deployment script for Grader-Agent

echo "🚀 Deploying Grader-Agent..."

# Navigate to app directory
cd ~/App/Grader-Agent || exit 1

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart grader-agent

# Check status
echo "✅ Checking service status..."
sudo systemctl status grader-agent --no-pager

echo "✨ Deployment complete!"
echo "🌐 App should be available at: http://contextgai.com/grader-gpt"
