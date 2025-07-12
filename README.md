# Fleet Management System

A comprehensive, offline-capable Progressive Web Application (PWA) designed for maritime fleet operations. Built with Flask, PostgreSQL, Redis, and featuring robust offline functionality for ships with limited internet connectivity.

## 🚢 Features

### Core Functionality
- **Task Management**: Create, assign, track, and complete maintenance and operational tasks
- **Fleet Management**: Manage vessels, crew assignments, and maritime operations
- **User Management**: Role-based access control (Manager/Worker)
- **Real-time Dashboard**: Monitor fleet status, task completion, and performance metrics

### Offline-First Design
- **100% Offline Capability**: Works completely without internet connection
- **Auto-Sync**: Automatically synchronizes data when connection is restored
- **IndexedDB Storage**: Local data storage for offline operations
- **Service Worker**: Advanced caching strategies for optimal performance
- **Background Sync**: Queues operations for sync when connection returns

### Progressive Web App (PWA)
- **Installable**: Install on mobile and desktop devices
- **Responsive Design**: Mobile-first, works on all screen sizes
- **Push Notifications**: Real-time alerts for urgent tasks
- **App Shell Architecture**: Fast loading and smooth navigation

### Monitoring & Analytics
- **Prometheus Metrics**: Comprehensive application monitoring
- **Health Checks**: System status and dependency monitoring
- **Performance Tracking**: Task completion rates and efficiency metrics
- **Grafana Dashboard**: Visual monitoring and alerting

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   Data Layer    │
│                 │    │                  │    │                 │
│ • PWA/SPA       │◄──►│ • Flask API      │◄──►│ • PostgreSQL    │
│ • Service Worker│    │ • Authentication │    │ • Redis Cache   │
│ • IndexedDB     │    │ • Task Management│    │ • File Storage  │
│ • Offline Sync  │    │ • Monitoring     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Monitoring     │
                       │                  │
                       │ • Prometheus     │
                       │ • Grafana        │
                       │ • Health Checks  │
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd flask-stack-complete
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings (database URLs are pre-configured)
nano .env
```

### 3. Start the Application
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Initialize Database
```bash
# Initialize database with sample data
docker-compose exec app python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Or use the CLI command
docker-compose exec app flask init-db
```

### 5. Access the Application
- **Main App**: http://localhost:5000
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9091

### 6. Demo Login
- **Manager**: admin@fleet.com / admin123
- **Worker**: worker@fleet.com / worker123

## 📱 PWA Installation

### Mobile Devices (iOS/Android)
1. Open the app in your mobile browser
2. Look for "Add to Home Screen" or "Install" prompt
3. Follow the installation prompts
4. The app will appear as a native app on your device

### Desktop (Chrome/Edge/Firefox)
1. Open the app in your browser
2. Look for the install icon in the address bar
3. Click "Install" to add to your desktop
4. The app will open in its own window

## 🔧 Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1
export DATABASE_URL="postgresql://postgres:HobokenHome3!@db.mjalobwwhnrgqqlnnbfa.supabase.co:5432/postgres"
export REDIS_URL="redis://default:AXXXAAIjcDFlM2ZmOWZjNmM0MDk0MTY4OWMyNjhmNThlYjE4OGJmNnAxMA@keen-sponge-30167.upstash.io:6379"

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the application
python app.py
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-flask coverage

# Run tests
pytest

# Run with coverage
coverage run -m pytest
coverage report
coverage html
```

### Database Migrations
```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

## 🔍 Monitoring

### Health Checks
- **Basic**: `/health`
- **Detailed**: `/health/detailed`
- **Prometheus Metrics**: `/monitoring/metrics/prometheus`

### Key Metrics
- Task completion rates
- User activity and sync status
- System performance (CPU, memory, disk)
- Database connection pool status
- Redis cache performance
- API response times

### Grafana Dashboards
Pre-configured dashboards for:
- Application Overview
- Task Management Metrics
- User Activity
- System Performance
- Offline Sync Status

## 🚢 Maritime-Specific Features

### Offline Operations
Perfect for ships with limited or intermittent internet:
- Complete task management offline
- Local data storage and synchronization
- Conflict resolution for concurrent edits
- Queue-based sync with retry logic

### Fleet Management
- Vessel information and specifications
- Crew assignment and management
- Port-to-port tracking
- Maintenance scheduling

### Compliance Ready
- Audit logs for all operations
- Role-based access control
- Data retention policies
- Export capabilities for reporting

## 🔒 Security

### Authentication & Authorization
- Secure password hashing (bcrypt)
- Session management with Redis
- CSRF protection
- Rate limiting

### Data Protection
- SQL injection prevention
- XSS protection
- Secure headers
- Input validation and sanitization

### API Security
- JWT token authentication
- API rate limiting
- Request validation
- Error handling without information leakage

## 📊 Performance

### Optimization Features
- Redis caching layer
- Database query optimization
- CDN-ready static assets
- Gzip compression
- Service Worker caching

### Scalability
- Horizontal scaling support
- Load balancer ready
- Database connection pooling
- Stateless application design

## 🚀 Deployment

### Production Deployment

#### Using Docker (Recommended)
```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale application
docker-compose up -d --scale app=3
```

#### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt gunicorn

# Set production environment variables
export FLASK_ENV=production
export SECRET_KEY="your-production-secret-key"

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### Environment Variables
See `.env.example` for all configuration options.

### Database Setup
The application is pre-configured to use the provided PostgreSQL and Redis instances. For production, consider:
- Setting up your own PostgreSQL database
- Configuring Redis for persistence
- Setting up database backups
- Monitoring database performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

#### PWA Not Installing
- Ensure HTTPS is enabled (required for PWA)
- Check that all required PWA files are accessible
- Verify Service Worker registration

#### Offline Sync Issues
- Check browser console for errors
- Verify IndexedDB is working
- Ensure Service Worker is properly registered

#### Database Connection Issues
- Verify database URL is correct
- Check network connectivity
- Ensure database server is running

### Getting Help
- Check the [Issues](../../issues) page
- Review [Documentation](./docs/)
- Contact support: support@yourcompany.com

## 🗺️ Roadmap

### Upcoming Features
- [ ] Real-time chat/messaging
- [ ] Advanced reporting and analytics
- [ ] Mobile app (React Native)
- [ ] Integration with maritime APIs
- [ ] Advanced workflow automation
- [ ] Multi-language support

### Version History
- **v1.0.0** - Initial release with core PWA features
- **v1.1.0** - Enhanced offline capabilities
- **v1.2.0** - Advanced monitoring and metrics

---

**Built for Maritime Excellence** ⚓

This Fleet Management System is specifically designed for the challenging connectivity environments of maritime operations, ensuring your fleet management continues seamlessly whether you're in port or in the middle of the ocean.