# Production Deployment Guide

## 🚀 Overview

This guide covers deploying the Diabetes Diet Manager application to production environments with best practices for security, performance, and reliability.

## 📋 Prerequisites

### Backend Requirements
- **Python 3.8+**
- **Azure Cosmos DB** instance
- **Azure OpenAI** service
- **SSL Certificate** for HTTPS
- **Domain name** (recommended)

### Frontend Requirements
- **Node.js 16+**
- **Web server** (Nginx, Apache, or CDN)
- **SSL Certificate** for HTTPS

## 🔧 Backend Deployment

### 1. Environment Setup

Create a production `.env` file:

```env
# Production Environment
NODE_ENV=production

# Azure Cosmos DB
COSMO_DB_CONNECTION_STRING=your_production_cosmos_connection_string
INTERACTIONS_CONTAINER=interactions
USER_INFORMATION_CONTAINER=user_information

# Azure OpenAI
AZURE_OPENAI_KEY=your_production_openai_key
AZURE_OPENAI_ENDPOINT=your_production_openai_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_production_deployment_name

# JWT Authentication (Use a strong, unique secret)
SECRET_KEY=your_super_secure_jwt_secret_key_for_production

# CORS Settings
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Twilio (Optional)
SMS_API_SID=your_production_twilio_sid
SMS_KEY=your_production_twilio_auth_token
TWILIO_PHONE_NUMBER=your_production_twilio_phone_number

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/diabetes-app/app.log

# Security
SECURE_COOKIES=true
HTTPS_ONLY=true
```

### 2. Docker Deployment (Recommended)

Create `Dockerfile` for backend:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 3. Production Server Configuration

#### Using Gunicorn + Nginx

Install Gunicorn:
```bash
pip install gunicorn
```

Create `gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

Create systemd service `/etc/systemd/system/diabetes-app.service`:
```ini
[Unit]
Description=Diabetes Diet Manager API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/diabetes-app/backend
Environment=PATH=/var/www/diabetes-app/backend/venv/bin
ExecStart=/var/www/diabetes-app/backend/venv/bin/gunicorn -c gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration

Create `/etc/nginx/sites-available/diabetes-app`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Frontend
    location / {
        root /var/www/diabetes-app/frontend/build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 🎨 Frontend Deployment

### 1. Environment Configuration

Create `.env.production`:
```env
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

### 2. Build for Production

```bash
cd frontend
npm ci --only=production
npm run build
```

### 3. Deploy to CDN (Recommended)

#### Using AWS CloudFront + S3

1. **Create S3 Bucket**:
```bash
aws s3 mb s3://diabetes-app-frontend
aws s3 sync build/ s3://diabetes-app-frontend --delete
```

2. **Configure CloudFront**:
```json
{
  "Origins": [{
    "DomainName": "diabetes-app-frontend.s3.amazonaws.com",
    "Id": "S3-diabetes-app-frontend",
    "S3OriginConfig": {
      "OriginAccessIdentity": ""
    }
  }],
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-diabetes-app-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "Compress": true,
    "CachePolicyId": "managed-caching-optimized"
  },
  "CustomErrorResponses": [{
    "ErrorCode": 404,
    "ResponseCode": 200,
    "ResponsePagePath": "/index.html"
  }]
}
```

## 🔒 Security Checklist

### Backend Security
- [ ] Use HTTPS only
- [ ] Implement rate limiting
- [ ] Validate all inputs
- [ ] Use secure JWT secrets
- [ ] Enable CORS properly
- [ ] Implement request logging
- [ ] Use environment variables for secrets
- [ ] Regular security updates

### Frontend Security
- [ ] Use HTTPS only
- [ ] Implement CSP headers
- [ ] Sanitize user inputs
- [ ] Secure token storage
- [ ] Regular dependency updates
- [ ] Remove development tools

## 📊 Monitoring & Logging

### Application Monitoring

1. **Health Check Endpoint**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }
```

2. **Logging Configuration**:
```python
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        RotatingFileHandler('/var/log/diabetes-app/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Performance Monitoring

- **Application Performance Monitoring (APM)**
- **Database query monitoring**
- **API response time tracking**
- **Error rate monitoring**
- **Resource usage monitoring**

## 🚀 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          cd backend && python -m pytest
          cd frontend && npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy Backend
        run: |
          # Deploy backend to your server
          
      - name: Deploy Frontend
        run: |
          cd frontend
          npm ci
          npm run build
          aws s3 sync build/ s3://your-bucket --delete
```

## 🔧 Performance Optimization

### Backend Optimizations
- Use connection pooling
- Implement caching (Redis)
- Optimize database queries
- Use async/await properly
- Implement request compression

### Frontend Optimizations
- Code splitting
- Lazy loading
- Image optimization
- Bundle analysis
- Service worker caching

## 📱 Mobile Considerations

- Responsive design testing
- Touch-friendly interfaces
- Offline functionality
- Progressive Web App (PWA) features
- Performance on mobile networks

## 🆘 Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Check ALLOWED_ORIGINS configuration
   - Verify frontend URL matches

2. **Authentication Issues**:
   - Check JWT secret configuration
   - Verify token expiration settings

3. **Database Connection**:
   - Verify Cosmos DB connection string
   - Check network connectivity

4. **Performance Issues**:
   - Monitor resource usage
   - Check database query performance
   - Analyze API response times

## 📞 Support

For production support:
- Monitor application logs
- Set up alerting for critical errors
- Maintain backup and recovery procedures
- Document incident response procedures 