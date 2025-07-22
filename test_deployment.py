#!/usr/bin/env python3
"""
<<<<<<< HEAD
Automated deployment testing script for Fleet Management PWA
Tests critical functionality after each deployment
"""

import requests
import json
import time
import sys
from urllib.parse import urljoin

class FleetManagementTester:
    def __init__(self, base_url="https://fleet-management-pwa.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Fleet-Test-Bot/1.0'
        })
        
    def test_homepage(self):
        """Test homepage loads correctly"""
=======
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
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
        print("🏠 Testing homepage...")
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
<<<<<<< HEAD
                if "Fleet Management System" in response.text:
                    print("✅ Homepage loads successfully")
                    return True
                else:
                    print("❌ Homepage content missing")
                    return False
=======
                print("✅ Homepage loads successfully")
                return True
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
            else:
                print(f"❌ Homepage returned {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Homepage request failed: {e}")
            return False
    
    def test_pwa_files(self):
<<<<<<< HEAD
        """Test PWA files are accessible"""
        print("📱 Testing PWA files...")
        pwa_files = [
            "/manifest.json",
            "/service-worker.js",
=======
        """Test PWA files accessibility"""
        print("📱 Testing PWA files...")
        pwa_files = [
            "/manifest.json",
            "/service-worker.js", 
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
            "/static/css/offline.css",
            "/static/icons/icon-192x192.png"
        ]
        
<<<<<<< HEAD
        all_good = True
=======
        all_passed = True
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
        for file_path in pwa_files:
            try:
                url = urljoin(self.base_url, file_path)
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {file_path}")
                else:
<<<<<<< HEAD
                    print(f"❌ {file_path} returned {response.status_code}")
                    all_good = False
            except requests.RequestException as e:
                print(f"❌ {file_path} failed: {e}")
                all_good = False
        
        return all_good
    
    def test_csrf_login(self):
        """Test login form has CSRF protection"""
        print("🔐 Testing CSRF protection...")
        try:
            # Get login page
            response = self.session.get(urljoin(self.base_url, "/auth/login"))
            if response.status_code != 200:
                print(f"❌ Login page returned {response.status_code}")
                return False
            
            # Check for CSRF token
            if 'csrf_token' in response.text:
                print("✅ CSRF token found in login form")
                return True
            else:
                print("❌ CSRF token missing from login form")
                return False
                
        except requests.RequestException as e:
            print(f"❌ CSRF test failed: {e}")
            return False
    
    def test_login_functionality(self):
        """Test actual login with demo credentials"""
        print("🔑 Testing login functionality...")
        try:
            # Get login page first to get CSRF token
            login_url = urljoin(self.base_url, "/auth/login")
            response = self.session.get(login_url)
            
            if response.status_code != 200:
                print(f"❌ Could not access login page: {response.status_code}")
                return False
            
            # Extract CSRF token (simple extraction)
            csrf_token = None
            for line in response.text.split('\n'):
                if 'csrf_token' in line and 'value=' in line:
                    start = line.find('value="') + 7
                    end = line.find('"', start)
                    csrf_token = line[start:end]
                    break
            
            if not csrf_token:
                print("❌ Could not extract CSRF token")
                return False
            
            # Attempt login with proper headers
            login_data = {
                'email': 'admin@fleet.com',
                'password': 'admin123',
                'csrf_token': csrf_token
            }
            
            # Add referrer header for CSRF protection
            headers = {
                'Referer': login_url,
                'Origin': self.base_url
            }
            
            response = self.session.post(login_url, data=login_data, headers=headers, allow_redirects=False)
            
            # Check for successful login (redirect to dashboard)
            if response.status_code in [302, 301]:
                location = response.headers.get('Location', '')
                if 'dashboard' in location or location == '/':
                    print("✅ Login successful (redirected)")
                    return True
                else:
                    print(f"❌ Login redirect unexpected: {location}")
                    return False
            elif response.status_code == 200:
                # Check if we're still on login page (failed login)
                if "Invalid email or password" in response.text:
                    print("❌ Login failed - invalid credentials")
                    return False
                elif "/auth/login" in response.url:
                    print("❌ Login failed - still on login page")
                    return False
                else:
                    print("✅ Login successful (same page)")
                    return True
            else:
                print(f"❌ Login returned unexpected status: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Login test failed: {e}")
            return False
    
    def test_dashboard_access(self):
        """Test dashboard access after login"""
        print("📊 Testing dashboard access...")
        try:
            # Try to access dashboard directly - if we're already logged in from previous test, this should work
            dashboard_url = urljoin(self.base_url, "/dashboard/manager")
            response = self.session.get(dashboard_url, timeout=10)
            
            if response.status_code == 200:
                # Check for dashboard content
                if "Manager Dashboard" in response.text and "Stevedoring" in response.text:
                    print("✅ Manager dashboard loads successfully")
                    return True
                else:
                    print("❌ Dashboard content missing or incomplete")
                    return False
            elif response.status_code == 302:
                # If redirected, we need to login first
                print("🔐 Dashboard redirected, attempting login first...")
                
                # Get the redirect location
                redirect_url = response.headers.get('Location', '/auth/login')
                if not redirect_url.startswith('http'):
                    redirect_url = urljoin(self.base_url, redirect_url)
                
                # Get login page
                response = self.session.get(redirect_url)
                if response.status_code != 200:
                    print(f"❌ Could not access login page: {response.status_code}")
                    return False
                
                # Extract CSRF token
                csrf_token = None
                for line in response.text.split('\n'):
                    if 'csrf_token' in line and 'value=' in line:
                        start = line.find('value="') + 7
                        end = line.find('"', start)
                        csrf_token = line[start:end]
                        break
                
                if not csrf_token:
                    print("❌ Could not extract CSRF token for dashboard login")
                    return False
                
                # Login for dashboard test
                login_data = {
                    'email': 'admin@fleet.com',
                    'password': 'admin123',
                    'csrf_token': csrf_token
                }
                
                headers = {
                    'Referer': redirect_url,
                    'Origin': self.base_url
                }
                
                login_response = self.session.post(redirect_url, data=login_data, headers=headers, allow_redirects=True)
                
                # Now try dashboard again
                response = self.session.get(dashboard_url, timeout=10)
                if response.status_code == 200:
                    if "Manager Dashboard" in response.text and "Stevedoring" in response.text:
                        print("✅ Manager dashboard loads successfully after login")
                        return True
                    else:
                        print("❌ Dashboard content missing after login")
                        return False
                else:
                    print(f"❌ Dashboard still returned {response.status_code} after login")
                    return False
            else:
                print(f"❌ Dashboard returned {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Dashboard test failed: {e}")
            return False
    
    def test_database_health(self):
        """Test if database is healthy by checking API endpoints"""
=======
                    print(f"❌ {file_path} failed: {response.status_code}")
                    all_passed = False
            except requests.RequestException as e:
                print(f"❌ {file_path} failed: {e}")
                all_passed = False
        
        return all_passed
    
    def test_database_health(self):
        """Test if database is healthy"""
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
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
    
<<<<<<< HEAD
=======
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
    
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
    def run_all_tests(self):
        """Run all tests and return overall result"""
        print("🚢 Fleet Management PWA - Automated Testing")
        print("=" * 50)
        
        tests = [
<<<<<<< HEAD
            ("Homepage", self.test_homepage),
            ("PWA Files", self.test_pwa_files),
            ("CSRF Protection", self.test_csrf_login),
            ("Database Health", self.test_database_health),
            ("Login Functionality", self.test_login_functionality),
            ("Dashboard Access", self.test_dashboard_access),
=======
            ("Local Imports", self.test_local_imports),
            ("Homepage", self.test_homepage),
            ("PWA Files", self.test_pwa_files),
            ("Database Health", self.test_database_health),
            ("Login Functionality", self.test_login_functionality),
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} test...")
            result = test_func()
            results.append((test_name, result))
<<<<<<< HEAD
            time.sleep(1)  # Brief pause between tests
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        
        passed = 0
        total = len(results)
        
=======
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        passed = 0
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:<20} {status}")
            if result:
                passed += 1
        
<<<<<<< HEAD
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Application is ready for use.")
=======
        total = len(results)
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Deployment ready.")
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
            return True
        else:
            print("⚠️ Some tests failed. Check the issues above.")
            return False

def main():
<<<<<<< HEAD
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://fleet-management-pwa.onrender.com"
    
    tester = FleetManagementTester(base_url)
    success = tester.run_all_tests()
    
=======
    """Main entry point"""
    tester = DeploymentTester()
    success = tester.run_all_tests()
>>>>>>> 4e49b731f64fd42daed4637f411f05aa1cb96683
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()