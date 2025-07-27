# 🚀 BOQMate Deployment Guide

## 📋 Pre-Deployment Checklist

### **1. Environment Setup**
- [ ] Docker and Docker Compose installed
- [ ] SSL certificates ready (or self-signed for development)
- [ ] Domain name configured (for production)
- [ ] Environment variables configured

### **2. Security Configuration**
- [ ] Changed default JWT_SECRET_KEY
- [ ] Changed default ENCRYPTION_KEY
- [ ] Set OPENAI_API_KEY
- [ ] Set SUPABASE_JWT_SECRET
- [ ] Set SUPABASE_PROJECT_ID
- [ ] Configured ALLOWED_ORIGINS

### **3. Infrastructure**
- [ ] Server with sufficient resources (2GB RAM, 1 CPU minimum)
- [ ] Firewall configured
- [ ] Backup strategy planned
- [ ] Monitoring setup ready

## 🛠️ Quick Deployment

### **Option 1: Automated Deployment (Recommended)**

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd BOQMate
   ```

2. **Set up environment variables:**
   ```bash
   cp backend/env.example .env
   # Edit .env with your actual values
   ```

3. **Run the deployment script:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

### **Option 2: Manual Docker Deployment**

1. **Build and start services:**
   ```bash
   docker-compose up --build -d
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

## 🌐 Production Deployment

### **1. Server Requirements**

**Minimum Requirements:**
- CPU: 1 core
- RAM: 2GB
- Storage: 20GB
- OS: Ubuntu 20.04+ or CentOS 8+

**Recommended Requirements:**
- CPU: 2+ cores
- RAM: 4GB+
- Storage: 50GB SSD
- OS: Ubuntu 22.04 LTS

### **2. Server Setup**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### **3. SSL Certificate Setup**

**For Let's Encrypt (Recommended):**

```bash
# Install Certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to project
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*
```

**For Self-Signed (Development):**
```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

### **4. Environment Configuration**

Create `.env` file with production values:

```env
# Security Keys (CHANGE THESE!)
JWT_SECRET_KEY=your-very-secure-jwt-key-32-characters-minimum
ENCRYPTION_KEY=your-32-byte-encryption-key-here
SECURITY_SECRET_KEY=your-security-secret-key-here

# API Keys
OPENAI_API_KEY=your-openai-api-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_PROJECT_ID=your-supabase-project-id

# Production Settings
ALLOWED_ORIGINS=https://yourdomain.com
RATE_LIMIT_REQUESTS=50
MAX_FILE_SIZE=52428800

# Monitoring
LOG_SECURITY_EVENTS=true
MONITORING_ENABLED=true
ALERT_EMAIL=admin@yourdomain.com
```

### **5. Firewall Configuration**

```bash
# Configure UFW firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### **6. Deploy Application**

```bash
# Clone repository
git clone <your-repo-url>
cd BOQMate

# Set up environment
cp backend/env.example .env
# Edit .env with production values

# Deploy
chmod +x deploy.sh
./deploy.sh
```

## 🔒 Security Hardening

### **1. Server Security**

```bash
# Disable root login
sudo passwd -l root

# Configure SSH
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no
sudo systemctl restart ssh

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### **2. Application Security**

- ✅ Rate limiting enabled
- ✅ Input validation active
- ✅ File upload restrictions
- ✅ SSL/TLS encryption
- ✅ Security headers configured
- ✅ Authentication middleware

### **3. Monitoring Setup**

```bash
# View security logs
tail -f backend/logs/security_monitor.log

# View application logs
docker-compose logs -f backend

# Check security status
docker exec -it boqmate-backend python security_monitor.py --report
```

## 📊 Monitoring & Maintenance

### **1. Health Checks**

```bash
# Check application health
curl https://yourdomain.com/health

# Check Docker services
docker-compose ps

# Check resource usage
docker stats
```

### **2. Backup Strategy**

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/boqmate_$DATE"

mkdir -p $BACKUP_DIR

# Backup database
docker exec boqmate-backend sqlite3 /app/boqmate.db ".backup $BACKUP_DIR/boqmate.db"

# Backup uploads
docker cp boqmate-backend:/app/uploads $BACKUP_DIR/

# Backup logs
docker cp boqmate-backend:/app/logs $BACKUP_DIR/

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completed: $BACKUP_DIR.tar.gz"
EOF

chmod +x backup.sh
```

### **3. Log Rotation**

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/boqmate

# Add configuration:
/var/log/boqmate/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

## 🚨 Troubleshooting

### **Common Issues**

**1. Service won't start:**
```bash
# Check logs
docker-compose logs backend

# Check environment variables
docker-compose config

# Restart services
docker-compose restart
```

**2. SSL certificate issues:**
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Regenerate certificates
rm ssl/cert.pem ssl/key.pem
./deploy.sh
```

**3. Database issues:**
```bash
# Check database
docker exec -it boqmate-backend sqlite3 /app/boqmate.db ".tables"

# Reset database (WARNING: loses data)
docker exec -it boqmate-backend rm /app/boqmate.db
docker-compose restart backend
```

### **Performance Optimization**

**1. Resource limits:**
```yaml
# Add to docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

**2. Database optimization:**
```sql
-- Run in database
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
```

## 🔄 Updates & Maintenance

### **1. Application Updates**

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### **2. Security Updates**

```bash
# Update base images
docker-compose pull
docker-compose up -d

# Update dependencies
docker-compose exec backend pip install --upgrade -r requirements.txt
```

### **3. Monitoring Updates**

```bash
# Check for security alerts
docker-compose exec backend python security_monitor.py --report

# Update SSL certificates
sudo certbot renew
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
docker-compose restart nginx
```

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment: `docker-compose config`
3. Test connectivity: `curl https://yourdomain.com/health`
4. Review security guide: `SECURITY_GUIDE.md`

---

**Your BOQMate application is now ready for production deployment!** 🚀