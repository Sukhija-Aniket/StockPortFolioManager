# Docker Compose Setup with RabbitMQ & Async Workers

## 🚀 Overview

This setup provides a scalable, production-ready architecture using:
- **RabbitMQ**: Message broker for reliable task processing
- **Async Workers**: Concurrent task processing with configurable concurrency
- **Docker Compose**: Easy deployment and scaling
- **Health Checks**: Automatic service monitoring
- **Google OAuth**: Secure authentication with Google accounts
- **Enhanced Security**: Token validation and session management

## 📁 Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │   Worker    │
│   (React)   │◄──►│   (Flask)   │◄──►│   (Async)   │
│ + OAuth     │    │ + OAuth     │    │ + Broker    │
│ + Session   │    │ + Session   │    │   Config    │
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

## 🛠️ Services

### 1. **Frontend** (React)
- **Port**: 3000
- **Purpose**: User interface with Google OAuth integration
- **Features**:
  - Modern React interface with Bootstrap
  - Google OAuth login flow
  - Spreadsheet management
  - File upload and data sync
  - Real-time status updates
- **Health Check**: Automatic restart on failure

### 2. **Backend** (Flask)
- **Port**: 5000
- **Purpose**: API endpoints, OAuth authentication, and business logic
- **Features**:
  - Google OAuth 2.0 authentication
  - Session management with token validation
  - Spreadsheet CRUD operations
  - Task queue management
  - Health check endpoints
- **Health Check**: `/health` endpoint with database connectivity
- **Dependencies**: RabbitMQ, Database, Google OAuth credentials

### 3. **Worker** (Async Python)
- **Purpose**: Background task processing with broker-specific calculations
- **Features**:
  - Asynchronous data processing
  - Broker-specific calculations (Zerodha, Upstox, etc.)
  - FIFO cost basis calculations
  - Google Sheets integration
  - Configurable concurrency and timeouts
- **Concurrency**: Configurable (default: 4 concurrent tasks)
- **Timeout**: Configurable (default: 300s)
- **Dependencies**: RabbitMQ, Broker configuration

### 4. **RabbitMQ**
- **Ports**: 5672 (AMQP), 15672 (Management UI)
- **Purpose**: Message broker for task distribution
- **Credentials**: username/password
- **Persistence**: Docker volume
- **Features**: Message queuing, task distribution, monitoring

### 5. **PostgreSQL**
- **Port**: 5432
- **Purpose**: Data persistence for users, spreadsheets, and tasks
- **Persistence**: Docker volume
- **Features**: ACID compliance, connection pooling

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version

# Clone the repository
git clone https://github.com/Sukhija-Aniket/StockPortfolioManager.git
cd StockPortfolioManager
```

### 2. Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API and Google Drive API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Place it in `backend/secrets/credentials.json`

### 3. Environment Configuration
Create environment files for each component:

**Backend** (`backend/.env`):
```env
GOOGLE_CREDENTIALS_FILE=secrets/credentials.json
FRONTEND_SERVICE=localhost:3000
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/stock_portfolio
RABBITMQ_HOST=rabbitmq
RABBITMQ_USERNAME=username
RABBITMQ_PASSWORD=password
SECRET_KEY=your-secret-key-here
```

**Frontend** (`frontend/.env`):
```env
REACT_APP_BACKEND_SERVICE=localhost:5000
```

### 4. Start All Services
```bash
docker-compose up -d
```

### 5. Check Service Status
```bash
docker-compose ps
```

### 6. View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 7. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **RabbitMQ Management**: http://localhost:15672
  - Username: `username`
  - Password: `password`
- **Health Check**: http://localhost:5000/health

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration
```yaml
environment:
  - GOOGLE_CREDENTIALS_FILE=secrets/credentials.json
  - FRONTEND_SERVICE=localhost:3000
  - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/stock_portfolio
  - RABBITMQ_HOST=rabbitmq
  - SECRET_KEY=your-secret-key-here
```

#### Worker Configuration
```yaml
environment:
  - WORKER_CONCURRENCY=4    # Number of concurrent tasks
  - WORKER_TIMEOUT=300      # Task timeout in seconds
  - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/stock_portfolio
  - RABBITMQ_HOST=rabbitmq
```

#### RabbitMQ Configuration
```yaml
environment:
  - RABBITMQ_USERNAME=username
  - RABBITMQ_PASSWORD=password
```

### Broker Configuration
Broker-specific rates are configured in `worker/config/participant_config.json`:

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
  },
  "upstox": {
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

### Scaling Workers

#### Option 1: Using Docker Compose Scale
```bash
# Scale to 3 worker instances
docker-compose up -d --scale worker=3
```

#### Option 2: Using the Scale Script
```bash
# Scale to 2 workers (default)
./scale_workers.sh

# Scale to 5 workers
./scale_workers.sh 5
```

## 📊 Monitoring

### 1. **RabbitMQ Management UI**
- **URL**: http://localhost:15672
- **Features**:
  - Queue monitoring
  - Message rates
  - Connection status
  - Performance metrics
  - Task processing status

### 2. **Health Checks**
```bash
# Check backend health
curl http://localhost:5000/health

# Check all services
docker-compose ps

# Check service logs
docker-compose logs --tail=50
```

### 3. **Logs Monitoring**
```bash
# Real-time logs
docker-compose logs -f

# Worker-specific logs
docker-compose logs -f worker

# Backend-specific logs
docker-compose logs -f backend

# Error logs only
docker-compose logs --tail=100 | grep ERROR
```

### 4. **Authentication Monitoring**
```bash
# Check OAuth status
curl http://localhost:5000/auth/user

# Monitor token validation
docker-compose logs backend | grep "token"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. **Worker Not Processing Tasks**
```bash
# Check worker logs
docker-compose logs worker

# Check RabbitMQ connection
docker-compose logs rabbitmq

# Check broker configuration
docker exec -it stockportfoliomanager-worker-1 cat /app/config/participant_config.json

# Restart worker
docker-compose restart worker
```

#### 2. **OAuth Authentication Issues**
```bash
# Check OAuth credentials
docker exec -it stockportfoliomanager-backend-1 ls -la /app/secrets/

# Check backend logs for OAuth errors
docker-compose logs backend | grep -i oauth

# Verify Google API access
docker exec -it stockportfoliomanager-backend-1 python -c "from google.oauth2.credentials import Credentials; print('OAuth OK')"
```

#### 3. **RabbitMQ Connection Issues**
```bash
# Check RabbitMQ status
docker-compose ps rabbitmq

# Check RabbitMQ logs
docker-compose logs rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq
```

#### 4. **Database Connection Issues**
```bash
# Check database status
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test database connection
docker exec -it stockportfoliomanager-backend-1 python -c "import psycopg2; print('DB OK')"
```

#### 5. **High Memory Usage**
```bash
# Check resource usage
docker stats

# Scale down workers
./scale_workers.sh 2

# Check memory limits
docker-compose config | grep -A 5 -B 5 memory
```

### Performance Tuning

#### 1. **Worker Concurrency**
Adjust based on your server resources:
```yaml
environment:
  - WORKER_CONCURRENCY=8  # Increase for more CPU cores
```

#### 2. **Memory Limits**
```yaml
deploy:
  resources:
    limits:
      memory: 2G  # Increase for memory-intensive tasks
```

#### 3. **Task Timeout**
```yaml
environment:
  - WORKER_TIMEOUT=600  # Increase for long-running tasks
```

#### 4. **Database Connection Pooling**
```yaml
environment:
  - DATABASE_POOL_SIZE=20
  - DATABASE_MAX_OVERFLOW=30
```

## 🔄 Development Workflow

### 1. **Local Development**
```bash
# Start services
docker-compose up -d

# Make code changes (volumes are mounted)
# Changes are reflected immediately

# Restart specific service if needed
docker-compose restart backend
```

### 2. **Testing Changes**
```bash
# Test backend
curl http://localhost:5000/health

# Test OAuth flow
# Visit http://localhost:3000 and try logging in

# Test worker (send a test message)
# Use the backend API to trigger a task
```

### 3. **Development with Hot Reload**
```bash
# Use development configuration
docker-compose -f docker-compose.dev.yml up -d

# Changes are automatically reflected
```

### 4. **Deployment**
```bash
# Build and deploy
docker-compose up -d --build

# Scale for production
./scale_workers.sh 4

# Monitor deployment
docker-compose logs -f
```

## 📈 Production Considerations

### 1. **Security**
- Change default RabbitMQ credentials
- Use environment files for secrets
- Enable SSL/TLS for RabbitMQ
- Secure Google OAuth credentials
- Implement proper session management
- Use HTTPS in production

### 2. **Monitoring**
- Set up log aggregation (ELK stack)
- Monitor RabbitMQ metrics
- Set up alerts for failures
- Monitor OAuth token expiration
- Track API usage and performance

### 3. **Backup and Recovery**
- Regular database backups
- RabbitMQ message persistence
- Configuration file backups
- Disaster recovery procedures

### 4. **Scaling Strategy**
- Horizontal scaling for workers
- Load balancing for backend
- Database read replicas
- Message queue clustering

## 🔒 Security Best Practices

### 1. **Authentication**
- Use strong OAuth credentials
- Implement token refresh logic
- Secure session management
- Regular credential rotation

### 2. **Network Security**
- Use private Docker networks
- Implement firewall rules
- Secure inter-service communication
- Use VPN for remote access

### 3. **Data Protection**
- Encrypt sensitive data
- Implement proper access controls
- Regular security audits
- Compliance with data regulations

## 🆘 Support

For additional support:
- Check the troubleshooting section above
- Review logs for specific error messages
- Consult the MODULAR_ARCHITECTURE.md for component details
- Create an issue on GitHub with detailed error information 