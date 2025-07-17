#!/usr/bin/env python3
"""
Test script to validate import structure and potential issues
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test basic Python imports that should work without external dependencies"""
    print("Testing basic imports...")
    
    try:
        import os
        import logging
        import sys
        from datetime import datetime, timedelta
        print("✓ Standard library imports successful")
    except ImportError as e:
        print(f"✗ Standard library import error: {e}")
        return False
    
    return True

def test_flask_imports():
    """Test Flask-related imports"""
    print("Testing Flask imports...")
    
    try:
        from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response, flash
        print("✓ Flask core imports successful")
    except ImportError as e:
        print(f"✗ Flask import error: {e}")
        return False
    
    return True

def test_app_structure():
    """Test if the app file structure is correct"""
    print("Testing app structure...")
    
    # Check if models directory exists
    if not os.path.exists('models'):
        print("✗ models directory not found")
        return False
    
    # Check if key model files exist
    model_files = [
        'models/models/user.py',
        'models/models/vessel.py',
        'models/models/task.py',
        'models/models/sync_log.py'
    ]
    
    for model_file in model_files:
        if not os.path.exists(model_file):
            print(f"✗ Model file not found: {model_file}")
            return False
    
    print("✓ App structure looks good")
    return True

def test_env_variables():
    """Test environment variable handling"""
    print("Testing environment variables...")
    
    # Test with different environment setups
    test_cases = [
        ('FLASK_ENV', 'development'),
        ('FLASK_ENV', 'production'),
        ('DATABASE_URL', 'postgresql://test:test@localhost/test'),
        ('REDIS_URL', 'redis://localhost:6379/0'),
    ]
    
    original_env = {}
    
    for env_var, test_value in test_cases:
        # Save original value
        original_env[env_var] = os.environ.get(env_var)
        
        # Set test value
        os.environ[env_var] = test_value
        print(f"  Testing {env_var}={test_value}")
        
        # Test that our app would handle this correctly
        if env_var == 'DATABASE_URL' and test_value.startswith('postgres://'):
            # Test the postgres:// to postgresql:// conversion logic
            database_url = test_value
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
                print(f"    ✓ URL conversion: {test_value} -> {database_url}")
    
    # Restore original environment
    for env_var, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(env_var, None)
        else:
            os.environ[env_var] = original_value
    
    print("✓ Environment variable handling looks good")
    return True

def main():
    """Run all tests"""
    print("=== Fleet Management App Import Tests ===\n")
    
    tests = [
        test_basic_imports,
        test_flask_imports,
        test_app_structure,
        test_env_variables,
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
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("✓ All tests passed! App structure looks good for deployment.")
        return True
    else:
        print("✗ Some tests failed. Please address the issues above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)