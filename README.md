# PollySystem

---

# WORK IN PROGRESS

---

A comprehensive infrastructure management system that allows you to manage Docker deployments across multiple machines through a unified web interface. The system provides container orchestration, monitoring, automated backups, and health checks.

## 🌟 Features

### Core Functionality
- **Machine Management**
  - SSH key-based authentication
  - Automatic key generation and distribution
  - VPN integration for private networks
  - Health monitoring and status tracking

- **Deployment Management**
  - Docker container deployment
  - Docker Compose support
  - Dynamic subdomain allocation
  - Automated health checks
  - Container logs and metrics
  - Start/Stop/Restart capabilities

- **Monitoring & Alerting**
  - Real-time resource monitoring
  - Container health tracking
  - Custom alert thresholds
  - Multi-channel notifications (Slack, Telegram)
  - Historical metrics and trends
  - Grafana dashboards

- **Security**
  - SSL/TLS encryption
  - Automated certificate management
  - Rate limiting and DDoS protection
  - Secure header configuration
  - VPN network integration
  - Audit logging

- **Backup System**
  - Automated backups
  - Multiple storage backends (local, S3)
  - Configurable retention policies
  - One-click restoration
  - Backup verification

### Additional Features
- Modern React frontend with real-time updates
- RESTful API with comprehensive documentation
- Prometheus metrics integration
- Granular access control
- Detailed system logging
- Performance optimization

## 🛠 Technology Stack

### Frontend
- React 18+
- TypeScript
- TailwindCSS
- React Query
- React Router
- Lucide Icons
- Chart.js

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic
- Paramiko (SSH)
- Docker SDK
- Redis

### Infrastructure
- Nginx
- PostgreSQL
- Redis
- Docker
- Prometheus
- Grafana

### Monitoring
- Prometheus
- Grafana
- Custom Python monitors
- Alert manager

## 📋 Prerequisites

- Docker and Docker Compose
- Domain with DNS access
- VPN network (OpenVPN or WireGuard)
- SSL certificates
- AWS account (optional, for S3 backups)

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/infra-manager.git
cd infra-manager
```

2. Create required directories:
```bash
mkdir -p /opt/infra-manager/{frontend,backend,monitoring,nginx/{ssl,conf.d}}
```

3. Configure environment variables:
```bash
cp .env.example .env
nano .env
```

4. Generate SSL certificates and DH parameters:
```bash
# Generate DH parameters
openssl dhparam -out nginx/dhparam.pem 2048

# Place your SSL certificates in nginx/ssl/
cp /path/to/your/fullchain.pem nginx/ssl/
cp /path/to/your/privkey.pem nginx/ssl/
```

5. Build and start the services:
```bash
docker-compose up -d
```

## ⚙️ Configuration

### Environment Variables

```env
# PostgreSQL
POSTGRES_PASSWORD=secure_password_here
POSTGRES_USER=inframanager
POSTGRES_DB=inframanager

# Security
SECRET_KEY=your_secret_key_here

# AWS (Optional)
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
AWS_BACKUP_BUCKET=your_backup_bucket

# Monitoring
SLACK_WEBHOOK_URL=your_slack_webhook
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Grafana
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### Nginx Configuration

The system uses Nginx as a reverse proxy with the following features:
- SSL/TLS termination
- Rate limiting
- DDoS protection
- WebSocket support
- Caching
- CORS configuration
- Security headers

### Monitoring Configuration

1. Prometheus metrics are available at:
   - System metrics: `http://localhost:9090/metrics`
   - Application metrics: `http://localhost:8000/metrics`

2. Grafana dashboards:
   - Access Grafana at `https://your-domain/grafana`
   - Default dashboards are automatically provisioned
   - Custom dashboards can be imported

## 🔧 Usage

### Adding a New Machine

1. Access the web interface at `https://your-domain`
2. Navigate to "Machines" section
3. Click "Add Machine"
4. Enter machine details:
   - Name
   - VPN hostname (*.in.lc)
   - SSH port (default: 22)
   - SSH username
5. The system will generate SSH keys
6. Add the public key to the machine's authorized_keys

### Deploying Containers

1. Navigate to "Deployments" section
2. Click "Deploy Container" or "Deploy Compose"
3. Select target machine
4. For containers:
   - Enter image name
   - Configure environment variables
   - Set port mappings
   - Add volumes if needed
5. For Compose:
   - Upload docker-compose.yml
   - Configure environment
6. Click Deploy

### Monitoring

1. Access Grafana dashboards:
   - System metrics
   - Container metrics
   - Application metrics
   - Custom metrics

2. Configure alerts:
   - Set thresholds
   - Configure notification channels
   - Set alert rules

### Backup Management

1. Automated backups:
   - Daily system backups
   - Configuration backups
   - Database backups

2. Manual backups:
   - Navigate to "Settings"
   - Click "Create Backup"
   - Select backup type
   - Choose storage location

3. Restore from backup:
   - Select backup from list
   - Click "Restore"
   - Confirm restoration

## 🔒 Security

### Network Security
- All traffic is encrypted with SSL/TLS
- VPN network integration
- Rate limiting and DDoS protection
- Secure headers configuration

### Authentication
- SSH key-based authentication for machines
- JWT tokens for API authentication
- Session management
- Role-based access control

### Data Security
- Encrypted storage of sensitive data
- Regular security updates
- Audit logging
- Backup encryption

## 📊 Monitoring & Alerts

### Metrics
- CPU, Memory, and Disk usage
- Container metrics
- Application metrics
- Custom metrics

### Alerts
- Resource usage alerts
- Service health alerts
- Security alerts
- Custom alert rules

### Notification Channels
- Slack
- Telegram
- Email
- Custom webhooks

## 🔍 Troubleshooting

### Common Issues

1. Connection Issues:
```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f [service_name]

# Check Nginx configuration
docker-compose exec nginx nginx -t
```

2. Database Issues:
```bash
# Check database logs
docker-compose logs db

# Connect to database
docker-compose exec db psql -U inframanager -d inframanager
```

3. Monitoring Issues:
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# View monitoring logs
docker-compose logs monitoring
```

### Health Checks

The system includes comprehensive health checks:
- Container health checks
- Service health checks
- Database health checks
- API health checks
- SSL certificate monitoring
