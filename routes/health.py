"""
<<<<<<< HEAD
Health check endpoint for monitoring and testing
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import structlog

logger = structlog.get_logger()
=======
Health check endpoints for deployment monitoring
"""

from flask import Blueprint, jsonify
import os
import sys
from datetime import datetime
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
<<<<<<< HEAD
    """Basic health check endpoint"""
    try:
        from models.models.enhanced_user import User
        
        # Test database connection
        user_count = User.query.count()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "connected": True,
                "user_count": user_count
            },
            "version": "1.0.0"
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_data = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "database": {
                "connected": False
            }
        }
        
        return jsonify(error_data), 500

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with component status"""
    try:
        from models.models.enhanced_user import User
        from models.models.enhanced_vessel import Vessel
        from app import redis_client
        
        # Test database
        user_count = User.query.count()
        vessel_count = Vessel.query.count()
        
        # Test Redis
        redis_healthy = False
        try:
            from app import app
            if app.config.get('SESSION_REDIS'):
                app.config['SESSION_REDIS'].ping()
                redis_healthy = True
        except:
            pass
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": {
                    "status": "healthy",
                    "user_count": user_count,
                    "vessel_count": vessel_count
                },
                "redis": {
                    "status": "healthy" if redis_healthy else "unhealthy",
                    "connected": redis_healthy
                },
                "authentication": {
                    "status": "healthy",
                    "csrf_enabled": True
                }
            },
            "version": "1.0.0"
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        error_data = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
        return jsonify(error_data), 500
=======
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@health_bp.route('/health/detailed')
def detailed_health():
    """Detailed health check"""
    try:
        # Check database connection
        from app import db
        db.engine.execute('SELECT 1')
        db_status = 'connected'
    except:
        db_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'python_version': sys.version,
        'environment': os.environ.get('FLASK_ENV', 'production')
    })
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
