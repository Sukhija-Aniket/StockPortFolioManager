# Stock Portfolio Manager

A comprehensive stock portfolio management system with real-time data processing, broker-specific calculations, and Google Sheets integration. Built with a modern microservices architecture supporting distributed deployment.

## 🚀 Features

### Core Functionality
- **📊 Portfolio Management**: Import and manage stock data from Excel sheets or Google Sheets
- **💰 Real-time Analytics**: Calculate profits, losses, and portfolio metrics with live stock prices
- **🏦 Broker-Specific Calculations**: Support for major Indian brokers (Zerodha, Upstox, etc.) with configurable rates
- **📈 Advanced Analytics**: 
  - Share Profit/Loss analysis
  - Daily Profit/Loss tracking
  - Taxation reports (LTCG, STCG, Intraday)
  - FIFO-based cost basis calculations

### Technical Features
- **🔐 Google OAuth Authentication**: Secure login with Google accounts
- **🔄 Asynchronous Processing**: Background task processing with RabbitMQ
- **📱 Modern Web Interface**: React-based responsive frontend
- **🔧 Microservices Architecture**: Independent frontend, backend, and worker components
- **🐳 Docker Support**: Easy deployment with Docker Compose
- **📊 Database Integration**: PostgreSQL for data persistence

### Broker Support
- **Zerodha**: Full support with configurable rates
- **Groww**: Full support with configurable rates

### Upcoming Brokers
- **Upstox**: Full support with configurable rates
- **Angel One**: Full support with configurable rates
- **ICICI Direct**: Full support with configurable rates
- **HDFC Securities**: Full support with configurable rates
- **Kotak Securities**: Full support with configurable rates
- **Axis Direct**: Full support with configurable rates
- **SBI Securities**: Full support with configurable rates
- **5Paisa**: Full support with configurable rates


## 🏗️ Architecture

The system is built with a modular microservices architecture:

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

### Components
- **Frontend**: React application with modern UI
- **Backend**: Flask API with Google OAuth integration
- **Worker**: Asynchronous task processor for data calculations
- **Shared Library**: Common utilities and models
- **Database**: PostgreSQL for data persistence
- **Message Queue**: RabbitMQ for task distribution

## 🛠️ Prerequisites

- **Docker & Docker Compose**: For containerized deployment
- **Node.js 18+**: For frontend development
- **Python 3.8+**: For backend and worker development
- **Google Cloud Project**: For OAuth and Google Sheets API access

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Sukhija-Aniket/StockPortfolioManager.git
cd StockPortfolioManager
```

### 2. Set Up Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API and Google Drive API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Place it in `backend/secrets/credentials.json`

### 3. Configure Environment
Create `.env` files in each component directory:

**Backend** (`backend/.env`):
```env
GOOGLE_CREDENTIALS_FILE=secrets/credentials.json
FRONTEND_SERVICE=localhost:3000
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/stock_portfolio
```

**Frontend** (`frontend/.env`):
```env
REACT_APP_BACKEND_SERVICE=localhost:5000
```

### 4. Start the Application
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 5. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **RabbitMQ Management**: http://localhost:15672

## 📖 Usage Guide

### 1. Authentication
- Click "Login with Google" on the frontend
- Grant necessary permissions for Google Sheets access
- Your session will be maintained securely

### 2. Creating Spreadsheets
- Click "Create New Spreadsheet"
- Select your broker from the dropdown
- The system will create a Google Sheet with proper structure

### 3. Adding Data
- Upload CSV files with your transaction data
- Select the target spreadsheet
- Data will be processed asynchronously with broker-specific calculations

### 4. Syncing Data
- Click "Sync All Data" to process all spreadsheets
- Monitor progress in the RabbitMQ management interface
- Results will be available in your Google Sheets

## 🔧 Configuration

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
  }
}
```

### Worker Configuration
Adjust worker concurrency and timeouts:

```bash
# Scale workers
./scale_workers.sh 4

# Environment variables
WORKER_CONCURRENCY=4
WORKER_TIMEOUT=300
```

## 🐳 Docker Deployment

### Production Deployment
```bash
# Build and start all services
docker-compose up -d --build

# Scale workers for production
./scale_workers.sh 4

# Monitor services
docker-compose logs -f
```

### Development Deployment
```bash
# Use development configuration
docker-compose -f docker-compose.dev.yml up -d
```

## 📊 Monitoring

### Health Checks
- **Backend**: `GET /health`
- **Worker**: RabbitMQ connection status
- **Database**: PostgreSQL readiness

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f worker
docker-compose logs -f backend
```

### RabbitMQ Management
- **URL**: http://localhost:15672
- **Username**: `username`
- **Password**: `password`

## 🔒 Security

- **OAuth 2.0 Authentication**: Secure Google account integration
- **Session Management**: Secure session handling with Flask
- **Token Validation**: Automatic token refresh and validation
- **Environment Variables**: Secure configuration management
- **Docker Security**: Containerized deployment with proper isolation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Run tests: `docker-compose -f docker-compose.dev.yml up --build`
5. Commit your changes: `git commit -m 'Add new feature'`
6. Push to the branch: `git push origin feature/new-feature`
7. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `/docs` folder
- Review the troubleshooting guide in `DOCKER_SETUP.md`
