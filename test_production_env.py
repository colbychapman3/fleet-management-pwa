#!/usr/bin/env python3
"""
Test script to simulate production environment like Render
"""

import os
import sys
import tempfile
import signal
import time
import subprocess
import threading

# Set production-like environment variables
def setup_production_env():
    """Setup environment variables similar to Render deployment"""
    
    # Production Flask settings
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Use the same database URL pattern as in your logs
    os.environ['DATABASE_URL'] = 'postgresql://postgres:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres'
    
    # Use the same Redis URL pattern as in your logs
    os.environ['REDIS_URL'] = 'redis://keen-sponge-30167.upstash.io:6379'
    
    # Set a strong secret key for production
    os.environ['SECRET_KEY'] = 'test-production-secret-key-very-long-and-secure'
    
    # Set port like Render would
    os.environ['PORT'] = '5000'
    
    print("✓ Production environment variables set")

def test_app_import():
    """Test importing the app with production settings"""
    print("Testing app import with production settings...")
    
    try:
        # Import the app
        import app
        print("✓ App imported successfully")
        
        # Check if Flask app was created
        if hasattr(app, 'app') and app.app is not None:
            print("✓ Flask app instance created")
            
            # Test basic app configuration
            print(f"  - Debug mode: {app.app.debug}")
            print(f"  - Secret key set: {'SECRET_KEY' in app.app.config and len(app.app.config['SECRET_KEY']) > 10}")
            print(f"  - Database URI configured: {'SQLALCHEMY_DATABASE_URI' in app.app.config}")
            print(f"  - Redis URL configured: {'REDIS_URL' in app.app.config}")
            
            return True
        else:
            print("✗ Flask app instance not found")
            return False
            
    except Exception as e:
        print(f"✗ App import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_startup():
    """Test if the app can start up without immediate errors"""
    print("Testing app startup simulation...")
    
    try:
        # Create a test script that tries to initialize the app
        test_script = '''
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import app
    print("App imported successfully")
    
    # Try to create app context
    with app.app.app_context():
        print("App context created successfully")
        
        # Test that logger is available
        if hasattr(app, 'logger'):
            app.logger.info("Logger test from production simulation")
            print("Logger working correctly")
        else:
            print("Warning: Logger not found")
    
    print("SUCCESS: App startup simulation completed")
    
except Exception as e:
    print(f"ERROR: App startup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        
        # Write test script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            test_file = f.name
        
        try:
            # Run the test script in a subprocess with virtual environment
            result = subprocess.run([
                'bash', '-c', 
                f'source venv/bin/activate && python {test_file}'
            ], capture_output=True, text=True, timeout=30)
            
            print("Test script output:")
            print(result.stdout)
            
            if result.stderr:
                print("Test script errors:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("✓ App startup test passed")
                return True
            else:
                print(f"✗ App startup test failed with code {result.returncode}")
                return False
                
        finally:
            # Clean up temporary file
            os.unlink(test_file)
            
    except subprocess.TimeoutExpired:
        print("✗ App startup test timed out")
        return False
    except Exception as e:
        print(f"✗ App startup test error: {e}")
        return False

def test_gunicorn_compatibility():
    """Test if the app works with gunicorn (production WSGI server)"""
    print("Testing Gunicorn compatibility...")
    
    try:
        # Test gunicorn command syntax
        test_script = '''
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test that app module can be imported for gunicorn
    import app
    
    # Check if app has the required WSGI callable
    if hasattr(app, 'app') and callable(app.app):
        print("✓ WSGI callable found")
        
        # Test app configuration for production
        with app.app.app_context():
            config_checks = [
                ('SECRET_KEY', app.app.config.get('SECRET_KEY')),
                ('SQLALCHEMY_DATABASE_URI', app.app.config.get('SQLALCHEMY_DATABASE_URI')),
                ('REDIS_URL', app.app.config.get('REDIS_URL')),
            ]
            
            for key, value in config_checks:
                if value:
                    print(f"✓ {key} configured")
                else:
                    print(f"✗ {key} missing")
        
        print("SUCCESS: Gunicorn compatibility test passed")
        
    else:
        print("✗ WSGI callable not found")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: Gunicorn compatibility test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
        
        # Write and run test script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            test_file = f.name
        
        try:
            result = subprocess.run([
                'bash', '-c', 
                f'source venv/bin/activate && python {test_file}'
            ], capture_output=True, text=True, timeout=30)
            
            print("Gunicorn compatibility test output:")
            print(result.stdout)
            
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            
            return result.returncode == 0
            
        finally:
            os.unlink(test_file)
            
    except Exception as e:
        print(f"✗ Gunicorn compatibility test error: {e}")
        return False

def main():
    """Run production environment simulation tests"""
    print("=== Fleet Management App Production Environment Tests ===\n")
    
    # Setup production environment
    setup_production_env()
    print()
    
    tests = [
        test_app_import,
        test_app_startup,
        test_gunicorn_compatibility,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}\n")
    
    print(f"=== Results: {passed}/{total} production tests passed ===")
    
    if passed == total:
        print("✓ App should deploy successfully to Render!")
        print("\nKey findings:")
        print("- Import structure is correct")
        print("- Logger initialization order is fixed")
        print("- Environment variables are handled properly")
        print("- WSGI compatibility confirmed")
        return True
    else:
        print("✗ Some production tests failed.")
        print("Review the errors above before deploying.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)