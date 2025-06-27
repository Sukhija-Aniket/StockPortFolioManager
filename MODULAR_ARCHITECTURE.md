# Modular Architecture Guide

This document explains the modular architecture that allows frontend, backend, and worker components to run independently on different machines with enhanced security and authentication.

## Architecture Overview

The Stock Portfolio Manager is structured as independent microservices with Google OAuth authentication:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │   Worker    │
│   (React)   │◄──►│   (Flask)   │◄──►│   (Async)   │
│             │    │ + OAuth     │    │ + Broker    │
│             │    │ + Session   │    │   Config    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           └───────┬───────────┘
                                   │
                           ┌─────────────┐
                           │  RabbitMQ   │
                           │ (Message    │
                           │  Broker)    │
                           └─────────────┘
```

## Component Independence

### 1. Frontend (React)
- **Location**: `./frontend/`
- **Dependencies**: None (pure React app)
- **Authentication**: Google OAuth via backend
- **Communication**: HTTP API calls to backend
- **Features**:
  - Modern React interface with Bootstrap
  - Google OAuth login integration
  - Spreadsheet management UI
  - File upload and data sync
  - Real-time status updates
- **Deployment**: Can run on any machine with Node.js

### 2. Backend (Flask API)
- **Location**: `./backend/`
- **Dependencies**: 
  - Shared library (installed via git)
  - PostgreSQL database
  - RabbitMQ (for task queue)
  - Google OAuth credentials
- **Authentication**: Google OAuth 2.0 with session management
- **Features**:
  - OAuth 2.0 authentication flow
  - Session management with token validation
  - Spreadsheet CRUD operations
  - Task queue management
  - Health check endpoints
- **Communication**: HTTP API, RabbitMQ messages
- **Deployment**: Can run on any machine with Python 3.8+

### 3. Worker (Background Tasks)
- **Location**: `./worker/`
- **Dependencies**:
  - Shared library (installed via git)
  - PostgreSQL database
  - RabbitMQ (for task queue)
  - Broker configuration files
- **Features**:
  - Asynchronous data processing
  - Broker-specific calculations
  - FIFO cost basis calculations
  - Google Sheets integration
  - Configurable concurrency
- **Communication**: RabbitMQ messages
- **Deployment**: Can run on any machine with Python 3.8+

### 4. Shared Library
- **Location**: `./shared/`
- **Purpose**: Common utilities, models, and constants
- **Features**:
  - Enhanced credentials management with expiry
  - Data processing utilities
  - Constants and enums
  - Google Sheets integration
- **Installation**: Via git repository or local development
- **Versioning**: Semantic versioning with git tags (currently v0.1.4)

## Authentication & Security

### Google OAuth Flow
1. **Frontend**: Redirects to Google OAuth
2. **Backend**: Handles OAuth callback and token exchange
3. **Session Management**: Secure session storage with token validation
4. **Token Refresh**: Automatic token refresh and validation

### Credentials Management
- **Enhanced Storage**: Credentials include expiry information
- **Token Validation**: Local and API-based token validation
- **Automatic Cleanup**: Expired tokens trigger re-authentication

## Deployment Options

### Option 1: Monolithic (All on one machine)
```bash
# Use the main docker-compose.yaml
docker-compose up -d
```

### Option 2: Distributed (Different machines)
```bash
# Machine 1: Database and Message Queue
docker-compose up postgres rabbitmq -d

# Machine 2: Backend API
cd backend
docker build -t stock-portfolio-backend .
docker run -d --name backend \
  -e DATABASE_URL=postgresql://user:pass@machine1:5432/stock_portfolio \
  -e RABBITMQ_HOST=machine1 \
  -e GOOGLE_CREDENTIALS_FILE=secrets/credentials.json \
  stock-portfolio-backend

# Machine 3: Worker
cd worker
docker build -t stock-portfolio-worker .
docker run -d --name worker \
  -e DATABASE_URL=postgresql://user:pass@machine1:5432/stock_portfolio \
  -e RABBITMQ_HOST=machine1 \
  stock-portfolio-worker

# Machine 4: Frontend
cd frontend
docker build -t stock-portfolio-frontend .
docker run -d --name frontend \
  -e REACT_APP_BACKEND_SERVICE=machine2:5000 \
  stock-portfolio-frontend
```

### Option 3: Kubernetes Deployment
Each component can be deployed as separate Kubernetes deployments with appropriate service configurations.

## Development Workflow

### Local Development
```bash
# Install shared package in editable mode
cd shared
pip install -e .

# Backend development
cd backend
pip install -r requirements-dev.txt
python app.py

# Worker development
cd worker
pip install -r requirements-dev.txt
python worker.py

# Frontend development
cd frontend
npm install
npm start
```

### Development with Docker
```bash
# Use development docker-compose
docker-compose -f docker-compose.dev.yml up -d
```

## Shared Library Management

### Installing Shared Library
```bash
# From git repository (production)
pip install git+https://github.com/Sukhija-Aniket/StockPortfolioManager.git@v0.1.4#subdirectory=shared

# From local directory (development)
pip install -e ./shared

# From PyPI (if published)
pip install stock-portfolio-shared==0.1.4
```

### Updating Shared Library
1. Make changes in `shared/` directory
2. Update version in `shared/setup.py`
3. Commit and push changes
4. Create git tag for new version
5. Update dependent components to use new version

### Version Pinning
In production, pin the shared library version:
```bash
# In requirements.txt
git+https://github.com/Sukhija-Aniket/StockPortfolioManager.git@v0.1.4#subdirectory=shared
```

## Configuration

### Environment Variables
Each component can be configured independently:

**Backend**:
- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_HOST`: RabbitMQ host address
- `FRONTEND_SERVICE`: Frontend service URL
- `GOOGLE_CREDENTIALS_FILE`: Path to OAuth credentials
- `SECRET_KEY`: Flask session secret key

**Worker**:
- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_HOST`: RabbitMQ host address
- `WORKER_CONCURRENCY`: Number of concurrent tasks
- `WORKER_TIMEOUT`: Task timeout in seconds

**Frontend**:
- `REACT_APP_BACKEND_SERVICE`: Backend API URL

### Broker Configuration
Broker-specific rates are stored in `worker/config/participant_config.json`:
```json
{
  "zerodha": {
    "brokerage": {
      "intraday": {"rate": 0.0005, "max_amount": 20.0},
      "delivery": {"rate": 0.0005, "max_amount": 20.0}
    },
    "stt": {"buy": 0.0005, "sell": 0.0005},
    "gst": 0.18,
    "dp_charges": 13.5
  }
}
```

## Network Configuration

### Production Network Setup
```bash
# Create a shared network for inter-service communication
docker network create stock-portfolio-network

# Run services on the shared network
docker run --network stock-portfolio-network ...
```

### Load Balancer Configuration
For production deployments, consider:
- Nginx reverse proxy for frontend
- API gateway for backend
- Database connection pooling
- Message queue clustering

## Monitoring and Health Checks

Each component includes health checks:
- **Backend**: `GET /health` with database connectivity check
- **Worker**: RabbitMQ connection check
- **Database**: PostgreSQL readiness check
- **Message Queue**: RabbitMQ ping
- **Authentication**: Token validation status

## Scaling

### Horizontal Scaling
```bash
# Scale workers
docker-compose up --scale worker=3

# Scale backend (with load balancer)
docker-compose up --scale backend=2
```

### Vertical Scaling
Adjust resource limits in docker-compose.yaml:
```yaml
services:
  worker:
    mem_limit: 2G
    cpus: 2.0
```

## Security Considerations

1. **Network Security**: Use private networks for inter-service communication
2. **Authentication**: Google OAuth 2.0 with secure session management
3. **Secrets Management**: Use environment variables or secrets management
4. **Database Security**: Use connection pooling and proper credentials
5. **API Security**: Implement rate limiting and input validation
6. **Token Security**: Automatic token refresh and validation

## Migration Guide

### From Monolithic to Modular
1. Update Dockerfiles to use new structure
2. Update docker-compose.yaml
3. Configure Google OAuth credentials
4. Test each component independently
5. Deploy components to separate machines
6. Update network configuration
7. Monitor and adjust as needed

## Troubleshooting

### Common Issues
1. **Shared library not found**: Ensure proper installation from git
2. **Network connectivity**: Check Docker networks and firewall rules
3. **Database connections**: Verify connection strings and credentials
4. **Message queue**: Check RabbitMQ connectivity and permissions
5. **OAuth authentication**: Verify Google credentials and redirect URIs
6. **Token expiration**: Check token validation and refresh logic

### Debug Commands
```bash
# Check shared library installation
python -c "import stock_portfolio_shared; print('OK')"

# Test database connection
python -c "import psycopg2; print('DB OK')"

# Test RabbitMQ connection
python -c "import pika; print('MQ OK')"

# Check OAuth credentials
python -c "from google.oauth2.credentials import Credentials; print('OAuth OK')"
```

### Release Workflow
The project includes automated release workflows:
- **Manual Release**: `manual-release.yml` for controlled releases
- **Auto Release**: `release.yml` for automatic releases
- **Branch Protection**: Compliant with repository protection rules
- **Version Management**: Semantic versioning with git tags 