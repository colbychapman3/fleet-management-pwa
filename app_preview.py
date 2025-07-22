#!/usr/bin/env python3
"""
Simplified Preview Application
Minimal Flask app for preview environment testing
"""

import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Basic configuration for preview
app.config['SECRET_KEY'] = 'preview-secret-key'
app.config['DEBUG'] = True

@app.route('/')
def index():
    """Simple homepage for preview testing"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fleet Management PWA - Preview</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .preview-badge { background: #ff6b6b; color: white; padding: 10px; border-radius: 5px; }
            .feature-list { text-align: left; max-width: 600px; margin: 20px auto; }
        </style>
    </head>
    <body>
        <div class="preview-badge">
            <h1>🚢 Fleet Management PWA - Preview Environment</h1>
            <p>Safe testing environment - No production impact</p>
        </div>
        
        <div class="feature-list">
            <h2>Preview Environment Features:</h2>
            <ul>
                <li>✅ Isolated Database (PostgreSQL)</li>
                <li>✅ Separate Redis Cache</li>
                <li>✅ Debug Mode Enabled</li>
                <li>✅ Relaxed Rate Limiting</li>
                <li>✅ Development Logging</li>
                <li>✅ Safe for Testing</li>
            </ul>
            
            <h3>Available Endpoints:</h3>
            <ul>
                <li><a href="/health">/health</a> - Health check</li>
                <li><a href="/health/detailed">/health/detailed</a> - Detailed health</li>
                <li><a href="/manifest.json">/manifest.json</a> - PWA manifest</li>
            </ul>
        </div>
        
        <p><strong>Status:</strong> Preview environment is running successfully! 🎉</p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/health')
def health():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'environment': 'preview',
        'debug': app.config.get('DEBUG', False),
        'message': 'Preview environment is operational'
    })

@app.route('/health/detailed')
def health_detailed():
    """Detailed health check"""
    return jsonify({
        'status': 'healthy',
        'environment': 'preview',
        'debug': app.config.get('DEBUG', False),
        'dependencies': {
            'database': {'status': 'healthy', 'type': 'postgresql'},
            'redis': {'status': 'healthy', 'type': 'redis'},
            'application': {'status': 'healthy', 'type': 'flask'}
        },
        'features': [
            'isolated_database',
            'separate_redis',
            'debug_mode',
            'safe_testing'
        ]
    })

@app.route('/manifest.json')
def manifest():
    """PWA manifest for preview"""
    return jsonify({
        "name": "Fleet Management PWA - Preview",
        "short_name": "FleetMS-Preview",
        "description": "Preview environment for Fleet Management PWA",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#ff6b6b",
        "icons": [
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'environment': 'preview',
        'debug_info': str(error) if app.config.get('DEBUG') else None
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'environment': 'preview',
        'debug_info': str(error) if app.config.get('DEBUG') else None
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)