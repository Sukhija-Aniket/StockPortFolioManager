# Docker Compose Setup with RabbitMQ & Async Workers

## 🚀 Overview

This setup provides a scalable, production-ready architecture using:
- **RabbitMQ**: Message broker for reliable task processing
- **Async Workers**: Concurrent task processing with configurable concurrency
- **Docker Compose**: Easy deployment and scaling
- **Health Checks**: Automatic service monitoring

## 📁 Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │   Worker    │
│   (React)   │◄──►│   (Flask)   │◄──►│   (Async)   │
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
- **Purpose**: User interface
- **Health Check**: Automatic restart on failure

### 2. **Backend** (Flask)
- **Port**: 5000
- **Purpose**: API endpoints and business logic
- **Health Check**: `/health` endpoint
- **Dependencies**: RabbitMQ, Database

### 3. **Worker** (Async Python)
- **Purpose**: Background task processing
- **Concurrency**: Configurable (default: 4 concurrent tasks)
- **Timeout**: Configurable (default: 300s)
- **Dependencies**: RabbitMQ

### 4. **RabbitMQ**
- **Ports**: 5672 (AMQP), 15672 (Management UI)
- **Purpose**: Message broker
- **Credentials**: username/password
- **Persistence**: Docker volume

## 🚀 Quick Start

### 1. Start All Services
```bash
docker-compose up -d
```

### 2. Check Service Status
```bash
docker-compose ps
```

### 3. View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker
docker-compose logs -f backend
```

### 4. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **RabbitMQ Management**: http://localhost:15672
  - Username: `username`
  - Password: `password`

## ⚙️ Configuration

### Environment Variables

#### Worker Configuration
```yaml
environment:
  - WORKER_CONCURRENCY=4    # Number of concurrent tasks
  - WORKER_TIMEOUT=300      # Task timeout in seconds
```

#### RabbitMQ Configuration
```yaml
environment:
  - RABBITMQ_USERNAME=username
  - RABBITMQ_PASSWORD=password
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

### 2. **Health Checks**
```bash
# Check backend health
curl http://localhost:5000/health

# Check all services
docker-compose ps
```

### 3. **Logs Monitoring**
```bash
# Real-time logs
docker-compose logs -f

# Worker-specific logs
docker-compose logs -f worker

# Error logs only
docker-compose logs --tail=100 | grep ERROR
```

## 🔧 Troubleshooting

### Common Issues

#### 1. **Worker Not Processing Tasks**
```bash
# Check worker logs
docker-compose logs worker

# Check RabbitMQ connection
docker-compose logs rabbitmq

# Restart worker
docker-compose restart worker
```

#### 2. **RabbitMQ Connection Issues**
```bash
# Check RabbitMQ status
docker-compose ps rabbitmq

# Check RabbitMQ logs
docker-compose logs rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq
```

#### 3. **High Memory Usage**
```bash
# Check resource usage
docker stats

# Scale down workers
./scale_workers.sh 2
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

# Test worker (send a test message)
# Use the backend API to trigger a task
```

### 3. **Deployment**
```bash
# Build and deploy
docker-compose up -d --build

# Scale for production
./scale_workers.sh 4
```

## 📈 Production Considerations

### 1. **Security**
- Change default RabbitMQ credentials
- Use environment files for secrets
- Enable SSL/TLS for RabbitMQ

### 2. **Monitoring**
- Set up log aggregation (ELK stack)
- Monitor RabbitMQ metrics
- Set up alerts for failures

### 3. **Backup**
- Backup RabbitMQ data volume
- Backup application data
- Test recovery procedures

### 4. **Scaling**
- Use multiple worker instances
- Consider horizontal scaling
- Monitor resource usage

## 🎯 Benefits of This Setup

✅ **Reliability**: RabbitMQ ensures message persistence and delivery  
✅ **Scalability**: Easy to scale workers up/down  
✅ **Monitoring**: Built-in health checks and management UI  
✅ **Development**: Hot reload with volume mounts  
✅ **Production**: Ready for deployment with proper configuration  
✅ **Async Processing**: Concurrent task handling for better performance  

This setup provides a robust foundation for your stock portfolio manager with excellent scalability and reliability! 