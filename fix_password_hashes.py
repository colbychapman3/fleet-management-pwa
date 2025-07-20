#!/usr/bin/env python3
"""
Fix Password Hashes Script
Updates the password hashes to be compatible with Werkzeug's check_password_hash
"""

import os
import sys
import sqlite3
import hashlib
import base64
import secrets

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_werkzeug_compatible_hash(password):
    """Generate password hash compatible with Werkzeug's check_password_hash"""
    # Werkzeug uses format: method$salt$hash
    method = "pbkdf2:sha256:260000"  # PBKDF2 with SHA256 and 260000 iterations (Werkzeug default)
    salt = secrets.token_urlsafe(16)
    
    # Generate hash using same method as Werkzeug
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        260000
    )
    
    # Encode hash in base64 (without padding) as Werkzeug does
    hash_b64 = base64.b64encode(password_hash).decode('ascii').rstrip('=')
    
    return f"{method}${salt}${hash_b64}"

def fix_password_hashes():
    """Fix the password hashes in the database"""
    try:
        db_path = os.path.join('instance', 'fleet_management.db')
        print(f"Connecting to database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update admin user password hash
        admin_hash = generate_werkzeug_compatible_hash('admin123')
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (admin_hash, 'admin@fleet.com')
        )
        print("Updated admin@fleet.com password hash")
        
        # Update worker user password hash
        worker_hash = generate_werkzeug_compatible_hash('worker123')
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (worker_hash, 'worker@fleet.com')
        )
        print("Updated worker@fleet.com password hash")
        
        conn.commit()
        
        # Verify updates
        cursor.execute("SELECT email, username, password_hash FROM users")
        users = cursor.fetchall()
        print(f"\nUpdated {len(users)} users:")
        for user in users:
            print(f"- {user[0]} ({user[1]}) - Hash format: {user[2][:20]}...")
        
        conn.close()
        print("\nPassword hashes updated successfully!")
        print("Passwords are now compatible with Werkzeug authentication.")
        return True
        
    except Exception as e:
        print(f"Error fixing password hashes: {e}")
        return False

if __name__ == '__main__':
    success = fix_password_hashes()
    if success:
        print("\nYou can now login with:")
        print("- admin@fleet.com / admin123 (manager role)")
        print("- worker@fleet.com / worker123 (worker role)")
    else:
        print("\nFailed to fix password hashes.")