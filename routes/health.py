"""
Health check endpoints for deployment monitoring
"""

from flask import Blueprint, jsonify
import os
import sys
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
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
