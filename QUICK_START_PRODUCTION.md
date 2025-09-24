# 🚀 Quick Start Production Deployment

This is a simplified guide for quickly deploying MapleHustleCAN to production.

## ⚡ One-Command Deployment

```bash
# Download and run the automated deployment script
curl -sSL https://raw.githubusercontent.com/NBhosale/MappleHustleCAN/main/scripts/deploy_production.sh | bash
```

## 📋 Prerequisites

Before running the deployment script, ensure you have:

- [ ] Ubuntu 20.04+ server with root/sudo access
- [ ] Domain name pointing to your server's IP
- [ ] At least 4GB RAM and 10GB disk space
- [ ] Email address for SSL certificate

## 🔧 Manual Deployment Steps

### 1. Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Create application user
sudo adduser --system --group --home /opt/maplehustlecan maplehustlecan
sudo usermod -aG sudo maplehustlecan
```

### 2. Run Deployment Script

```bash
# Switch to application user
sudo su - maplehustlecan

# Download deployment script
wget https://raw.githubusercontent.com/NBhosale/MappleHustleCAN/main/scripts/deploy_production.sh
chmod +x deploy_production.sh

# Run deployment
./deploy_production.sh
```

### 3. Follow Prompts

The script will ask for:
- Domain name (e.g., `yourdomain.com`)
- Email address for SSL certificate

### 4. Verify Deployment

```bash
# Check application status
sudo systemctl status maplehustlecan

# Check health
curl https://yourdomain.com/health

# View logs
sudo journalctl -u maplehustlecan -f
```

## 🌐 Access Your Application

After successful deployment:

- **API Documentation**: `https://yourdomain.com/docs`
- **ReDoc**: `https://yourdomain.com/redoc`
- **Health Check**: `https://yourdomain.com/health`
- **Security Dashboard**: `https://yourdomain.com/security/dashboard`

## ⚙️ Post-Deployment Configuration

### 1. Update Environment Variables

Edit the production environment file:

```bash
sudo vim /opt/maplehustlecan/.env.production
```

Update the following settings:

```env
# Email Configuration
SMTP_HOST=your-smtp-host
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-app-password

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# File Storage (AWS S3)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-bucket-name

# Error Tracking (Sentry)
SENTRY_DSN=your-sentry-dsn
```

### 2. Restart Application

```bash
sudo systemctl restart maplehustlecan
```

## 🔒 Security Checklist

- [ ] SSL certificate installed and working
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Fail2Ban active and monitoring
- [ ] Database password changed from default
- [ ] Application secrets generated
- [ ] Security headers enabled
- [ ] Rate limiting configured

## 📊 Monitoring

### Health Checks

```bash
# Application health
curl https://yourdomain.com/health

# Detailed health
curl https://yourdomain.com/health/detailed

# Performance metrics
curl https://yourdomain.com/performance/metrics
```

### Logs

```bash
# Application logs
sudo journalctl -u maplehustlecan -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Security logs
sudo tail -f /var/log/maplehustlecan/security.log
```

## 🛠️ Maintenance

### Update Application

```bash
cd /opt/maplehustlecan
sudo -u maplehustlecan git pull origin main
sudo -u maplehustlecan bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u maplehustlecan bash -c "source venv/bin/activate && alembic upgrade head"
sudo systemctl restart maplehustlecan
```

### Backup Database

```bash
# Create backup
sudo -u postgres pg_dump maplehustlecan_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
sudo -u postgres psql maplehustlecan_prod < backup_file.sql
```

## 🆘 Troubleshooting

### Application Won't Start

```bash
# Check status
sudo systemctl status maplehustlecan

# Check logs
sudo journalctl -u maplehustlecan -f

# Check configuration
sudo -u maplehustlecan bash -c "cd /opt/maplehustlecan && source venv/bin/activate && python -c 'from app.main import app; print(\"App loads successfully\")'"
```

### Database Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connection
sudo -u postgres psql -c "SELECT 1;"

# Check database exists
sudo -u postgres psql -c "\l" | grep maplehustlecan
```

### SSL Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL
curl -I https://yourdomain.com
```

## 📞 Support

For detailed deployment instructions, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)

For issues and support:
- Check logs: `sudo journalctl -u maplehustlecan -f`
- Run health checks: `curl https://yourdomain.com/health`
- Review security audit: `python scripts/security_audit.py`

---

**Note**: This quick start guide provides basic deployment. For production environments with high traffic, refer to the comprehensive [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for advanced configuration, monitoring, and security hardening.
