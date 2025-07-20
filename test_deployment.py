#!/usr/bin/env python3
"""
Fleet Management PWA - Automated Testing System
Comprehensive test suite for deployment verification
"""

import subprocess
import time
import requests
import os
import sys
from datetime import datetime
from urllib.parse import urljoin

class DeploymentTester:
    def __init__(self, base_url="https://fleet-management-pwa.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 15
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def test_local_imports(self):
        """Test local app imports and structure"""
        print("🔍 Testing local app imports...")
        try:
            # Test basic imports first
            import os
            import flask
            print("✅ Flask imports successfully")
            
            # Check if app.py file exists
            if os.path.exists('app.py'):
                print("✅ app.py file exists")
                return True
            else:
                print("❌ app.py file not found")
                return False
                
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def test_homepage(self):
        """Test if homepage loads successfully"""
        print("🏠 Testing homepage...")
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                print("✅ Homepage loads successfully")
                return True
            else:
                print(f"❌ Homepage returned {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Homepage request failed: {e}")
            return False
    
    def test_pwa_files(self):
        """Test PWA files accessibility"""
        print("📱 Testing PWA files...")
        pwa_files = [
            "/manifest.json",
            "/service-worker.js", 
            "/static/css/offline.css",
            "/static/icons/icon-192x192.png"
        ]
        
        all_passed = True
        for file_path in pwa_files:
            try:
                url = urljoin(self.base_url, file_path)
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {file_path}")
                else:
                    print(f"❌ {file_path} failed: {response.status_code}")
                    all_passed = False
            except requests.RequestException as e:
                print(f"❌ {file_path} failed: {e}")
                all_passed = False
        
        return all_passed
    
    def test_database_health(self):
        """Test if database is healthy"""
        print("🗄️ Testing database health...")
        try:
            # Test if homepage triggers database initialization
            response = self.session.get(self.base_url)
            
            # Simple check - if homepage loads without 500 error, DB is likely OK
            if response.status_code == 200:
                print("✅ Database appears healthy")
                return True
            else:
                print(f"❌ Database health check failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Database health test failed: {e}")
            return False
    
    def test_login_functionality(self):
        """Test basic login functionality"""
        print("🔑 Testing login functionality...")
        try:
            # Try to access login page
            login_url = urljoin(self.base_url, "/auth/login")
            response = self.session.get(login_url)
            
            if response.status_code == 200:
                print("✅ Login page accessible")
                return True
            else:
                print(f"❌ Login page failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Login test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and return overall result"""
        print("🚢 Fleet Management PWA - Automated Testing")
        print("=" * 50)
        
        tests = [
            ("Local Imports", self.test_local_imports),
            ("Homepage", self.test_homepage),
            ("PWA Files", self.test_pwa_files),
            ("Database Health", self.test_database_health),
            ("Login Functionality", self.test_login_functionality),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} test...")
            result = test_func()
            results.append((test_name, result))
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:<20} {status}")
            if result:
                passed += 1
        
        total = len(results)
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Deployment ready.")
            return True
        else:
            print("⚠️ Some tests failed. Check the issues above.")
            return False

def main():
    """Main entry point"""
    tester = DeploymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()