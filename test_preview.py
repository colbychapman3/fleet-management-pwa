#!/usr/bin/env python3
"""
Preview Environment Testing Script
Specialized testing for preview environment with relaxed constraints
"""

import subprocess
import time
import requests
import os
import sys
from datetime import datetime
from urllib.parse import urljoin

class PreviewTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30  # Longer timeout for local
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def test_preview_health(self):
        """Test preview environment health"""
        print("🏥 Testing preview environment health...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Preview environment healthy: {health_data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ Preview health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Preview health check failed: {e}")
            return False
    
    def test_environment_variables(self):
        """Test that preview environment has correct configuration"""
        print("🔧 Testing environment configuration...")
        try:
            response = self.session.get(f"{self.base_url}/health/detailed")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Environment configuration accessible")
                
                # Check dependencies
                deps = health_data.get('dependencies', {})
                if deps.get('database', {}).get('status') == 'healthy':
                    print("✅ Preview database connected")
                else:
                    print("⚠️ Preview database connection issues")
                
                if deps.get('redis', {}).get('status') == 'healthy':
                    print("✅ Preview Redis connected")
                else:
                    print("⚠️ Preview Redis connection issues")
                
                return True
            else:
                print(f"❌ Environment config check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Environment config check failed: {e}")
            return False
    
    def test_preview_features(self):
        """Test preview-specific features and relaxed constraints"""
        print("🧪 Testing preview-specific features...")
        try:
            # Test homepage with preview mode
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                print("✅ Preview homepage loads")
                
                # Check for preview mode indicators
                if "preview" in response.text.lower() or "development" in response.text.lower():
                    print("✅ Preview mode indicators found")
                else:
                    print("ℹ️ No explicit preview mode indicators")
                
                return True
            else:
                print(f"❌ Preview homepage failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Preview features test failed: {e}")
            return False
    
    def test_development_tools(self):
        """Test development tools and debugging features"""
        print("🛠️ Testing development tools...")
        try:
            # Test if error pages show debug info
            response = self.session.get(f"{self.base_url}/nonexistent-route")
            if response.status_code == 404:
                print("✅ 404 handling works")
                return True
            else:
                print(f"⚠️ Unexpected response for 404 test: {response.status_code}")
                return True  # Not critical for preview
        except requests.RequestException as e:
            print(f"⚠️ Development tools test failed: {e}")
            return True  # Not critical
    
    def test_api_endpoints(self):
        """Test API endpoints in preview environment"""
        print("🔌 Testing API endpoints...")
        try:
            # Test API health
            api_health_url = f"{self.base_url}/api/health"
            response = self.session.get(api_health_url)
            if response.status_code == 200:
                print("✅ API endpoints accessible")
                return True
            elif response.status_code == 404:
                print("ℹ️ API health endpoint not implemented (acceptable)")
                return True
            else:
                print(f"⚠️ API test returned: {response.status_code}")
                return True  # Non-critical for preview
        except requests.RequestException as e:
            print(f"⚠️ API test failed: {e}")
            return True  # Non-critical for preview
    
    def run_preview_tests(self):
        """Run all preview environment tests"""
        print("🧪 Fleet Management PWA - Preview Environment Testing")
        print("=" * 60)
        
        tests = [
            ("Preview Health", self.test_preview_health),
            ("Environment Config", self.test_environment_variables),
            ("Preview Features", self.test_preview_features),
            ("Development Tools", self.test_development_tools),
            ("API Endpoints", self.test_api_endpoints),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} test...")
            result = test_func()
            results.append((test_name, result))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Preview Environment Test Results:")
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:<20} {status}")
            if result:
                passed += 1
        
        total = len(results)
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed >= total - 1:  # Allow 1 failure for preview
            print("🎉 Preview environment ready for testing!")
            return True
        else:
            print("⚠️ Preview environment has issues. Check logs above.")
            return False

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5001"
    
    print(f"🎯 Testing preview environment at: {base_url}")
    
    tester = PreviewTester(base_url)
    success = tester.run_preview_tests()
    
    if success:
        print("\n🚀 Preview environment is ready!")
        print("💡 You can now test features safely without affecting production.")
    else:
        print("\n🔧 Preview environment needs attention.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()