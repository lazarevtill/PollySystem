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
  - Health monitoring and status tracking

- **Deployment Management**
  - Docker container deployment
  - Docker Compose support
  - Automated health checks
  - Container logs and metrics
  - Start/Stop/Restart capabilities

- **Monitoring & Alerting**
  - Real-time resource monitoring
  - Container health tracking

- **Security**
  - Audit logging


### Additional Features
- RESTful API with comprehensive documentation
- Prometheus metrics integration
- Detailed system logging

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
- Redis\KeyDB

### Infrastructure
- Nginx
- PostgreSQL\Supabase
- Redis
- Docker
- Prometheus
- Grafana

### Monitoring
- Prometheus
- Grafana
- Custom Python monitors

## 📋 Prerequisites

- Docker and Docker Compose


## 🔧 Usage

### Adding a New Machine

1. Access the web interface at `https://your-domain`
2. Navigate to "Machines" section
3. Click "Add Machine"
4. Enter machine details:
   - Name
   - SSH IP:port (default: 22)
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

