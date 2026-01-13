# Grader-Agent Deployment Guide

Deploy the Grader-Agent app to the same server as teaching-resources-api, accessible at `contextgai.com/grader-gpt`.

## Current Server Setup

- **Backend API**: `teaching-resources-api` on port `8000` → `contextgai.com/api/*`
- **Frontend**: `storylaunch-hub` (static files) → `contextgai.com/`
- **New App**: `Grader-Agent` on port `4040` → `contextgai.com/grader-gpt/`

## Port Conflict Analysis

✅ **No conflicts:**
- Port 80/443: Nginx (listening for all requests)
- Port 8000: teaching-resources-api (backend)
- Port 4040: Grader-Agent (new app) ✅ Available

## Deployment Steps

### Step 1: Upload Code to Server

```bash
# On your local machine
cd Grader-Agent
git add .
git commit -m "Ready for deployment"
git push

# On server
ssh -i contextgai_azure.pem contextgai@contextgai.com
cd ~/App
git clone <your-repo-url> Grader-Agent
# Or if already exists:
cd Grader-Agent && git pull
```

### Step 2: Set Up Virtual Environment

```bash
cd ~/App/Grader-Agent
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
cd ~/App/Grader-Agent
nano .env
```

Add your Azure OpenAI credentials:
```bash
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-12-01-preview
FLASK_DEBUG=False
```

### Step 4: Create Systemd Service

```bash
sudo nano /etc/systemd/system/grader-agent.service
```

Copy the content from `grader-agent.service` file, or use:

```ini
[Unit]
Description=Grader Agent Flask App
After=network.target

[Service]
Type=simple
User=contextgai
WorkingDirectory=/home/contextgai/App/Grader-Agent
Environment="PATH=/home/contextgai/App/Grader-Agent/venv/bin"
EnvironmentFile=/home/contextgai/App/Grader-Agent/.env
ExecStart=/home/contextgai/App/Grader-Agent/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 5: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable grader-agent

# Start service
sudo systemctl start grader-agent

# Check status
sudo systemctl status grader-agent
```

### Step 6: Update Nginx Configuration

**IMPORTANT**: Your current nginx config handles:
- `/api/*` → Backend (port 8000)
- `/` → Frontend (static files)

We need to add `/grader-gpt/` → Grader-Agent (port 4040)

```bash
sudo nano /etc/nginx/sites-available/contextgai
# Or wherever your main nginx config is
```

**Add this location block BEFORE the frontend `/` location:**

```nginx
server {
    listen 443 ssl http2;
    server_name contextgai.com;

    # SSL certificates (existing)
    ssl_certificate /etc/letsencrypt/live/contextgai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/contextgai.com/privkey.pem;

    # Backend API routes (existing - MUST stay first)
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Grader Agent - NEW (add this)
    location /grader-gpt/ {
        proxy_pass http://127.0.0.1:4040/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for file uploads
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        
        # Increase body size for large file uploads
        client_max_body_size 50M;
    }

    # Handle /grader-gpt without trailing slash
    location = /grader-gpt {
        return 301 /grader-gpt/;
    }

    # Frontend static files (existing - MUST stay last)
    root /home/contextgai/App/storylaunch-hub/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # ... rest of your config (SSL, caching, etc.)
}
```

**Critical Order:**
1. `/api` - Backend API (first)
2. `/grader-gpt/` - Grader app (second)
3. `/` - Frontend (last)

### Step 7: Test and Reload Nginx

```bash
# Test configuration
sudo nginx -t

# If successful, reload
sudo systemctl reload nginx
```

### Step 8: Verify Everything Works

```bash
# Check all services are running
sudo systemctl status teaching-resources-api
sudo systemctl status grader-agent
sudo systemctl status nginx

# Check ports are in use
sudo netstat -tlnp | grep -E '8000|4040|80|443'

# Test endpoints locally
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:4040/
```

### Step 9: Test URLs

- ✅ Frontend: `https://contextgai.com/`
- ✅ Backend API: `https://contextgai.com/api/health`
- ✅ Grader App: `https://contextgai.com/grader-gpt/`

## Complete Nginx Configuration Example

Here's a complete example combining all three services:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name contextgai.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name contextgai.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/contextgai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/contextgai.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 1. Backend API - MUST be first
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 2. Grader Agent - Second
    location /grader-gpt/ {
        proxy_pass http://127.0.0.1:4040/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 50M;
    }

    location = /grader-gpt {
        return 301 /grader-gpt/;
    }

    # 3. Frontend - MUST be last
    root /home/contextgai/App/storylaunch-hub/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u grader-agent -n 50 -f

# Check if port is in use
sudo lsof -i :4040
```

### Nginx 502 Bad Gateway
- Check Flask app: `sudo systemctl status grader-agent`
- Check logs: `sudo journalctl -u grader-agent -f`
- Test locally: `curl http://127.0.0.1:4040`

### Route not working
- Check nginx error log: `sudo tail -f /var/log/nginx/error.log`
- Verify location order in nginx config
- Test nginx config: `sudo nginx -t`

### Port conflicts
```bash
# Check what's using each port
sudo lsof -i :8000  # Backend
sudo lsof -i :4040  # Grader
sudo lsof -i :80    # Nginx HTTP
sudo lsof -i :443   # Nginx HTTPS
```

## Quick Update Script

Use the provided `deploy.sh` script:

```bash
cd ~/App/Grader-Agent
./deploy.sh
```

Or manually:
```bash
cd ~/App/Grader-Agent
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart grader-agent
```

## Summary

✅ **Port 4040**: Grader-Agent (no conflicts)  
✅ **Route `/grader-gpt/`**: Added to nginx  
✅ **Systemd service**: Created and enabled  
✅ **All services**: Can run simultaneously  

Your server will now serve:
- `contextgai.com/` → Frontend
- `contextgai.com/api/*` → Backend API
- `contextgai.com/grader-gpt/` → Grader App
