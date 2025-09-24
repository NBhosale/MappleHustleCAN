#!/bin/bash

# MapleHustleCAN Production Deployment Script
# This script automates the production deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/maplehustlecan"
APP_USER="maplehustlecan"
SERVICE_NAME="maplehustlecan"
NGINX_SITE="maplehustlecan"
DOMAIN=""
EMAIL=""

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Please run as a regular user with sudo privileges."
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check OS
    if ! grep -q "Ubuntu" /etc/os-release; then
        warn "This script is optimized for Ubuntu. Other distributions may require modifications."
    fi
    
    # Check available memory
    MEMORY_GB=$(free -g | awk 'NR==2{print $2}')
    if [ $MEMORY_GB -lt 4 ]; then
        warn "System has less than 4GB RAM. Consider upgrading for production use."
    fi
    
    # Check disk space
    DISK_SPACE=$(df / | awk 'NR==2{print $4}')
    if [ $DISK_SPACE -lt 10485760 ]; then  # 10GB in KB
        error "Insufficient disk space. At least 10GB required."
    fi
    
    log "System requirements check passed"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y curl wget git vim htop unzip software-properties-common \
        postgresql-15 postgresql-client-15 postgresql-15-postgis-3 \
        redis-server nginx certbot python3-certbot-nginx \
        python3.13 python3.13-venv python3.13-dev python3-pip \
        ufw fail2ban
    
    log "System dependencies installed"
}

# Create application user
create_user() {
    log "Creating application user..."
    
    if ! id "$APP_USER" &>/dev/null; then
        sudo adduser --system --group --home $APP_DIR $APP_USER
        sudo usermod -aG sudo $APP_USER
        log "Application user created"
    else
        log "Application user already exists"
    fi
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."
    
    sudo mkdir -p $APP_DIR
    sudo chown $APP_USER:$APP_USER $APP_DIR
    
    # Clone repository if not exists
    if [ ! -d "$APP_DIR/.git" ]; then
        sudo -u $APP_USER git clone https://github.com/NBhosale/MappleHustleCAN.git $APP_DIR
    else
        sudo -u $APP_USER bash -c "cd $APP_DIR && git pull origin main"
    fi
    
    # Create log directory
    sudo mkdir -p /var/log/maplehustlecan
    sudo chown $APP_USER:$APP_USER /var/log/maplehustlecan
    
    log "Application directory setup complete"
}

# Setup Python environment
setup_python_env() {
    log "Setting up Python environment..."
    
    sudo -u $APP_USER bash -c "
        cd $APP_DIR
        python3.13 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    "
    
    log "Python environment setup complete"
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE maplehustlecan_prod;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE USER $APP_USER WITH PASSWORD 'secure_password_123';" 2>/dev/null || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE maplehustlecan_prod TO $APP_USER;"
    
    # Enable PostGIS
    sudo -u postgres psql -d maplehustlecan_prod -c "CREATE EXTENSION IF NOT EXISTS postgis;"
    sudo -u postgres psql -d maplehustlecan_prod -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    
    log "Database setup complete"
}

# Create environment file
create_env_file() {
    log "Creating environment file..."
    
    if [ -z "$DOMAIN" ]; then
        read -p "Enter your domain name: " DOMAIN
    fi
    
    if [ -z "$EMAIL" ]; then
        read -p "Enter your email for SSL certificate: " EMAIL
    fi
    
    sudo -u $APP_USER tee $APP_DIR/.env.production > /dev/null << EOF
# Application Configuration
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=postgresql+psycopg2://$APP_USER:secure_password_123@localhost:5432/maplehustlecan_prod

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security Configuration
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
ALLOWED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

# SSL Configuration
HTTPS_ONLY=true
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=true
SECURE_HSTS_PRELOAD=true

# Email Configuration (Update with your SMTP settings)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# SMS Configuration (Update with your Twilio settings)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# File Storage Configuration (Update with your AWS settings)
STORAGE_TYPE=local
# AWS_ACCESS_KEY_ID=your-aws-access-key
# AWS_SECRET_ACCESS_KEY=your-aws-secret-key
# AWS_S3_BUCKET=maplehustlecan-files
# AWS_S3_REGION=us-east-1

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
EOF

    sudo chmod 600 $APP_DIR/.env.production
    log "Environment file created"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    sudo -u $APP_USER bash -c "
        cd $APP_DIR
        source venv/bin/activate
        export ENVIRONMENT=production
        export DATABASE_URL=postgresql+psycopg2://$APP_USER:secure_password_123@localhost:5432/maplehustlecan_prod
        alembic upgrade head
    "
    
    log "Database migrations complete"
}

# Create systemd service
create_systemd_service() {
    log "Creating systemd service..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=MapleHustleCAN FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env.production
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    log "Systemd service created"
}

# Configure Nginx
configure_nginx() {
    log "Configuring Nginx..."
    
    sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null << EOF
# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;

# Upstream configuration
upstream maplehustlecan_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Main server block
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Auth routes with stricter rate limiting
    location /auth/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://maplehustlecan_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://maplehustlecan_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Security dashboard (admin only)
    location /security/ {
        proxy_pass http://maplehustlecan_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Root redirect to API docs
    location / {
        return 301 https://\$server_name/docs;
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl reload nginx
    
    log "Nginx configured"
}

# Setup SSL
setup_ssl() {
    log "Setting up SSL certificate..."
    
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive
    
    # Setup automatic renewal
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
    
    log "SSL certificate installed"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80
    sudo ufw allow 443
    sudo ufw allow from 127.0.0.1 to any port 5432
    sudo ufw allow from 127.0.0.1 to any port 6379
    sudo ufw --force enable
    
    log "Firewall configured"
}

# Configure Fail2Ban
configure_fail2ban() {
    log "Configuring Fail2Ban..."
    
    sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
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
EOF

    sudo systemctl restart fail2ban
    sudo systemctl enable fail2ban
    
    log "Fail2Ban configured"
}

# Start services
start_services() {
    log "Starting services..."
    
    sudo systemctl start postgresql
    sudo systemctl start redis-server
    sudo systemctl start $SERVICE_NAME
    sudo systemctl start nginx
    
    # Wait for services to start
    sleep 10
    
    # Check service status
    sudo systemctl is-active --quiet postgresql || error "PostgreSQL failed to start"
    sudo systemctl is-active --quiet redis-server || error "Redis failed to start"
    sudo systemctl is-active --quiet $SERVICE_NAME || error "Application failed to start"
    sudo systemctl is-active --quiet nginx || error "Nginx failed to start"
    
    log "All services started successfully"
}

# Run health checks
run_health_checks() {
    log "Running health checks..."
    
    # Check application health
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log "Application health check passed"
    else
        error "Application health check failed"
    fi
    
    # Check database connection
    sudo -u postgres psql -c "SELECT 1;" > /dev/null || error "Database connection failed"
    
    # Check Redis connection
    redis-cli ping > /dev/null || error "Redis connection failed"
    
    log "All health checks passed"
}

# Create monitoring script
create_monitoring_script() {
    log "Creating monitoring script..."
    
    sudo -u $APP_USER tee $APP_DIR/scripts/monitor.sh > /dev/null << 'EOF'
#!/bin/bash

APP_URL="http://localhost:8000/health"
LOG_FILE="/var/log/maplehustlecan/monitor.log"

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL)
    if [ $response -eq 200 ]; then
        echo "$(date): Application is healthy" >> $LOG_FILE
    else
        echo "$(date): Application is unhealthy (HTTP $response)" >> $LOG_FILE
        systemctl restart maplehustlecan
    fi
}

check_health
EOF

    sudo chmod +x $APP_DIR/scripts/monitor.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/scripts/monitor.sh") | crontab -
    
    log "Monitoring script created"
}

# Main deployment function
main() {
    log "Starting MapleHustleCAN production deployment..."
    
    check_root
    check_system
    install_dependencies
    create_user
    setup_app_directory
    setup_python_env
    setup_database
    create_env_file
    run_migrations
    create_systemd_service
    configure_nginx
    setup_ssl
    configure_firewall
    configure_fail2ban
    start_services
    run_health_checks
    create_monitoring_script
    
    log "Production deployment completed successfully!"
    log "Application is available at: https://$DOMAIN"
    log "API documentation: https://$DOMAIN/docs"
    log "Security dashboard: https://$DOMAIN/security/dashboard"
    
    warn "Please update the following in your environment file:"
    warn "- Email SMTP settings"
    warn "- SMS/Twilio settings"
    warn "- AWS S3 settings (if using cloud storage)"
    warn "- Sentry DSN for error tracking"
    warn "- Database password (currently using default)"
}

# Run main function
main "$@"
