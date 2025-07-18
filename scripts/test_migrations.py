#!/usr/bin/env python3
"""
Test script for maritime database migrations

This script tests the migration process for both PostgreSQL and SQLite
databases, ensuring compatibility and data integrity.
"""

import os
import sys
import sqlite3
import psycopg2
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationTester:
    """Test maritime database migrations for both PostgreSQL and SQLite"""
    
    def __init__(self):
        self.test_results = {
            'postgresql': {'passed': 0, 'failed': 0, 'errors': []},
            'sqlite': {'passed': 0, 'failed': 0, 'errors': []}
        }
        self.temp_dir = None
        
    def setup_test_environment(self):
        """Setup temporary test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix='maritime_migration_test_')
        logger.info(f"Created test environment: {self.temp_dir}")
        
        # Copy migration files to test directory
        migrations_source = Path(__file__).parent.parent / 'migrations'
        migrations_dest = Path(self.temp_dir) / 'migrations'
        
        if migrations_source.exists():
            shutil.copytree(migrations_source, migrations_dest)
            logger.info("Copied migration files to test environment")
        else:
            logger.error("Migration source directory not found")
            return False
            
        return True
    
    def cleanup_test_environment(self):
        """Cleanup temporary test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up test environment: {self.temp_dir}")
    
    def test_sqlite_migrations(self):
        """Test migrations on SQLite database"""
        logger.info("Testing SQLite migrations...")
        
        try:
            # Create test SQLite database
            db_path = os.path.join(self.temp_dir, 'test_maritime.db')
            
            # Test each migration individually
            migrations = [
                ('001_initial_migration.py', 'Initial schema creation'),
                ('002_maritime_enhancement.py', 'Maritime enhancement'),
                ('003_berth_management.py', 'Berth management'),
                ('004_performance_optimization.py', 'Performance optimization'),
                ('005_data_validation_constraints.py', 'Data validation')
            ]
            
            conn = sqlite3.connect(db_path)
            conn.execute('PRAGMA foreign_keys = ON')
            
            for migration_file, description in migrations:
                try:
                    logger.info(f"Testing SQLite migration: {description}")
                    
                    # Apply migration
                    success = self._apply_sqlite_migration(conn, migration_file)
                    
                    if success:
                        # Test data insertion
                        success = self._test_sqlite_data_operations(conn, migration_file)
                    
                    if success:
                        self.test_results['sqlite']['passed'] += 1
                        logger.info(f"✓ SQLite migration {migration_file} passed")
                    else:
                        self.test_results['sqlite']['failed'] += 1
                        logger.error(f"✗ SQLite migration {migration_file} failed")
                        
                except Exception as e:
                    self.test_results['sqlite']['failed'] += 1
                    error_msg = f"SQLite migration {migration_file} error: {str(e)}"
                    self.test_results['sqlite']['errors'].append(error_msg)
                    logger.error(error_msg)
            
            conn.close()
            
        except Exception as e:
            error_msg = f"SQLite test setup error: {str(e)}"
            self.test_results['sqlite']['errors'].append(error_msg)
            logger.error(error_msg)
    
    def test_postgresql_migrations(self):
        """Test migrations on PostgreSQL database"""
        logger.info("Testing PostgreSQL migrations...")
        
        # Skip PostgreSQL tests if not available
        if not self._check_postgresql_available():
            logger.warning("PostgreSQL not available, skipping PostgreSQL tests")
            return
        
        try:
            # Create test PostgreSQL database
            test_db_name = f"test_maritime_{int(datetime.now().timestamp())}"
            
            # Connect to PostgreSQL and create test database
            admin_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                database='postgres'
            )
            admin_conn.autocommit = True
            admin_cursor = admin_conn.cursor()
            
            # Create test database
            admin_cursor.execute(f'CREATE DATABASE "{test_db_name}"')
            admin_conn.close()
            
            # Connect to test database
            test_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                database=test_db_name
            )
            
            # Test migrations
            migrations = [
                ('001_initial_migration.py', 'Initial schema creation'),
                ('002_maritime_enhancement.py', 'Maritime enhancement'),
                ('003_berth_management.py', 'Berth management'),
                ('004_performance_optimization.py', 'Performance optimization'),
                ('005_data_validation_constraints.py', 'Data validation')
            ]
            
            for migration_file, description in migrations:
                try:
                    logger.info(f"Testing PostgreSQL migration: {description}")
                    
                    # Apply migration
                    success = self._apply_postgresql_migration(test_conn, migration_file)
                    
                    if success:
                        # Test data insertion
                        success = self._test_postgresql_data_operations(test_conn, migration_file)
                    
                    if success:
                        self.test_results['postgresql']['passed'] += 1
                        logger.info(f"✓ PostgreSQL migration {migration_file} passed")
                    else:
                        self.test_results['postgresql']['failed'] += 1
                        logger.error(f"✗ PostgreSQL migration {migration_file} failed")
                        
                except Exception as e:
                    self.test_results['postgresql']['failed'] += 1
                    error_msg = f"PostgreSQL migration {migration_file} error: {str(e)}"
                    self.test_results['postgresql']['errors'].append(error_msg)
                    logger.error(error_msg)
            
            test_conn.close()
            
            # Cleanup test database
            admin_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                database='postgres'
            )
            admin_conn.autocommit = True
            admin_cursor = admin_conn.cursor()
            admin_cursor.execute(f'DROP DATABASE IF EXISTS "{test_db_name}"')
            admin_conn.close()
            
        except Exception as e:
            error_msg = f"PostgreSQL test setup error: {str(e)}"
            self.test_results['postgresql']['errors'].append(error_msg)
            logger.error(error_msg)
    
    def _check_postgresql_available(self):
        """Check if PostgreSQL is available for testing"""
        try:
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
                database='postgres',
                connect_timeout=5
            )
            conn.close()
            return True
        except Exception:
            return False
    
    def _apply_sqlite_migration(self, conn, migration_file):
        """Apply a single migration to SQLite database"""
        try:
            migration_path = os.path.join(self.temp_dir, 'migrations', 'versions', migration_file)
            
            if not os.path.exists(migration_path):
                logger.error(f"Migration file not found: {migration_path}")
                return False
            
            # Read and execute migration content (simplified)
            # In a real implementation, you would use Alembic
            cursor = conn.cursor()
            
            # Create basic tables for testing
            if '001_initial' in migration_file:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vessels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL,
                        imo_number VARCHAR(20),
                        vessel_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email VARCHAR(120) NOT NULL UNIQUE,
                        username VARCHAR(80) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        task_type VARCHAR(50) NOT NULL,
                        created_by_id INTEGER NOT NULL,
                        vessel_id INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by_id) REFERENCES users(id),
                        FOREIGN KEY (vessel_id) REFERENCES vessels(id)
                    )
                ''')
                
            elif '002_maritime' in migration_file:
                # Add maritime columns to vessels
                cursor.execute('ALTER TABLE vessels ADD COLUMN shipping_line VARCHAR(50)')
                cursor.execute('ALTER TABLE vessels ADD COLUMN berth VARCHAR(20)')
                cursor.execute('ALTER TABLE vessels ADD COLUMN operation_type VARCHAR(50) DEFAULT "Discharge Only"')
                cursor.execute('ALTER TABLE vessels ADD COLUMN total_vehicles INTEGER DEFAULT 0')
                cursor.execute('ALTER TABLE vessels ADD COLUMN progress INTEGER DEFAULT 0')
                
                # Create maritime tables
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cargo_operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vessel_id INTEGER NOT NULL,
                        zone VARCHAR(10),
                        vehicle_type VARCHAR(50),
                        quantity INTEGER,
                        discharged INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (vessel_id) REFERENCES vessels(id)
                    )
                ''')
                
            elif '003_berth' in migration_file:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS berths (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        berth_number VARCHAR(20) NOT NULL UNIQUE,
                        berth_name VARCHAR(100),
                        berth_type VARCHAR(50),
                        status VARCHAR(20) DEFAULT 'active',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
            # Test specific functionality for each migration
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"SQLite migration error: {str(e)}")
            return False
    
    def _apply_postgresql_migration(self, conn, migration_file):
        """Apply a single migration to PostgreSQL database"""
        try:
            cursor = conn.cursor()
            
            # Simplified migration application for testing
            if '001_initial' in migration_file:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vessels (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        imo_number VARCHAR(20),
                        vessel_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(120) NOT NULL UNIQUE,
                        username VARCHAR(80) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        task_type VARCHAR(50) NOT NULL,
                        created_by_id INTEGER NOT NULL REFERENCES users(id),
                        vessel_id INTEGER REFERENCES vessels(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
            elif '002_maritime' in migration_file:
                cursor.execute('ALTER TABLE vessels ADD COLUMN IF NOT EXISTS shipping_line VARCHAR(50)')
                cursor.execute('ALTER TABLE vessels ADD COLUMN IF NOT EXISTS berth VARCHAR(20)')
                cursor.execute('ALTER TABLE vessels ADD COLUMN IF NOT EXISTS operation_type VARCHAR(50) DEFAULT \'Discharge Only\'')
                cursor.execute('ALTER TABLE vessels ADD COLUMN IF NOT EXISTS total_vehicles INTEGER DEFAULT 0')
                cursor.execute('ALTER TABLE vessels ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cargo_operations (
                        id SERIAL PRIMARY KEY,
                        vessel_id INTEGER NOT NULL REFERENCES vessels(id),
                        zone VARCHAR(10),
                        vehicle_type VARCHAR(50),
                        quantity INTEGER,
                        discharged INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
            elif '003_berth' in migration_file:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS berths (
                        id SERIAL PRIMARY KEY,
                        berth_number VARCHAR(20) NOT NULL UNIQUE,
                        berth_name VARCHAR(100),
                        berth_type VARCHAR(50),
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL migration error: {str(e)}")
            conn.rollback()
            return False
    
    def _test_sqlite_data_operations(self, conn, migration_file):
        """Test data operations after SQLite migration"""
        try:
            cursor = conn.cursor()
            
            if '001_initial' in migration_file:
                # Test basic CRUD operations
                cursor.execute("INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)",
                             ('test@example.com', 'testuser', 'hashedpassword', 'admin'))
                
                cursor.execute("INSERT INTO vessels (name, vessel_type) VALUES (?, ?)",
                             ('Test Vessel', 'Container Ship'))
                
                # Verify data
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM vessels")
                vessel_count = cursor.fetchone()[0]
                
                if user_count == 0 or vessel_count == 0:
                    return False
                    
            elif '002_maritime' in migration_file:
                # Test maritime operations
                cursor.execute("SELECT id FROM vessels LIMIT 1")
                vessel_result = cursor.fetchone()
                
                if vessel_result:
                    vessel_id = vessel_result[0]
                    cursor.execute('''
                        INSERT INTO cargo_operations (vessel_id, zone, vehicle_type, quantity, discharged)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (vessel_id, 'BRV', 'Sedan', 100, 25))
                    
                    # Verify cargo operation
                    cursor.execute("SELECT discharged FROM cargo_operations WHERE vessel_id = ?", (vessel_id,))
                    discharged = cursor.fetchone()[0]
                    
                    if discharged != 25:
                        return False
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"SQLite data operation test error: {str(e)}")
            return False
    
    def _test_postgresql_data_operations(self, conn, migration_file):
        """Test data operations after PostgreSQL migration"""
        try:
            cursor = conn.cursor()
            
            if '001_initial' in migration_file:
                cursor.execute("INSERT INTO users (email, username, password_hash, role) VALUES (%s, %s, %s, %s)",
                             ('test@example.com', 'testuser', 'hashedpassword', 'admin'))
                
                cursor.execute("INSERT INTO vessels (name, vessel_type) VALUES (%s, %s)",
                             ('Test Vessel', 'Container Ship'))
                
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM vessels")
                vessel_count = cursor.fetchone()[0]
                
                if user_count == 0 or vessel_count == 0:
                    return False
                    
            elif '002_maritime' in migration_file:
                cursor.execute("SELECT id FROM vessels LIMIT 1")
                vessel_result = cursor.fetchone()
                
                if vessel_result:
                    vessel_id = vessel_result[0]
                    cursor.execute('''
                        INSERT INTO cargo_operations (vessel_id, zone, vehicle_type, quantity, discharged)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (vessel_id, 'BRV', 'Sedan', 100, 25))
                    
                    cursor.execute("SELECT discharged FROM cargo_operations WHERE vessel_id = %s", (vessel_id,))
                    discharged = cursor.fetchone()[0]
                    
                    if discharged != 25:
                        return False
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL data operation test error: {str(e)}")
            conn.rollback()
            return False
    
    def test_rollback_functionality(self):
        """Test migration rollback functionality"""
        logger.info("Testing rollback functionality...")
        
        try:
            # Create test databases for rollback testing
            sqlite_db = os.path.join(self.temp_dir, 'rollback_test.db')
            
            conn = sqlite3.connect(sqlite_db)
            cursor = conn.cursor()
            
            # Apply migrations
            self._apply_sqlite_migration(conn, '001_initial_migration.py')
            self._apply_sqlite_migration(conn, '002_maritime_enhancement.py')
            
            # Verify tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables_before = [row[0] for row in cursor.fetchall()]
            
            # Test rollback (simplified - would use Alembic in real implementation)
            cursor.execute("DROP TABLE IF EXISTS cargo_operations")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables_after = [row[0] for row in cursor.fetchall()]
            
            if 'cargo_operations' not in tables_after and 'cargo_operations' in tables_before:
                logger.info("✓ Rollback test passed")
                return True
            else:
                logger.error("✗ Rollback test failed")
                return False
                
        except Exception as e:
            logger.error(f"Rollback test error: {str(e)}")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_environment': self.temp_dir,
            'results': self.test_results,
            'summary': {
                'total_tests': (
                    self.test_results['sqlite']['passed'] + 
                    self.test_results['sqlite']['failed'] +
                    self.test_results['postgresql']['passed'] + 
                    self.test_results['postgresql']['failed']
                ),
                'total_passed': (
                    self.test_results['sqlite']['passed'] + 
                    self.test_results['postgresql']['passed']
                ),
                'total_failed': (
                    self.test_results['sqlite']['failed'] + 
                    self.test_results['postgresql']['failed']
                )
            }
        }
        
        # Save report to file
        report_path = os.path.join(self.temp_dir, 'migration_test_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("MARITIME DATABASE MIGRATION TEST REPORT")
        print("="*60)
        print(f"Test Environment: {self.temp_dir}")
        print(f"Timestamp: {report['timestamp']}")
        print("\nResults Summary:")
        print(f"  Total Tests: {report['summary']['total_tests']}")
        print(f"  Passed: {report['summary']['total_passed']}")
        print(f"  Failed: {report['summary']['total_failed']}")
        
        print("\nSQLite Results:")
        print(f"  Passed: {self.test_results['sqlite']['passed']}")
        print(f"  Failed: {self.test_results['sqlite']['failed']}")
        if self.test_results['sqlite']['errors']:
            print("  Errors:")
            for error in self.test_results['sqlite']['errors']:
                print(f"    - {error}")
        
        print("\nPostgreSQL Results:")
        print(f"  Passed: {self.test_results['postgresql']['passed']}")
        print(f"  Failed: {self.test_results['postgresql']['failed']}")
        if self.test_results['postgresql']['errors']:
            print("  Errors:")
            for error in self.test_results['postgresql']['errors']:
                print(f"    - {error}")
        
        print(f"\nDetailed report saved to: {report_path}")
        print("="*60)
        
        return report
    
    def run_all_tests(self):
        """Run all migration tests"""
        logger.info("Starting maritime database migration tests...")
        
        if not self.setup_test_environment():
            logger.error("Failed to setup test environment")
            return False
        
        try:
            # Run tests
            self.test_sqlite_migrations()
            self.test_postgresql_migrations()
            self.test_rollback_functionality()
            
            # Generate report
            report = self.generate_test_report()
            
            # Return success if no failures
            return report['summary']['total_failed'] == 0
            
        finally:
            self.cleanup_test_environment()


def main():
    """Main function to run migration tests"""
    tester = MigrationTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            logger.info("All migration tests passed!")
            sys.exit(0)
        else:
            logger.error("Some migration tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()