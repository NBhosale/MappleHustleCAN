# 🚀 MapleHustleCAN Production Deployment Guide

This comprehensive guide will walk you through deploying the MapleHustleCAN application to production with enterprise-grade security, monitoring, and scalability.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Application Deployment](#application-deployment)
6. [Security Configuration](#security-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [SSL/TLS Setup](#ssltls-setup)
9. [Load Balancing](#load-balancing)
10. [Backup & Recovery](#backup--recovery)
11. [Maintenance & Updates](#maintenance--updates)
12. [Troubleshooting](#troubleshooting)
13. [Performance Optimization](#performance-optimization)

---

## 🔧 Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04 LTS or later (recommended)
- **CPU**: 4+ cores (8+ cores for high-traffic)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB+ SSD storage
- **Network**: Stable internet connection with static IP

### Software Dependencies

- **Python**: 3.11+ (3.13 recommended)
- **PostgreSQL**: 15+ with PostGIS extension
- **Redis**: 7.0+
- **Nginx**: 1.20+
- **Docker**: 24.0+ (optional, for containerized deployment)
- **Certbot**: For SSL certificates

### Domain & DNS

- Domain name registered
- DNS records configured
- SSL certificate (Let's Encrypt recommended)

---

## 🏗️ Infrastructure Setup

### 1. Server Provisioning

#### Option A: Cloud Provider (Recommended)

**AWS EC2:**
```bash
# Launch Ubuntu 22.04 LTS instance
# Instance type: t3.large or larger
# Security groups: HTTP (80), HTTPS (443), SSH (22), PostgreSQL (5432), Redis (6379)
```

**DigitalOcean Droplet:**
```bash
# Create droplet with Ubuntu 22.04 LTS
# Size: 4GB RAM, 2 vCPUs minimum
# Add monitoring and backups
```

**Google Cloud Platform:**
```bash
# Create Compute Engine instance
# Machine type: e2-standard-2 or larger
# Enable HTTP/HTTPS traffic
```

#### Option B: VPS/Dedicated Server

```bash
# Ensure server meets minimum requirements
# Configure firewall rules
# Set up monitoring
```

### 2. Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git vim htop unzip software-properties-common

# Create application user
sudo adduser --system --group --home /opt/maplehustlecan maplehustlecan
sudo usermod -aG sudo maplehustlecan

# Switch to application user
sudo su - maplehustlecan
```

### 3. Install Required Software

#### Install Python 3.13

```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.13
sudo apt install -y python3.13 python3.13-venv python3.13-dev python3-pip

# Verify installation
python3.13 --version
```

#### Install PostgreSQL 15

```bash
# Add PostgreSQL repository
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql-15 postgresql-client-15 postgresql-15-postgis-3

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
sudo -u postgres psql -c "SELECT version();"
```

#### Install Redis 7

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis
sudo vim /etc/redis/redis.conf

# Set the following configurations:
# maxmemory 2gb
# maxmemory-policy allkeys-lru
# save 900 1
# save 300 10
# save 60 10000

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify installation
redis-cli ping
```

#### Install Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Verify installation
sudo nginx -t
```

---

## ⚙️ Environment Configuration

### 1. Create Application Directory

```bash
# Create application directory
sudo mkdir -p /opt/maplehustlecan
sudo chown maplehustlecan:maplehustlecan /opt/maplehustlecan
cd /opt/maplehustlecan

# Clone repository
git clone https://github.com/NBhosale/MappleHustleCAN.git .
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Create production environment file:

```bash
# Create environment file
sudo vim /opt/maplehustlecan/.env.production
```

Add the following configuration:

```env
# Application Configuration
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here-minimum-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-here-minimum-32-characters

# Database Configuration
DATABASE_URL=postgresql+psycopg2://maplehustlecan:your-db-password@localhost:5432/maplehustlecan_prod

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security Configuration
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# SSL Configuration
HTTPS_ONLY=true
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true

# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# File Storage Configuration
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=maplehustlecan-files
AWS_S3_REGION=us-east-1

# Monitoring Configuration
SENTRY_DSN=your-sentry-dsn-here
SECURITY_MONITORING_ENABLED=true
PERFORMANCE_MONITORING_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL=3600

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/maplehustlecan/app.log
```

### 4. Set File Permissions

```bash
# Set proper permissions
sudo chown -R maplehustlecan:maplehustlecan /opt/maplehustlecan
sudo chmod 600 /opt/maplehustlecan/.env.production

# Create log directory
sudo mkdir -p /var/log/maplehustlecan
sudo chown maplehustlecan:maplehustlecan /var/log/maplehustlecan
```

---

## 🗄️ Database Setup

### 1. Create Production Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE maplehustlecan_prod;
CREATE USER maplehustlecan WITH PASSWORD 'your-secure-db-password';
GRANT ALL PRIVILEGES ON DATABASE maplehustlecan_prod TO maplehustlecan;

# Enable PostGIS extension
\c maplehustlecan_prod
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Exit psql
\q
```

### 2. Run Database Migrations

```bash
# Activate virtual environment
cd /opt/maplehustlecan
source venv/bin/activate

# Set environment variables
export ENVIRONMENT=production
export DATABASE_URL=postgresql+psycopg2://maplehustlecan:your-db-password@localhost:5432/maplehustlecan_prod

# Run migrations
alembic upgrade head

# Verify database setup
python -c "
from app.db.session import get_engine
from sqlalchemy import text
engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text('SELECT version();'))
    print('Database connected successfully:', result.fetchone()[0])
"
```

### 3. Create Database Indexes

```bash
# Run database optimization script
python scripts/optimize_database.py
```

---

## 🚀 Application Deployment

### 1. Create Systemd Service

Create a systemd service file:

```bash
sudo vim /etc/systemd/system/maplehustlecan.service
```

Add the following configuration:

```ini
[Unit]
Description=MapleHustleCAN FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=maplehustlecan
Group=maplehustlecan
WorkingDirectory=/opt/maplehustlecan
Environment=PATH=/opt/maplehustlecan/venv/bin
EnvironmentFile=/opt/maplehustlecan/.env.production
ExecStart=/opt/maplehustlecan/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Start Application Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable maplehustlecan

# Start service
sudo systemctl start maplehustlecan

# Check status
sudo systemctl status maplehustlecan

# View logs
sudo journalctl -u maplehustlecan -f
```

### 3. Configure Nginx

Create Nginx configuration:

```bash
sudo vim /etc/nginx/sites-available/maplehustlecan
```

Add the following configuration:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

# Upstream configuration
upstream maplehustlecan_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Main server block
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';" always;
    
    # Rate limiting
    limit_req zone=api burst=20 nodelay;
    
    # Client settings
    client_max_body_size 10M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # API routes
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://maplehustlecan_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Auth routes with stricter rate limiting
    location /auth/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://maplehustlecan_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://maplehustlecan_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Security dashboard (admin only)
    location /security/ {
        # Add IP whitelist here if needed
        proxy_pass http://maplehustlecan_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/maplehustlecan/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Root redirect to API docs
    location / {
        return 301 https://$server_name/docs;
    }
}

# HTTPS server block (will be configured after SSL setup)
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration will be added here
    # (See SSL/TLS Setup section)
}
```

### 4. Enable Nginx Configuration

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/maplehustlecan /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## 🔒 Security Configuration

### 1. Firewall Setup

```bash
# Install UFW
sudo apt install -y ufw

# Configure firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow PostgreSQL (only from localhost)
sudo ufw allow from 127.0.0.1 to any port 5432

# Allow Redis (only from localhost)
sudo ufw allow from 127.0.0.1 to any port 6379

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 2. Fail2Ban Setup

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create configuration
sudo vim /etc/fail2ban/jail.local
```

Add the following configuration:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
```

```bash
# Start Fail2Ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Check status
sudo fail2ban-client status
```

### 3. Security Hardening

```bash
# Disable root login
sudo vim /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Restart SSH
sudo systemctl restart ssh

# Install security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure automatic security updates
sudo vim /etc/apt/apt.conf.d/50unattended-upgrades
```

---

## 📊 Monitoring & Logging

### 1. Set Up Log Rotation

```bash
sudo vim /etc/logrotate.d/maplehustlecan
```

Add the following configuration:

```
/var/log/maplehustlecan/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 maplehustlecan maplehustlecan
    postrotate
        systemctl reload maplehustlecan
    endscript
}
```

### 2. Set Up Monitoring

#### Option A: Prometheus + Grafana

```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus
sudo chown -R maplehustlecan:maplehustlecan /opt/prometheus

# Install Grafana
wget https://dl.grafana.com/oss/release/grafana-10.0.0.linux-amd64.tar.gz
tar xvfz grafana-10.0.0.linux-amd64.tar.gz
sudo mv grafana-10.0.0 /opt/grafana
sudo chown -R maplehustlecan:maplehustlecan /opt/grafana
```

#### Option B: Simple Monitoring Script

```bash
# Create monitoring script
sudo vim /opt/maplehustlecan/scripts/monitor.sh
```

```bash
#!/bin/bash

# Health check script
APP_URL="http://localhost:8000/health"
LOG_FILE="/var/log/maplehustlecan/monitor.log"

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL)
    if [ $response -eq 200 ]; then
        echo "$(date): Application is healthy" >> $LOG_FILE
    else
        echo "$(date): Application is unhealthy (HTTP $response)" >> $LOG_FILE
        # Restart service
        systemctl restart maplehustlecan
    fi
}

check_health
```

```bash
# Make executable
sudo chmod +x /opt/maplehustlecan/scripts/monitor.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/maplehustlecan/scripts/monitor.sh") | crontab -
```

### 3. Set Up Sentry (Error Tracking)

```bash
# Install Sentry SDK
pip install sentry-sdk[fastapi]

# Configure Sentry in your application
# (Already configured in app/core/error_tracking.py)
```

---

## 🔐 SSL/TLS Setup

### 1. Install Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run

# Set up automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 2. Update Nginx Configuration for HTTPS

The SSL configuration will be automatically added by Certbot. Verify the configuration:

```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## ⚖️ Load Balancing

### 1. Multiple Application Instances

```bash
# Create additional systemd services for load balancing
sudo cp /etc/systemd/system/maplehustlecan.service /etc/systemd/system/maplehustlecan-2.service
sudo cp /etc/systemd/system/maplehustlecan.service /etc/systemd/system/maplehustlecan-3.service

# Modify ports in additional services
sudo vim /etc/systemd/system/maplehustlecan-2.service
# Change port to 8001

sudo vim /etc/systemd/system/maplehustlecan-3.service
# Change port to 8002

# Update Nginx upstream configuration
sudo vim /etc/nginx/sites-available/maplehustlecan
```

Update upstream configuration:

```nginx
upstream maplehustlecan_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    keepalive 32;
}
```

### 2. Start Additional Instances

```bash
# Start additional instances
sudo systemctl start maplehustlecan-2
sudo systemctl start maplehustlecan-3

# Enable them
sudo systemctl enable maplehustlecan-2
sudo systemctl enable maplehustlecan-3

# Reload Nginx
sudo systemctl reload nginx
```

---

## 💾 Backup & Recovery

### 1. Database Backup

```bash
# Create backup script
sudo vim /opt/maplehustlecan/scripts/backup_db.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/opt/maplehustlecan/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="maplehustlecan_prod"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U maplehustlecan -d $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: db_backup_$DATE.sql.gz"
```

```bash
# Make executable
sudo chmod +x /opt/maplehustlecan/scripts/backup_db.sh

# Add to crontab (daily backup at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/maplehustlecan/scripts/backup_db.sh") | crontab -
```

### 2. Application Backup

```bash
# Create application backup script
sudo vim /opt/maplehustlecan/scripts/backup_app.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/opt/maplehustlecan/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/maplehustlecan"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create application backup (excluding venv and logs)
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=logs \
    -C $APP_DIR .

# Remove backups older than 30 days
find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +30 -delete

echo "Application backup completed: app_backup_$DATE.tar.gz"
```

### 3. Recovery Procedures

#### Database Recovery

```bash
# Stop application
sudo systemctl stop maplehustlecan

# Restore database
gunzip -c /opt/maplehustlecan/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -U maplehustlecan -d maplehustlecan_prod

# Start application
sudo systemctl start maplehustlecan
```

#### Application Recovery

```bash
# Stop application
sudo systemctl stop maplehustlecan

# Restore application
cd /opt/maplehustlecan
tar -xzf /opt/maplehustlecan/backups/app_backup_YYYYMMDD_HHMMSS.tar.gz

# Recreate virtual environment
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start application
sudo systemctl start maplehustlecan
```

---

## 🔧 Maintenance & Updates

### 1. Application Updates

```bash
# Create update script
sudo vim /opt/maplehustlecan/scripts/update.sh
```

```bash
#!/bin/bash

APP_DIR="/opt/maplehustlecan"
BACKUP_DIR="/opt/maplehustlecan/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting application update..."

# Create backup before update
$APP_DIR/scripts/backup_app.sh
$APP_DIR/scripts/backup_db.sh

# Stop application
sudo systemctl stop maplehustlecan

# Navigate to application directory
cd $APP_DIR

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run security audit
python scripts/security_audit.py

# Start application
sudo systemctl start maplehustlecan

# Check application health
sleep 10
curl -f http://localhost:8000/health || {
    echo "Application health check failed. Rolling back..."
    # Rollback procedure would go here
    exit 1
}

echo "Application update completed successfully"
```

### 2. Security Updates

```bash
# Create security update script
sudo vim /opt/maplehustlecan/scripts/security_update.sh
```

```bash
#!/bin/bash

echo "Starting security updates..."

# Update system packages
sudo apt update
sudo apt upgrade -y

# Update Python packages
cd /opt/maplehustlecan
source venv/bin/activate
pip list --outdated
pip install --upgrade pip
pip install -r requirements.txt

# Run security audit
python scripts/security_audit.py

# Run security tests
python scripts/security_testing.py

echo "Security updates completed"
```

### 3. Log Management

```bash
# Create log cleanup script
sudo vim /opt/maplehustlecan/scripts/cleanup_logs.sh
```

```bash
#!/bin/bash

LOG_DIR="/var/log/maplehustlecan"
DAYS_TO_KEEP=30

# Clean up old logs
find $LOG_DIR -name "*.log" -mtime +$DAYS_TO_KEEP -delete

# Compress old logs
find $LOG_DIR -name "*.log" -mtime +7 -exec gzip {} \;

echo "Log cleanup completed"
```

---

## 🐛 Troubleshooting

### 1. Common Issues

#### Application Won't Start

```bash
# Check service status
sudo systemctl status maplehustlecan

# Check logs
sudo journalctl -u maplehustlecan -f

# Check application logs
tail -f /var/log/maplehustlecan/app.log

# Test database connection
python -c "
from app.db.session import get_engine
engine = get_engine()
with engine.connect() as conn:
    print('Database connection successful')
"
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Test database connection
psql -h localhost -U maplehustlecan -d maplehustlecan_prod -c "SELECT 1;"
```

#### Redis Connection Issues

```bash
# Check Redis status
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

#### Nginx Issues

```bash
# Check Nginx status
sudo systemctl status nginx

# Test Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### 2. Performance Issues

#### High Memory Usage

```bash
# Check memory usage
free -h
htop

# Check application memory usage
ps aux | grep uvicorn

# Check Redis memory usage
redis-cli info memory
```

#### High CPU Usage

```bash
# Check CPU usage
top
htop

# Check application processes
ps aux | grep uvicorn

# Check system load
uptime
```

#### Database Performance

```bash
# Check database connections
psql -h localhost -U maplehustlecan -d maplehustlecan_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
psql -h localhost -U maplehustlecan -d maplehustlecan_prod -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### 3. Security Issues

#### Check Security Status

```bash
# Run security audit
cd /opt/maplehustlecan
source venv/bin/activate
python scripts/security_audit.py

# Run security tests
python scripts/security_testing.py

# Check firewall status
sudo ufw status

# Check Fail2Ban status
sudo fail2ban-client status
```

#### Monitor Security Events

```bash
# Check security logs
tail -f /var/log/maplehustlecan/security.log

# Check failed login attempts
sudo grep "Failed password" /var/log/auth.log

# Check Nginx access logs for suspicious activity
sudo tail -f /var/log/nginx/access.log | grep -E "(40[0-9]|50[0-9])"
```

---

## ⚡ Performance Optimization

### 1. Database Optimization

```bash
# Run database optimization
cd /opt/maplehustlecan
source venv/bin/activate
python scripts/optimize_database.py

# Check database performance
psql -h localhost -U maplehustlecan -d maplehustlecan_prod -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;
"
```

### 2. Redis Optimization

```bash
# Check Redis memory usage
redis-cli info memory

# Check Redis performance
redis-cli --latency

# Optimize Redis configuration
sudo vim /etc/redis/redis.conf
```

### 3. Application Optimization

```bash
# Check application performance
curl -s http://localhost:8000/performance/metrics | jq

# Monitor application metrics
curl -s http://localhost:8000/health/detailed | jq

# Check cache performance
curl -s http://localhost:8000/performance/cache-metrics | jq
```

### 4. Nginx Optimization

```bash
# Check Nginx performance
sudo nginx -T | grep -E "(worker_processes|worker_connections|keepalive_timeout)"

# Optimize Nginx configuration
sudo vim /etc/nginx/nginx.conf
```

---

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Server provisioned and configured
- [ ] Domain name registered and DNS configured
- [ ] SSL certificate obtained
- [ ] Environment variables configured
- [ ] Database created and configured
- [ ] Redis installed and configured
- [ ] Nginx installed and configured
- [ ] Firewall configured
- [ ] Monitoring set up

### Deployment

- [ ] Application code deployed
- [ ] Dependencies installed
- [ ] Database migrations run
- [ ] Application service started
- [ ] Nginx configuration applied
- [ ] SSL certificate installed
- [ ] Health checks passing
- [ ] Security audit passed

### Post-Deployment

- [ ] Monitoring alerts configured
- [ ] Backup procedures tested
- [ ] Performance optimization applied
- [ ] Security hardening completed
- [ ] Documentation updated
- [ ] Team trained on maintenance procedures

---

## 🆘 Emergency Procedures

### 1. Application Down

```bash
# Quick restart
sudo systemctl restart maplehustlecan

# Check status
sudo systemctl status maplehustlecan

# If still down, check logs
sudo journalctl -u maplehustlecan -f
```

### 2. Database Issues

```bash
# Restart PostgreSQL
sudo systemctl restart postgresql

# Check database status
sudo -u postgres psql -c "SELECT 1;"

# If database is corrupted, restore from backup
gunzip -c /opt/maplehustlecan/backups/db_backup_latest.sql.gz | psql -h localhost -U maplehustlecan -d maplehustlecan_prod
```

### 3. Security Breach

```bash
# Immediate response
sudo fail2ban-client set nginx-http-auth banip <attacker_ip>
sudo ufw deny from <attacker_ip>

# Check logs for compromise
sudo grep -r "suspicious" /var/log/

# Run security audit
cd /opt/maplehustlecan
source venv/bin/activate
python scripts/security_audit.py
```

---

## 📞 Support & Maintenance

### 1. Monitoring Endpoints

- **Health Check**: `https://yourdomain.com/health`
- **Detailed Health**: `https://yourdomain.com/health/detailed`
- **Performance Metrics**: `https://yourdomain.com/performance/metrics`
- **Security Dashboard**: `https://yourdomain.com/security/dashboard`

### 2. Log Locations

- **Application Logs**: `/var/log/maplehustlecan/`
- **System Logs**: `/var/log/syslog`
- **Nginx Logs**: `/var/log/nginx/`
- **PostgreSQL Logs**: `/var/log/postgresql/`
- **Redis Logs**: `/var/log/redis/`

### 3. Configuration Files

- **Application Config**: `/opt/maplehustlecan/.env.production`
- **Nginx Config**: `/etc/nginx/sites-available/maplehustlecan`
- **Systemd Service**: `/etc/systemd/system/maplehustlecan.service`
- **PostgreSQL Config**: `/etc/postgresql/15/main/postgresql.conf`
- **Redis Config**: `/etc/redis/redis.conf`

---

## 🎯 Conclusion

This production deployment guide provides comprehensive instructions for deploying MapleHustleCAN to production with enterprise-grade security, monitoring, and scalability. Follow these steps carefully and adapt them to your specific infrastructure requirements.

For additional support or questions, refer to the project documentation or contact the development team.

---

**Last Updated**: September 2024  
**Version**: 1.0  
**Maintainer**: MapleHustleCAN Development Team
