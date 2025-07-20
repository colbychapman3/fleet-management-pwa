#!/usr/bin/env python3
"""
Initialize production database with demo users
This script connects to the production PostgreSQL database and creates demo users
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add current directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_production_database():
    """Initialize production database with demo users"""
    try:
        # Import Flask app to get database connection
        from app import app, db
        from models.models.enhanced_user import User
        
        print("Connecting to production database...")
        
        with app.app_context():
            try:
                # Test database connection
                result = db.engine.execute("SELECT version();")
                print(f"Database connected: {result.fetchone()[0]}")
                
                # Check if users table exists
                existing_users = User.query.count()
                print(f"Current users in database: {existing_users}")
                
                # Create admin user if doesn't exist
                admin_user = User.query.filter_by(email='admin@fleet.com').first()
                if not admin_user:
                    print("Creating admin user...")
                    admin_user = User(
                        email='admin@fleet.com',
                        first_name='Admin',
                        last_name='Manager',
                        role='port_manager',
                        is_active=True,
                        password_hash=generate_password_hash('admin123')
                    )
                    db.session.add(admin_user)
                    print("✅ Admin user created")
                else:
                    print("✅ Admin user already exists")
                    # Update password just in case
                    admin_user.password_hash = generate_password_hash('admin123')
                    print("✅ Admin password updated")
                
                # Create worker user if doesn't exist
                worker_user = User.query.filter_by(email='worker@fleet.com').first()
                if not worker_user:
                    print("Creating worker user...")
                    worker_user = User(
                        email='worker@fleet.com',
                        first_name='Worker',
                        last_name='Employee',
                        role='general_stevedore',
                        is_active=True,
                        password_hash=generate_password_hash('worker123')
                    )
                    db.session.add(worker_user)
                    print("✅ Worker user created")
                else:
                    print("✅ Worker user already exists")
                    # Update password just in case
                    worker_user.password_hash = generate_password_hash('worker123')
                    print("✅ Worker password updated")
                
                # Commit changes
                db.session.commit()
                print("✅ Database changes committed")
                
                # Verify users
                total_users = User.query.count()
                print(f"\nFinal user count: {total_users}")
                
                for user in User.query.all():
                    print(f"- {user.email} ({user.first_name}) - Role: {user.role} - Active: {user.is_active}")
                
                print("\n🎉 Production database initialization completed!")
                print("\nYou can now login with:")
                print("- admin@fleet.com / admin123 (port manager)")
                print("- worker@fleet.com / worker123 (general stevedore)")
                
                return True
                
            except Exception as db_error:
                print(f"❌ Database operation failed: {db_error}")
                db.session.rollback()
                return False
                
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return False

if __name__ == "__main__":
    print("🚢 Fleet Management System - Production Database Initialization")
    print("=" * 60)
    
    success = init_production_database()
    
    if success:
        print("\n✅ SUCCESS: Demo users are ready for production!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Database initialization incomplete")
        sys.exit(1)