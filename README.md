# PollySystem

---

# WORK IN PROGRESS

---
# PollySystem

PollySystem is a robust infrastructure management system built for managing Docker-based deployments across multiple machines in a network. It provides a modular, plugin-based architecture with real-time monitoring and management capabilities.

## 🌟 Features

### Core Functionality
- **Machine Management**
  - SSH key-based authentication
  - Automatic key generation and distribution
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
  - Rate limiting and DDoS protection
  - Secure header configuration
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
- Alert manager

## 📋 Prerequisites

- Docker and Docker Compose
- Redis
- Prometheus
- Nginx (for production)

## Installation

1. **Clone Repository**
```bash
git clone https://github.com/lazarevtill/PollySystem.git
cd PollySystem
```

2. **Environment Setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start Services**
```bash
docker-compose up -d
```

4. **Access Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Prometheus: http://localhost:9090

## Development

1. **Backend Development**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

2. **Frontend Development**
```bash
cd frontend
npm install
npm run dev
```

## Testing (NTBD)

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Production Deployment

1. **Build Images**
```bash
docker-compose -f docker-compose.prod.yml build
```

2. **Deploy**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FastAPI team for the amazing framework
- Docker team for containerization support
- All contributors and users of PollySystem