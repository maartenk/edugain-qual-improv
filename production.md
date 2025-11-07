# Production Deployment Guide

This guide covers deploying the eduGAIN Quality Dashboard web application to a production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Architecture](#deployment-architecture)
3. [Deployment Options](#deployment-options)
4. [Recommended Production Setup](#recommended-production-setup)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Backup and Recovery](#backup-and-recovery)
8. [Scaling Considerations](#scaling-considerations)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 22.04 LTS or similar)
- **Python**: 3.12 or higher (tested on 3.12–3.14)
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 10GB+ for database and logs
- **Network**: Stable internet connection for metadata fetching

### Required Software

- Python 3.12+
- pip and virtualenv
- Nginx or Apache (for reverse proxy)
- systemd (for process management)
- Git (for deployment)
- Optional: Docker and Docker Compose

---

## Deployment Architecture

### Recommended Production Stack

```
Internet → Nginx (Reverse Proxy + SSL) → Uvicorn (ASGI Server) → FastAPI Application → SQLite Database
                                      ↓
                                  systemd (Process Management)
                                      ↓
                            Scheduled Data Import (cron/systemd timer)
```

### Components

1. **Web Server (Nginx)**: Handles SSL/TLS, static file serving, and reverse proxy
2. **ASGI Server (Uvicorn)**: Runs the FastAPI application
3. **Process Manager (systemd)**: Ensures the application stays running
4. **Database (SQLite)**: Stores analysis data and snapshots
5. **Scheduler (cron/systemd)**: Automates data imports

---

## Deployment Options

### Option 1: Traditional Linux Server Deployment (Recommended)

**Best for:** Full control, single-server deployment, cost-effective

**Pros:**
- Complete control over environment
- Easy to debug and maintain
- Cost-effective for small to medium workloads
- Direct access to logs and database

**Cons:**
- Manual server management required
- Single point of failure
- Manual scaling required

See [Recommended Production Setup](#recommended-production-setup) below.

---

### Option 2: Docker Deployment

**Best for:** Containerized environments, easy portability, development-production parity

**Pros:**
- Reproducible environment
- Easy to move between hosts
- Simplified dependency management
- Good for multi-service deployments

**Cons:**
- Slightly more complex setup
- Requires Docker knowledge
- Additional overhead

#### Docker Setup

1. **Create Dockerfile:**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -e .[web]

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "edugain_analysis_web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - ./cache:/root/.cache/edugain-analysis
    environment:
      - DATABASE_PATH=/data/edugain_analysis.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  scheduler:
    build: .
    volumes:
      - ./data:/data
      - ./cache:/root/.cache/edugain-analysis
    environment:
      - DATABASE_PATH=/data/edugain_analysis.db
    command: >
      sh -c "echo '0 6,18 * * * cd /app && python -m edugain_analysis_web.import_data --validate-urls >> /var/log/edugain_import.log 2>&1' | crontab - && crond -f"
    restart: unless-stopped

volumes:
  data:
  cache:
```

3. **Deploy:**

```bash
docker-compose up -d
```

---

### Option 3: Cloud Platform Deployment

#### AWS Elastic Beanstalk

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize EB application:
```bash
eb init -p python-3.12 edugain-dashboard
```

3. Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: edugain_analysis_web.app:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: /var/app/current
```

4. Deploy:
```bash
eb create edugain-prod
eb deploy
```

#### Google Cloud Run

1. Create `Dockerfile` (see Docker option above)

2. Build and deploy:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/edugain-dashboard
gcloud run deploy edugain-dashboard --image gcr.io/PROJECT_ID/edugain-dashboard --platform managed
```

#### Heroku

1. Create `Procfile`:
```
web: uvicorn edugain_analysis_web.app:app --host 0.0.0.0 --port $PORT
```

2. Deploy:
```bash
heroku create edugain-dashboard
git push heroku main
```

---

## Recommended Production Setup

This section provides step-by-step instructions for deploying to a traditional Linux server.

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.12 python3.12-venv python3-pip nginx git

# Create application user
sudo useradd -m -s /bin/bash edugain
sudo mkdir -p /opt/edugain-dashboard
sudo chown edugain:edugain /opt/edugain-dashboard
```

### 2. Application Installation

```bash
# Switch to application user
sudo su - edugain

# Clone repository
cd /opt/edugain-dashboard
git clone https://github.com/your-org/edugain-qual-improv.git .

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install application
pip install -e .[web]

# Create data directories
mkdir -p ~/.local/share/edugain-analysis
mkdir -p ~/.cache/edugain-analysis

# Initial data import
python -m edugain_analysis_web.import_data --validate-urls
```

### 3. Systemd Service Configuration

Create `/etc/systemd/system/edugain-dashboard.service`:

```ini
[Unit]
Description=eduGAIN Quality Dashboard
After=network.target

[Service]
Type=notify
User=edugain
Group=edugain
WorkingDirectory=/opt/edugain-dashboard
Environment="PATH=/opt/edugain-dashboard/.venv/bin"
ExecStart=/opt/edugain-dashboard/.venv/bin/uvicorn edugain_analysis_web.app:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log

# Restart policy
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/edugain/.local/share/edugain-analysis /home/edugain/.cache/edugain-analysis

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable edugain-dashboard
sudo systemctl start edugain-dashboard
sudo systemctl status edugain-dashboard
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/edugain-dashboard`:

```nginx
upstream edugain_backend {
    server 127.0.0.1:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name edugain.example.com;

    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name edugain.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/edugain.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/edugain.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/edugain-dashboard-access.log;
    error_log /var/log/nginx/edugain-dashboard-error.log;

    # Static files
    location /static {
        alias /opt/edugain-dashboard/src/edugain_analysis/web/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to FastAPI
    location / {
        proxy_pass http://edugain_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for future enhancements)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting for API endpoints
    location /api/database/ {
        limit_req zone=api_limit burst=5;
        proxy_pass http://edugain_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Rate limit configuration
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/h;
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/edugain-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL/TLS Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d edugain.example.com

# Auto-renewal is configured automatically
sudo systemctl status certbot.timer
```

### 6. Automated Data Import

Create systemd timer for automated data import.

Create `/etc/systemd/system/edugain-import.service`:

```ini
[Unit]
Description=eduGAIN Data Import
After=network.target

[Service]
Type=oneshot
User=edugain
Group=edugain
WorkingDirectory=/opt/edugain-dashboard
Environment="PATH=/opt/edugain-dashboard/.venv/bin"
ExecStart=/opt/edugain-dashboard/.venv/bin/python -m edugain_analysis_web.import_data --validate-urls
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/edugain-import.timer`:

```ini
[Unit]
Description=Run eduGAIN import twice daily

[Timer]
OnCalendar=*-*-* 06,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:

```bash
sudo systemctl enable edugain-import.timer
sudo systemctl start edugain-import.timer
sudo systemctl list-timers
```

---

## Security Considerations

### 1. Application Security

- **Environment Variables**: Store sensitive configuration in environment variables, not code
- **Database Encryption**: Consider SQLCipher for database encryption at rest
- **HTTPS Only**: Enforce HTTPS for all connections
- **Rate Limiting**: Implement rate limits on API endpoints (configured in Nginx)
- **Input Validation**: Validate all user inputs (already implemented in FastAPI)

### 2. Server Hardening

```bash
# Enable firewall
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Install fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
```

### 3. Regular Updates

```bash
# Automated security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Monitoring and Maintenance

### 1. Application Monitoring

**Log Locations:**
- Application logs: `journalctl -u edugain-dashboard -f`
- Nginx access logs: `/var/log/nginx/edugain-dashboard-access.log`
- Nginx error logs: `/var/log/nginx/edugain-dashboard-error.log`
- Import logs: `journalctl -u edugain-import -f`

**Health Check:**
```bash
curl https://edugain.example.com/health
```

### 2. Performance Monitoring

Install and configure monitoring tools:

```bash
# Install htop for process monitoring
sudo apt install -y htop

# Install logrotate for log management
sudo apt install -y logrotate
```

Create `/etc/logrotate.d/edugain-dashboard`:

```
/var/log/nginx/edugain-dashboard-*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1
    endscript
}
```

### 3. Database Maintenance

```bash
# Vacuum database monthly
sqlite3 ~/.local/share/edugain-analysis/edugain_analysis.db "VACUUM;"

# Check database integrity
sqlite3 ~/.local/share/edugain-analysis/edugain_analysis.db "PRAGMA integrity_check;"
```

---

## Backup and Recovery

### 1. Automated Backups

Create backup script `/opt/edugain-dashboard/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/edugain"
DB_PATH="/home/edugain/.local/share/edugain-analysis/edugain_analysis.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/edugain_backup_$TIMESTAMP.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Compress backup
gzip "$BACKUP_FILE"

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "edugain_backup_*.db.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

Make executable and schedule:

```bash
chmod +x /opt/edugain-dashboard/backup.sh

# Add to crontab (daily at 3 AM)
echo "0 3 * * * /opt/edugain-dashboard/backup.sh >> /var/log/edugain-backup.log 2>&1" | sudo crontab -u edugain -
```

### 2. Recovery Procedure

```bash
# Stop application
sudo systemctl stop edugain-dashboard

# Restore from backup
cd /home/edugain/.local/share/edugain-analysis
mv edugain_analysis.db edugain_analysis.db.old
gunzip -c /var/backups/edugain/edugain_backup_TIMESTAMP.db.gz > edugain_analysis.db

# Restart application
sudo systemctl start edugain-dashboard
```

### 3. Remote Backups

Consider backing up to remote storage:

```bash
# Using rclone to sync to cloud storage
rclone sync /var/backups/edugain remote:edugain-backups
```

---

## Scaling Considerations

### Vertical Scaling

1. **Increase workers**: Adjust `--workers` in systemd service (rule of thumb: 2-4 × CPU cores)
2. **Upgrade server**: More RAM and CPU for larger datasets
3. **Database optimization**: Add indexes, vacuum regularly

### Horizontal Scaling

For high-traffic scenarios:

1. **Load Balancer**: Use HAProxy or cloud load balancer
2. **Multiple App Servers**: Run multiple Uvicorn instances behind load balancer
3. **Shared Database**: Use network-accessible database (PostgreSQL recommended)
4. **Cache Layer**: Add Redis for session management and caching
5. **CDN**: Use CloudFlare or AWS CloudFront for static assets

Example multi-server architecture:

```
Internet → Load Balancer → [App Server 1, App Server 2, App Server 3]
                                        ↓
                                 Shared PostgreSQL Database
                                        ↓
                                   Redis Cache
```

### Database Migration (SQLite → PostgreSQL)

For production at scale, consider PostgreSQL:

1. Install PostgreSQL
2. Update `models.py` to use PostgreSQL connection string
3. Migrate data using SQLAlchemy's migration tools
4. Update connection pooling settings

---

## Troubleshooting

### Common Issues

1. **Application won't start:**
   ```bash
   journalctl -u edugain-dashboard -n 50
   ```

2. **Database locked errors:**
   - Check for multiple processes accessing database
   - Ensure proper file permissions
   - Consider migrating to PostgreSQL for concurrent access

3. **High memory usage:**
   - Reduce Uvicorn workers
   - Optimize database queries
   - Clear old snapshots from database

4. **Slow performance:**
   - Enable gzip compression in Nginx
   - Add database indexes
   - Use CDN for static files
   - Enable browser caching

---

## Production Checklist

Before going live:

- [ ] SSL/TLS certificate installed and auto-renewal configured
- [ ] Firewall configured and enabled
- [ ] Automated backups configured
- [ ] Monitoring and alerting configured
- [ ] Log rotation configured
- [ ] Security headers enabled in Nginx
- [ ] Rate limiting configured
- [ ] Health check endpoint verified
- [ ] Automated data import scheduled
- [ ] Documentation updated with server details
- [ ] Emergency contact procedures documented
- [ ] Disaster recovery plan tested

---

## Support and Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor application logs for errors
- Check health endpoint

**Weekly:**
- Review access logs for anomalies
- Check disk space usage

**Monthly:**
- Update system packages
- Review and optimize database
- Test backup restoration
- Review security headers and SSL configuration

**Quarterly:**
- Security audit
- Performance review
- Update dependencies

---

## Additional Resources

- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Uvicorn Deployment**: https://www.uvicorn.org/deployment/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **systemd Documentation**: https://systemd.io/

---

## License

This deployment guide is part of the eduGAIN Quality Improvement project.
