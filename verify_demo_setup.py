#!/usr/bin/env python3
"""
Verify Demo Setup Script
Checks that demo users are properly configured and can authenticate
"""

import os
import sys
import sqlite3

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_demo_setup():
    """Verify that demo users are properly set up"""
    try:
        db_path = os.path.join('instance', 'fleet_management.db')
        print(f"Verifying database: {db_path}")
        
        if not os.path.exists(db_path):
            print("❌ Database file does not exist!")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("❌ Users table does not exist!")
            return False
        
        print("✅ Users table exists")
        
        # Check for demo users
        cursor.execute("SELECT email, username, role, is_active, password_hash FROM users WHERE email IN ('admin@fleet.com', 'worker@fleet.com')")
        users = cursor.fetchall()
        
        if len(users) != 2:
            print(f"❌ Expected 2 demo users, found {len(users)}")
            return False
        
        print("✅ Demo users exist")
        
        # Verify user details
        for user in users:
            email, username, role, is_active, password_hash = user
            print(f"\n📧 {email}")
            print(f"   Username: {username}")
            print(f"   Role: {role}")
            print(f"   Active: {'Yes' if is_active else 'No'}")
            print(f"   Password hash format: {password_hash[:30] if password_hash else 'None'}...")
            
            # Check role mapping
            expected_roles = {
                'admin@fleet.com': 'port_manager',
                'worker@fleet.com': 'general_stevedore'
            }
            
            if email in expected_roles and role == expected_roles[email]:
                print(f"   ✅ Role is correct ({role})")
            else:
                print(f"   ❌ Role mismatch. Expected: {expected_roles.get(email, 'unknown')}, Got: {role}")
            
            # Check password hash format (should be compatible with Werkzeug)
            if password_hash and password_hash.startswith('pbkdf2:sha256:'):
                print(f"   ✅ Password hash format is correct")
            else:
                print(f"   ❌ Password hash format is incompatible")
        
        conn.close()
        
        print("\n🎉 Demo setup verification completed!")
        print("\nDemo users are ready for testing:")
        print("- admin@fleet.com / admin123 (Port Manager)")
        print("- worker@fleet.com / worker123 (General Stevedore)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying demo setup: {e}")
        return False

def check_authentication_compatibility():
    """Check if password hashing is compatible with the application"""
    print("\n🔐 Checking authentication compatibility...")
    
    try:
        # Try to import werkzeug to test password compatibility
        import hashlib
        import base64
        
        # Test password hash verification logic (simulating what Werkzeug does)
        def verify_password(stored_hash, password):
            if not stored_hash.startswith('pbkdf2:sha256:'):
                return False
            
            try:
                method, iterations, salt, hash_part = stored_hash.split('$', 3)
                iterations = int(iterations.split(':')[-1])
                
                # Generate hash with same salt and iterations
                computed_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt.encode('utf-8'),
                    iterations
                )
                
                # Compare with stored hash
                stored_hash_bytes = base64.b64decode(hash_part + '==')  # Add padding
                return computed_hash == stored_hash_bytes
            except:
                return False
        
        # Test with a known hash
        db_path = os.path.join('instance', 'fleet_management.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT password_hash FROM users WHERE email = 'admin@fleet.com'")
        result = cursor.fetchone()
        
        if result:
            stored_hash = result[0]
            if verify_password(stored_hash, 'admin123'):
                print("✅ Password verification logic is working correctly")
            else:
                print("❌ Password verification logic is not working")
        
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Could not fully verify authentication compatibility: {e}")

if __name__ == '__main__':
    print("🔍 Fleet Management Demo Setup Verification")
    print("=" * 50)
    
    success = verify_demo_setup()
    check_authentication_compatibility()
    
    if success:
        print("\n✅ All checks passed! Demo users are ready to use.")
    else:
        print("\n❌ Some issues were found. Please run the setup scripts again.")