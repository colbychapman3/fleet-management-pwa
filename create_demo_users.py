#!/usr/bin/env python3
"""
Demo User Creation Script
Creates admin@fleet.com and worker@fleet.com users for testing
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_demo_users():
    """Create demo users without full app dependencies"""
    try:
        # Minimal imports to avoid dependency issues
        import sqlite3
        import hashlib
        import secrets
        
        def simple_password_hash(password):
            """Simple password hashing using hashlib"""
            salt = secrets.token_hex(16)
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            return f"pbkdf2:sha256:100000${salt}${password_hash.hex()}"
        
        db_path = os.path.join('instance', 'fleet_management.db')
        print(f"Connecting to database: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("Users table doesn't exist. Creating it...")
            # Create basic users table
            cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) UNIQUE NOT NULL,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(30) NOT NULL DEFAULT 'worker',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                last_sync DATETIME,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                phone VARCHAR(20),
                employee_id VARCHAR(20),
                emergency_contact VARCHAR(100),
                emergency_phone VARCHAR(20),
                maritime_license_number VARCHAR(50),
                maritime_license_expiry DATE,
                twic_card_number VARCHAR(20),
                twic_expiry DATE,
                safety_training_completion DATE,
                medical_clearance_date DATE,
                auto_operations_certified BOOLEAN DEFAULT 0,
                heavy_equipment_certified BOOLEAN DEFAULT 0,
                crane_operator_certified BOOLEAN DEFAULT 0,
                forklift_certified BOOLEAN DEFAULT 0,
                dangerous_goods_certified BOOLEAN DEFAULT 0,
                current_vessel_id INTEGER,
                current_team_id INTEGER,
                shift_start_time TIME,
                shift_end_time TIME,
                hourly_rate DECIMAL(10, 2),
                total_hours_worked INTEGER DEFAULT 0,
                operations_completed INTEGER DEFAULT 0,
                safety_incidents INTEGER DEFAULT 0,
                last_safety_training DATE,
                performance_rating FLOAT,
                availability_status VARCHAR(20) DEFAULT 'available',
                current_location VARCHAR(100),
                radio_call_sign VARCHAR(10)
            );
            """)
            print("Created users table")
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", ('admin@fleet.com',))
        if not cursor.fetchone():
            admin_password_hash = simple_password_hash('admin123')
            cursor.execute("""
            INSERT INTO users (email, username, password_hash, role, is_active, first_name, last_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, ('admin@fleet.com', 'admin', admin_password_hash, 'manager', 1, 'Admin', 'User'))
            print("Created admin@fleet.com user")
        else:
            print("admin@fleet.com user already exists")
        
        # Check if worker user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", ('worker@fleet.com',))
        if not cursor.fetchone():
            worker_password_hash = simple_password_hash('worker123')
            cursor.execute("""
            INSERT INTO users (email, username, password_hash, role, is_active, first_name, last_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, ('worker@fleet.com', 'worker', worker_password_hash, 'worker', 1, 'Worker', 'User'))
            print("Created worker@fleet.com user")
        else:
            print("worker@fleet.com user already exists")
        
        conn.commit()
        
        # Verify users were created
        cursor.execute("SELECT email, username, role, is_active FROM users")
        users = cursor.fetchall()
        print(f"\nTotal users in database: {len(users)}")
        for user in users:
            print(f"- {user[0]} ({user[1]}) - Role: {user[2]} - Active: {user[3]}")
        
        conn.close()
        print("\nDemo users created successfully!")
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Required dependencies not available")
        return False
    except Exception as e:
        print(f"Error creating demo users: {e}")
        return False

if __name__ == '__main__':
    success = create_demo_users()
    if success:
        print("\nYou can now login with:")
        print("- admin@fleet.com / admin123 (manager role)")
        print("- worker@fleet.com / worker123 (worker role)")
    else:
        print("\nFailed to create demo users.")