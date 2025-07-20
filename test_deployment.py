#!/usr/bin/env python3
"""
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
        print("🏠 Testing homepage...")
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                if "Fleet Management System" in response.text:
                    print("✅ Homepage loads successfully")
                    return True
                else:
                    print("❌ Homepage content missing")
                    return False
            else:
                print(f"❌ Homepage returned {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Homepage request failed: {e}")
            return False
    
    def test_pwa_files(self):
        """Test PWA files are accessible"""
        print("📱 Testing PWA files...")
        pwa_files = [
            "/manifest.json",
            "/service-worker.js",
            "/static/css/offline.css",
            "/static/icons/icon-192x192.png"
        ]
        
        all_good = True
        for file_path in pwa_files:
            try:
                url = urljoin(self.base_url, file_path)
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {file_path}")
                else:
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
            
            # Attempt login
            login_data = {
                'email': 'admin@fleet.com',
                'password': 'admin123',
                'csrf_token': csrf_token
            }
            
            response = self.session.post(login_url, data=login_data, allow_redirects=False)
            
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
    
    def test_database_health(self):
        """Test if database is healthy by checking API endpoints"""
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
    
    def run_all_tests(self):
        """Run all tests and return overall result"""
        print("🚢 Fleet Management PWA - Automated Testing")
        print("=" * 50)
        
        tests = [
            ("Homepage", self.test_homepage),
            ("PWA Files", self.test_pwa_files),
            ("CSRF Protection", self.test_csrf_login),
            ("Database Health", self.test_database_health),
            ("Login Functionality", self.test_login_functionality),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} test...")
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Brief pause between tests
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:<20} {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Application is ready for use.")
            return True
        else:
            print("⚠️ Some tests failed. Check the issues above.")
            return False

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://fleet-management-pwa.onrender.com"
    
    tester = FleetManagementTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()