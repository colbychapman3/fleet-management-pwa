#!/usr/bin/env python3
"""
Fleet Management System - Main Flask Application
Production-ready Flask app with PostgreSQL, Redis, PWA support, and monitoring
"""

import os
import logging
import redis
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash
from prometheus_flask_exporter import PrometheusMetrics
import structlog

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 
    'postgresql://postgres:HobokenHome3!@db.mjalobwwhnrgqqlnnbfa.supabase.co:5432/postgres')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 
    'redis://default:AXXXAAIjcDFlM2ZmOWZjNmM0MDk0MTY4OWMyNjhmNThlYjE4OGJmNnAxMA@keen-sponge-30167.upstash.io:6379')

# Session configuration for Redis
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'fleet:'
app.config['SESSION_REDIS'] = redis.from_url(app.config['REDIS_URL'])

# Security configurations
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = structlog.get_logger()

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize Redis
try:
    redis_client = redis.from_url(app.config['REDIS_URL'])
    redis_client.ping()
    logger.info("Redis connection established successfully")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['REDIS_URL'] if redis_client else "memory://"
)
limiter.init_app(app)

# Prometheus metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Custom metrics
REQUEST_COUNT = metrics.counter(
    'requests_total', 'Total requests', ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = metrics.histogram(
    'request_duration_seconds', 'Request latency', ['method', 'endpoint']
)
ACTIVE_USERS = metrics.gauge(
    'active_users_total', 'Number of active users'
)
DATABASE_CONNECTIONS = metrics.gauge(
    'database_connections_active', 'Active database connections'
)

# Import models after db initialization
from app.models.user import User
from app.models.vessel import Vessel
from app.models.task import Task
from app.models.sync_log import SyncLog

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes
from app.routes.auth import auth_bp
from app.routes.api import api_bp
from app.routes.dashboard import dashboard_bp
from app.routes.monitoring import monitoring_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(monitoring_bp, url_prefix='/monitoring')

# Cache helper functions
def get_cache_key(prefix, *args):
    """Generate cache key with prefix and arguments"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def cache_get(key, default=None):
    """Get value from Redis cache"""
    if not redis_client:
        return default
    try:
        value = redis_client.get(key)
        return value.decode('utf-8') if value else default
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")
        return default

def cache_set(key, value, timeout=300):
    """Set value in Redis cache with timeout"""
    if not redis_client:
        return False
    try:
        return redis_client.setex(key, timeout, str(value))
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")
        return False

def cache_delete(key):
    """Delete key from Redis cache"""
    if not redis_client:
        return False
    try:
        return redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Cache delete failed for key {key}: {e}")
        return False

# Main routes
@app.route('/')
def index():
    """Main landing page with PWA manifest"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.main'))
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    """PWA Web App Manifest"""
    manifest_data = {
        "name": "Fleet Management System",
        "short_name": "FleetMS",
        "description": "Offline-capable fleet and task management for maritime operations",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#2196F3",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/icons/icon-72x72.png",
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/icons/icon-96x96.png",
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/icons/icon-128x128.png",
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/icons/icon-144x144.png",
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/icons/icon-152x152.png",
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/icons/icon-384x384.png",
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": "/static/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable any"
            }
        ],
        "categories": ["productivity", "business"],
        "screenshots": [
            {
                "src": "/static/screenshots/desktop-1.png",
                "sizes": "1280x720",
                "type": "image/png",
                "form_factor": "wide"
            },
            {
                "src": "/static/screenshots/mobile-1.png",
                "sizes": "375x667",
                "type": "image/png",
                "form_factor": "narrow"
            }
        ]
    }
    
    response = make_response(jsonify(manifest_data))
    response.headers['Content-Type'] = 'application/manifest+json'
    return response

@app.route('/service-worker.js')
def service_worker():
    """Serve the service worker file"""
    response = make_response(render_template('service-worker.js'))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html')

# Health check endpoints
@app.route('/health')
def health_check():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/health/detailed')
def health_detailed():
    """Detailed health check with dependencies"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'dependencies': {}
    }
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        health_status['dependencies']['database'] = {'status': 'healthy'}
    except Exception as e:
        health_status['dependencies']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        if redis_client:
            redis_client.ping()
            health_status['dependencies']['redis'] = {'status': 'healthy'}
        else:
            health_status['dependencies']['redis'] = {'status': 'unavailable'}
    except Exception as e:
        health_status['dependencies']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    return jsonify(health_status)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limiting"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Rate limit exceeded', 'retry_after': e.retry_after}), 429
    return render_template('errors/429.html'), 429

# Request hooks for metrics
@app.before_request
def before_request():
    """Track request start time for metrics"""
    request.start_time = datetime.utcnow()

@app.after_request
def after_request(response):
    """Track request metrics"""
    if hasattr(request, 'start_time'):
        duration = (datetime.utcnow() - request.start_time).total_seconds()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# CLI commands
@app.cli.command()
def init_db():
    """Initialize the database with tables and sample data"""
    db.create_all()
    
    # Create sample data
    if not User.query.filter_by(email='admin@fleet.com').first():
        admin = User(
            email='admin@fleet.com',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='manager',
            is_active=True
        )
        db.session.add(admin)
    
    if not User.query.filter_by(email='worker@fleet.com').first():
        worker = User(
            email='worker@fleet.com',
            username='worker',
            password_hash=generate_password_hash('worker123'),
            role='worker',
            is_active=True
        )
        db.session.add(worker)
    
    db.session.commit()
    print("Database initialized successfully!")

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )