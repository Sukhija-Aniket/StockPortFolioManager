# Stock Portfolio Manager - Frontend

A modern React-based frontend for the Stock Portfolio Manager system, featuring Google OAuth authentication, spreadsheet management, and real-time data processing.

## 🚀 Features

- **🔐 Google OAuth Authentication**: Secure login with Google accounts
- **📊 Spreadsheet Management**: Create and manage Google Sheets for portfolio data
- **📁 File Upload**: Upload CSV files with transaction data
- **🔄 Data Sync**: Trigger asynchronous data processing
- **📱 Responsive Design**: Modern UI with Bootstrap components
- **⚡ Real-time Updates**: Live status updates and notifications

## 🛠️ Prerequisites

- **Node.js 18+**: Required for React development
- **npm or yarn**: Package manager
- **Backend Service**: Running Stock Portfolio Manager backend
- **Google OAuth**: Configured Google Cloud project with OAuth credentials

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Environment Configuration
Create a `.env` file in the frontend directory:
```env
REACT_APP_BACKEND_SERVICE=localhost:5000
```

### 3. Start Development Server
```bash
npm start
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/         # React components
│   │   ├── FileUploader.js # File upload component
│   │   ├── Login.js        # OAuth login component
│   │   └── SpreadsheetManager.js # Spreadsheet management
│   ├── services/           # API services
│   │   ├── api.js          # API utilities
│   │   └── auth.js         # Authentication utilities
│   ├── utils/              # Utility functions
│   ├── App.js              # Main application component
│   └── index.js            # Application entry point
├── package.json            # Dependencies and scripts
└── Dockerfile              # Docker configuration
```

## 🔧 Available Scripts

### `npm start`
Runs the app in development mode with hot reloading.

### `npm test`
Launches the test runner in interactive watch mode.

### `npm run build`
Builds the app for production to the `build` folder.

### `npm run eject`
**Note: This is a one-way operation!**

Ejects from Create React App to get full control over configuration.

## 🔐 Authentication

The frontend integrates with Google OAuth 2.0 for secure authentication:

1. **Login Flow**: Users click "Login with Google" to authenticate
2. **OAuth Redirect**: Redirects to Google for authentication
3. **Session Management**: Backend handles session creation and management
4. **Token Validation**: Automatic token validation and refresh

## 📊 API Integration

The frontend communicates with the backend API for:

- **Authentication**: OAuth flow and session management
- **Spreadsheet Management**: Create, list, and manage Google Sheets
- **File Upload**: Upload CSV files for processing
- **Data Sync**: Trigger background data processing
- **Status Monitoring**: Check processing status and results

## 🐳 Docker Deployment

### Development
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.dev.yml up frontend
```

### Production
```bash
# Build production image
docker build -t stock-portfolio-frontend .

# Run with environment variables
docker run -d \
  -e REACT_APP_BACKEND_SERVICE=backend:5000 \
  -p 3000:3000 \
  stock-portfolio-frontend
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_BACKEND_SERVICE` | Backend API URL | `localhost:5000` |

### Build Configuration

The application uses Create React App's default configuration with:

- **Babel**: ES6+ transpilation
- **Webpack**: Module bundling
- **ESLint**: Code linting
- **Jest**: Unit testing

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in CI mode
npm test -- --watchAll=false
```

## 📦 Build and Deployment

### Production Build
```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

### Static Deployment
The built application can be deployed to any static hosting service:

- **Netlify**: Drag and drop the `build/` folder
- **Vercel**: Connect repository for automatic deployments
- **AWS S3**: Upload to S3 bucket with CloudFront
- **Nginx**: Serve static files from nginx server

### Docker Deployment
```bash
# Build production image
docker build -t stock-portfolio-frontend .

# Run container
docker run -d -p 3000:3000 stock-portfolio-frontend
```

## 🔒 Security Considerations

- **HTTPS**: Always use HTTPS in production
- **Environment Variables**: Never commit sensitive data to version control
- **CORS**: Backend must be configured to allow frontend origin
- **OAuth**: Secure OAuth flow with proper redirect URIs

## 🐛 Troubleshooting

### Common Issues

1. **Backend Connection Error**
   - Verify backend service is running
   - Check `REACT_APP_BACKEND_SERVICE` environment variable
   - Ensure CORS is configured on backend

2. **OAuth Authentication Issues**
   - Verify Google OAuth credentials are configured
   - Check redirect URIs in Google Cloud Console
   - Ensure backend OAuth endpoints are working

3. **Build Failures**
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check for syntax errors in React components
   - Verify all dependencies are compatible

### Debug Commands
```bash
# Check Node.js version
node --version

# Check npm version
npm --version

# Clear npm cache
npm cache clean --force

# Check for outdated packages
npm outdated
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Run tests: `npm test`
5. Commit your changes: `git commit -m 'Add new feature'`
6. Push to the branch: `git push origin feature/new-feature`
7. Create a Pull Request

## 📚 Additional Resources

- [React Documentation](https://reactjs.org/)
- [Create React App Documentation](https://facebook.github.io/create-react-app/)
- [Bootstrap Documentation](https://getbootstrap.com/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
