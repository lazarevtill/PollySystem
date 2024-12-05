# PollySystem

---

# WORK IN PROGRESS

---
# PollySystem

PollySystem is a robust infrastructure management system built for managing Docker-based deployments across multiple machines in a network. It provides a modular, plugin-based architecture with real-time monitoring and management capabilities.

## System Architecture

### Core Components

#### Backend (FastAPI)

1. **Plugin System**
   - Modular architecture allowing easy extension
   - Plugin lifecycle management (initialization, cleanup)
   - Dependency resolution between plugins
   - Hot-reloading support in development

2. **Authentication System**
   - JWT-based authentication with role-based access control
   - Rate limiting and brute force protection
   - Session management and token refresh
   - Secure password hashing using bcrypt

3. **Core Plugins**

   a. **Machines Plugin**
   - SSH-based machine management
   - Real-time health monitoring
   - Secure key management
   - Command execution and automation
   - System metrics collection (CPU, Memory, Disk)

   b. **Docker Plugin**
   - Container lifecycle management
   - Image registry integration
   - Docker Compose support
   - Container health monitoring
   - Volume and network management
   - Real-time logs and metrics

   c. **Monitoring Plugin**
   - Prometheus metrics integration
   - Alert rules and notifications
   - Historical data retention
   - Custom metric definitions
   - Dashboard integration

4. **State Management**
   - Redis-based caching and real-time updates
   - Distributed locking mechanism
   - Event propagation system
   - Data persistence

#### Frontend (React)

1. **Plugin Architecture**
   - Dynamic plugin loading
   - Shared component registry
   - Plugin state management
   - Inter-plugin communication

2. **Core Features**
   - Real-time updates using WebSocket
   - Responsive dashboard design
   - Dark/Light theme support
   - Error boundary implementation
   - Loading state management

3. **Plugin UIs**
   
   a. **Machine Management**
   - Machine status dashboard
   - SSH key management interface
   - Command execution console
   - System metrics visualization

   b. **Docker Management**
   - Container management interface
   - Image registry browser
   - Log viewer with filtering
   - Resource usage graphs
   - Compose file editor

   c. **Monitoring Dashboard**
   - Real-time metrics graphs
   - Alert management interface
   - Custom dashboard creation
   - Metric exploration tools

## Implementation Details

### Backend Structure

```
backend/
├── app/
│   ├── core/               # Core framework components
│   │   ├── auth.py        # Authentication system
│   │   ├── config.py      # Configuration management
│   │   ├── exceptions.py  # Custom exception handling
│   │   └── plugin_manager.py # Plugin system
│   ├── plugins/           # Plugin implementations
│   │   ├── machines/      # Machine management
│   │   ├── docker/        # Docker operations
│   │   └── monitoring/    # System monitoring
│   └── main.py           # Application entry point
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/        # Shared components
│   ├── hooks/            # Custom React hooks
│   ├── plugins/          # Plugin implementations
│   └── App.tsx          # Main application
```

## Key Features

1. **Security**
   - Role-based access control
   - Secure credential storage
   - SSL/TLS encryption
   - Rate limiting
   - Audit logging

2. **Scalability**
   - Horizontal scaling support
   - Redis-based caching
   - Connection pooling
   - Asynchronous operations

3. **Monitoring**
   - Real-time metrics
   - Custom alert rules
   - Historical data analysis
   - Performance monitoring
   - Health checks

4. **Reliability**
   - Automatic failover
   - Error recovery
   - Transaction management
   - Data backup support

## Technical Requirements

### Backend
- Python 3.11+
- FastAPI
- Redis
- Docker
- Prometheus

### Frontend
- Node.js 18+
- React 18
- TypeScript 5
- Vite

### Infrastructure
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