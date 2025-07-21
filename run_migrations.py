#!/usr/bin/env python3
"""
Migration execution script for Fleet Management PWA
"""

import os
import sys
import shutil
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_app():
    """Create Flask app with minimal configuration for migrations"""
    app = Flask(__name__)
    
    # Use SQLite for this test
    db_path = os.path.join(os.path.dirname(__file__), 'fleet_management.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'migration-test-key'
    
    return app

def backup_database():
    """Create a backup of the current database"""
    db_path = os.path.join(os.path.dirname(__file__), 'fleet_management.db')
    
    if os.path.exists(db_path):
        backup_name = f'fleet_management_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        backup_path = os.path.join(os.path.dirname(__file__), backup_name)
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    else:
        print("No existing database found, creating new one")
        return None

def check_migration_status(migrate):
    """Check current migration status"""
    try:
        from flask_migrate import current, heads
        current_rev = current()
        head_rev = heads()
        print(f"Current migration: {current_rev}")
        print(f"Latest migration: {head_rev}")
        return current_rev, head_rev
    except Exception as e:
        print(f"Could not check migration status: {e}")
        return None, None

def main():
    print("=== Fleet Management PWA Migration Tool ===")
    
    # Create app
    app = create_app()
    
    # Initialize database and migration
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    
    with app.app_context():
        print("\n1. Backing up current database state...")
        backup_path = backup_database()
        
        print("\n2. Checking migration status...")
        current_rev, head_rev = check_migration_status(migrate)
        
        print("\n3. Available migration files:")
        migrations_path = os.path.join(os.path.dirname(__file__), 'migrations', 'versions')
        if os.path.exists(migrations_path):
            migration_files = sorted([f for f in os.listdir(migrations_path) if f.endswith('.py')])
            for i, migration in enumerate(migration_files, 1):
                print(f"   {i}. {migration}")
        else:
            print("   No migrations directory found")
            return
        
        # Import models to ensure they're registered
        try:
            print("\n4. Importing models...")
            import models.models.user
            import models.models.vessel  
            import models.models.task
            print("   Core models imported successfully")
        except ImportError as e:
            print(f"   Warning: Could not import some models: {e}")
        
        print("\n5. Database connection test...")
        try:
            db.create_all()
            print("   Database connection successful")
        except Exception as e:
            print(f"   Database connection failed: {e}")
            return
        
        print(f"\nMigration environment ready!")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        if backup_path:
            print(f"Backup: {backup_path}")

if __name__ == "__main__":
    main()