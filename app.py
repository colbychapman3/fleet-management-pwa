#!/usr/bin/env python3
"""
Fleet Management System - Main Flask Application
Production-ready Flask app with PostgreSQL, Redis, PWA support, and monitoring
"""

import os
import logging
try:
    import redis
except ImportError:
    redis = None
    # Redis not available - will log later
import sys # Added import for sys
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response, flash
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
# IMPORTANT: Change this to a strong, randomly generated key in production!
# Use `os.urandom(24)` to generate a good secret key.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'YOUR_SUPER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION')

# Database URL - PostgreSQL is primary
# Use environment variable if available, otherwise default to Supabase URL
database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:HobokenHome3!@db.mjalobwwhnrgqqlnnbfa.supabase.co:5432/postgres')

# Fallback to SQLite for development if PostgreSQL is not available
if not database_url or database_url == 'sqlite:///fleet_management.db':
    database_url = 'postgresql://postgres:HobokenHome3!@db.mjalobwwhnrgqqlnnbfa.supabase.co:5432/postgres'

# Fix Render's postgres:// to postgresql:// if needed
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
# Database URL will be logged after structlog is configured

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# PostgreSQL engine options
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': 300,
    'pool_pre_ping': True,
    'connect_args': {
        'application_name': 'fleet_management_pwa'
    }
}

# Redis URL configuration: Use local Redis if FLASK_ENV is development, otherwise use external Upstash
if os.environ.get('FLASK_ENV') == 'development':
    app.config['REDIS_URL'] = 'redis://redis-local:6379/0' # Use the service name from docker-compose
    redis_env = 'local'
else:
    app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 
        'rediss://default:AXXXAAIjcDFlM2ZmOWZjNmM0MDk0MTY4OWMyNjhmNThlYjE4OGJmNnAxMA@keen-sponge-30167.upstash.io:6380')
    redis_env = 'external'

# Logging configuration
# Configure structlog for better structured logging
# Use environment variable to determine if we're in debug mode
is_debug = os.environ.get('FLASK_ENV') == 'development'

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard logging to use structlog
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

logger = structlog.get_logger()

# Log configuration after structlog is set up
if not redis:
    logger.warning("Redis not available - using fallback configuration")
logger.info(f"Using PostgreSQL database: {database_url.split('@')[1] if '@' in database_url else database_url}")
logger.info(f"Using {redis_env} Redis configuration")

# Session configuration for Redis
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'fleet:'
# Initialize Redis client after setting REDIS_URL
try:
    app.config['SESSION_REDIS'] = redis.from_url(app.config['REDIS_URL'])
    app.config['SESSION_REDIS'].ping()
    logger.info("Redis connection established successfully")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    app.config['SESSION_REDIS'] = None # Ensure it's None if connection fails

# Security configurations
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Add request and user context to logs
@app.before_request
def add_request_context_to_logger():
    if request:
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.path,
            ip_address=request.remote_addr,
            user_id=getattr(current_user, 'id', 'anonymous')
        )

@app.after_request
def clear_request_context_from_logger(response):
    structlog.contextvars.clear_contextvars()
    return response

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize Redis (moved this block to be after REDIS_URL is set)
# try:
#     redis_client = redis.from_url(app.config['REDIS_URL'])
#     redis_client.ping()
#     logger.info("Redis connection established successfully")
# except Exception as e:
#     logger.error(f"Redis connection failed: {e}")
#     redis_client = None
# The redis_client is now directly accessed via app.config['SESSION_REDIS']

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "200 per hour", "50 per minute"],
    storage_uri=app.config['REDIS_URL'] if app.config['SESSION_REDIS'] else "memory://" # Use SESSION_REDIS for storage_uri
)
limiter.init_app(app)

# Import models after db initialization
from models.models.user import User
from models.models.enhanced_vessel import Vessel
from models.models.enhanced_task import Task
from models.models.sync_log import SyncLog
from models.models.berth import Berth
from models.maritime.ship_operation import ShipOperation
from models.maritime.stevedore_team import StevedoreTeam
from models.models.operation_assignment import OperationAssignment
from models.models.equipment_assignment import EquipmentAssignment
from models.models.work_time_log import WorkTimeLog
from models.models.cargo_batch import CargoBatch

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Cache helper functions
def get_cache_key(prefix, *args):
    """Generate cache key with prefix and arguments"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def cache_get(key, default=None):
    """Get value from Redis cache"""
    if not app.config['SESSION_REDIS']: # Use SESSION_REDIS
        return default
    try:
        value = app.config['SESSION_REDIS'].get(key) # Use SESSION_REDIS
        return value.decode('utf-8') if value else default
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")
        return default

def cache_set(key, value, timeout=300):
    """Set value in Redis cache with timeout"""
    if not app.config['SESSION_REDIS']: # Use SESSION_REDIS
        return False
    try:
        return app.config['SESSION_REDIS'].setex(key, timeout, str(value)) # Use SESSION_REDIS
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")
        return False

def cache_delete(key):
    """Delete key from Redis cache"""
    if not app.config['SESSION_REDIS']: # Use SESSION_REDIS
        return False
    try:
        return app.config['SESSION_REDIS'].delete(key) # Use SESSION_REDIS
    except Exception as e:
        logger.warning(f"Cache delete failed for key {key}: {e}")
        return False

# Main routes
@app.route('/')
def index():
    """Main landing page with PWA manifest"""
    # Try to initialize database on first request if not already done
    try:
        User.query.first()  # Test database connection
    except Exception as e:
        logger.info(f"Database not initialized, attempting to initialize now: {e}")
        if not init_database():
            # If database init fails, still show the page but with a message
            flash('Database connection unavailable. Some features may not work.', 'error')
    
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

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return redirect(url_for('static', filename='favicon.ico'))

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
        if app.config['SESSION_REDIS']: # Use SESSION_REDIS
            app.config['SESSION_REDIS'].ping() # Use SESSION_REDIS
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
    db.session.rollback() # Ensure any pending transactions are rolled back
    logger.error(f"Internal server error: {error}") # Log the error
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500 # Redirect to generic 500 page

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limiting"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Rate limit exceeded', 'retry_after': e.retry_after}), 429
    return render_template('errors/429.html'), 429

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Handle all unexpected errors"""
    db.session.rollback() # Ensure any pending transactions are rolled back
    logger.exception(f"An unexpected error occurred: {e}") # Log the full exception traceback
    
    if request.path.startswith('/api/'):
        return jsonify({'error': 'An unexpected server error occurred'}), 500
    return render_template('errors/500.html'), 500 # Redirect to generic 500 page

# Request hooks for security headers
@app.before_request
def enforce_https():
    """Redirect HTTP requests to HTTPS in production"""
    # Check if running in a production-like environment and if proto is http
    if os.environ.get('FLASK_ENV') == 'production' and request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

@app.after_request
def after_request(response):
    """Add security headers"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # HSTS header: max-age in seconds (1 year), includeSubDomains
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# Database initialization helper
def init_database():
    """Initialize database tables and sample data if needed"""
    try:
        with app.app_context():
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
            
            # Create default berths if they don't exist
            if not Berth.query.first():
                berths = [
                    Berth(berth_number='B01', berth_name='Berth 1 - Container Terminal', berth_type='Container', 
                          length_meters=250.0, depth_meters=12.0, max_draft=11.0, max_loa=240.0, 
                          status='active', hourly_rate=50.00, daily_rate=1000.00),
                    Berth(berth_number='B02', berth_name='Berth 2 - RoRo Terminal', berth_type='RoRo', 
                          length_meters=200.0, depth_meters=8.0, max_draft=7.5, max_loa=190.0, 
                          status='active', hourly_rate=40.00, daily_rate=800.00),
                    Berth(berth_number='B03', berth_name='Berth 3 - General Cargo', berth_type='General Cargo', 
                          length_meters=180.0, depth_meters=10.0, max_draft=9.0, max_loa=170.0, 
                          status='active', hourly_rate=35.00, daily_rate=700.00),
                    Berth(berth_number='B04', berth_name='Berth 4 - Multi-Purpose', berth_type='Multi-Purpose', 
                          length_meters=220.0, depth_meters=11.0, max_draft=10.0, max_loa=210.0, 
                          status='active', hourly_rate=45.00, daily_rate=900.00),
                    Berth(berth_number='B05', berth_name='Berth 5 - Heavy Lift', berth_type='Heavy Lift', 
                          length_meters=160.0, depth_meters=15.0, max_draft=14.0, max_loa=150.0, 
                          status='active', hourly_rate=60.00, daily_rate=1200.00)
                ]
                for berth in berths:
                    db.session.add(berth)
            
            db.session.commit()
            logger.info("Database initialized successfully!")
            return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

# CLI commands
@app.cli.command()
def init_db():
    """Initialize the database with tables and sample data"""
    if init_database():
        logger.info("Database initialized successfully!")
    else:
        logger.error("Database initialization failed!")

# Import and register blueprints after all app setup is complete
from routes.auth import auth_bp
from routes.health import health_bp
from routes.api import api_bp
from routes.dashboard import dashboard_bp
from routes.monitoring import monitoring_bp
from routes.maritime.ship_operations import maritime_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(health_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(monitoring_bp, url_prefix='/monitoring')
app.register_blueprint(maritime_bp, url_prefix='/maritime')

# Initialize Prometheus metrics after all blueprints are registered
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
