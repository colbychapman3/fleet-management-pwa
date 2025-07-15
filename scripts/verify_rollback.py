#!/usr/bin/env python3
"""
Rollback verification script for maritime database migrations

This script verifies that database rollbacks work correctly and data integrity
is maintained during the rollback process.
"""

import os
import sys
import sqlite3
import psycopg2
import tempfile
import shutil
import json
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RollbackVerifier:
    """Verify database rollback functionality for maritime migrations"""
    
    def __init__(self):
        self.test_results = {
            'rollback_tests': [],
            'data_integrity_tests': [],
            'foreign_key_tests': [],
            'constraint_tests': []
        }
        self.temp_dir = None
    
    def setup_test_environment(self):
        """Setup test environment with sample data"""
        self.temp_dir = tempfile.mkdtemp(prefix='rollback_test_')
        logger.info(f"Created rollback test environment: {self.temp_dir}")
        return True
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up test environment: {self.temp_dir}")
    
    def create_test_data(self, db_type='sqlite'):
        """Create comprehensive test data for rollback verification"""
        test_data = {
            'users': [
                {
                    'email': 'admin@maritime.com',
                    'username': 'admin',
                    'password_hash': 'hashed_password_1',
                    'role': 'maritime_manager',
                    'department': 'Operations',
                    'is_active': True
                },
                {
                    'email': 'supervisor@maritime.com', 
                    'username': 'supervisor',
                    'password_hash': 'hashed_password_2',
                    'role': 'operations_supervisor',
                    'department': 'Operations',
                    'is_active': True
                },
                {
                    'email': 'stevedore1@maritime.com',
                    'username': 'stevedore1',
                    'password_hash': 'hashed_password_3',
                    'role': 'stevedore',
                    'department': 'Maritime Operations',
                    'is_active': True
                }
            ],
            'vessels': [
                {
                    'name': 'MV Atlantic Trader',
                    'imo_number': 'IMO1234567',
                    'vessel_type': 'Container Ship',
                    'shipping_line': 'Atlantic Shipping',
                    'operation_type': 'Discharge Only',
                    'total_vehicles': 500,
                    'expected_rate': 150,
                    'progress': 25
                },
                {
                    'name': 'MV Pacific Explorer',
                    'imo_number': 'IMO2345678',
                    'vessel_type': 'RoRo Vessel',
                    'shipping_line': 'Pacific Lines',
                    'operation_type': 'Discharge and Loading',
                    'total_vehicles': 300,
                    'expected_rate': 120,
                    'progress': 60
                }
            ],
            'berths': [
                {
                    'berth_number': 'B01',
                    'berth_name': 'Container Terminal 1',
                    'berth_type': 'Container',
                    'status': 'active',
                    'length_meters': 250.0,
                    'max_draft': 12.0
                },
                {
                    'berth_number': 'B02',
                    'berth_name': 'RoRo Terminal',
                    'berth_type': 'RoRo',
                    'status': 'active',
                    'length_meters': 200.0,
                    'max_draft': 8.0
                }
            ],
            'cargo_operations': [
                {
                    'vessel_id': 1,
                    'zone': 'BRV',
                    'vehicle_type': 'Sedan',
                    'quantity': 150,
                    'discharged': 40
                },
                {
                    'vessel_id': 1,
                    'zone': 'ZEE',
                    'vehicle_type': 'SUV',
                    'quantity': 100,
                    'discharged': 20
                },
                {
                    'vessel_id': 2,
                    'zone': 'SOU',
                    'vehicle_type': 'Truck',
                    'quantity': 50,
                    'discharged': 30
                }
            ]
        }
        return test_data
    
    def insert_test_data_sqlite(self, conn, test_data):
        """Insert test data into SQLite database"""
        cursor = conn.cursor()
        
        try:
            # Insert users
            for user in test_data['users']:
                cursor.execute('''
                    INSERT INTO users (email, username, password_hash, role, department, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user['email'], user['username'], user['password_hash'],
                    user['role'], user.get('department'), user['is_active']
                ))
            
            # Insert vessels
            for vessel in test_data['vessels']:
                cursor.execute('''
                    INSERT INTO vessels (name, imo_number, vessel_type, shipping_line, 
                                       operation_type, total_vehicles, expected_rate, progress)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    vessel['name'], vessel['imo_number'], vessel['vessel_type'],
                    vessel['shipping_line'], vessel['operation_type'],
                    vessel['total_vehicles'], vessel['expected_rate'], vessel['progress']
                ))
            
            # Insert berths (if table exists)
            try:
                for berth in test_data['berths']:
                    cursor.execute('''
                        INSERT INTO berths (berth_number, berth_name, berth_type, status, 
                                          length_meters, max_draft)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        berth['berth_number'], berth['berth_name'], berth['berth_type'],
                        berth['status'], berth['length_meters'], berth['max_draft']
                    ))
            except sqlite3.OperationalError:
                # Berths table might not exist yet
                pass
            
            # Insert cargo operations (if table exists)
            try:
                for cargo in test_data['cargo_operations']:
                    cursor.execute('''
                        INSERT INTO cargo_operations (vessel_id, zone, vehicle_type, quantity, discharged)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        cargo['vessel_id'], cargo['zone'], cargo['vehicle_type'],
                        cargo['quantity'], cargo['discharged']
                    ))
            except sqlite3.OperationalError:
                # Cargo operations table might not exist yet
                pass
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error inserting SQLite test data: {str(e)}")
            conn.rollback()
            return False
    
    def test_sqlite_rollback_sequence(self):
        """Test complete rollback sequence for SQLite"""
        logger.info("Testing SQLite rollback sequence...")
        
        try:
            # Create test database
            db_path = os.path.join(self.temp_dir, 'rollback_test.db')
            conn = sqlite3.connect(db_path)
            conn.execute('PRAGMA foreign_keys = ON')
            cursor = conn.cursor()
            
            test_data = self.create_test_data('sqlite')
            
            # Step 1: Apply initial migration
            logger.info("Step 1: Applying initial migration...")
            self._apply_initial_schema_sqlite(cursor)
            
            # Step 2: Insert base data
            logger.info("Step 2: Inserting base test data...")
            base_data_success = self.insert_test_data_sqlite(conn, test_data)
            
            if not base_data_success:
                logger.error("Failed to insert base test data")
                return False
            
            # Step 3: Take snapshot of data
            snapshot_before = self._take_data_snapshot_sqlite(cursor)
            
            # Step 4: Apply maritime enhancement migration
            logger.info("Step 3: Applying maritime enhancement...")
            self._apply_maritime_enhancement_sqlite(cursor)
            
            # Step 5: Insert maritime-specific data
            logger.info("Step 4: Inserting maritime-specific data...")
            maritime_data_success = self.insert_test_data_sqlite(conn, test_data)
            
            # Step 6: Verify maritime data
            maritime_snapshot = self._take_data_snapshot_sqlite(cursor)
            
            # Step 7: Perform rollback
            logger.info("Step 5: Performing rollback...")
            rollback_success = self._rollback_maritime_enhancement_sqlite(cursor)
            
            if not rollback_success:
                logger.error("Rollback failed")
                return False
            
            # Step 8: Verify data integrity after rollback
            logger.info("Step 6: Verifying data integrity after rollback...")
            snapshot_after = self._take_data_snapshot_sqlite(cursor)
            
            # Step 9: Compare snapshots
            integrity_check = self._compare_snapshots(snapshot_before, snapshot_after)
            
            conn.close()
            
            test_result = {
                'test_name': 'SQLite Complete Rollback Sequence',
                'success': integrity_check,
                'details': {
                    'base_data_inserted': base_data_success,
                    'maritime_data_inserted': maritime_data_success,
                    'rollback_executed': rollback_success,
                    'data_integrity_preserved': integrity_check
                }
            }
            
            self.test_results['rollback_tests'].append(test_result)
            
            if integrity_check:
                logger.info("✓ SQLite rollback sequence test passed")
            else:
                logger.error("✗ SQLite rollback sequence test failed")
            
            return integrity_check
            
        except Exception as e:
            logger.error(f"SQLite rollback sequence test error: {str(e)}")
            test_result = {
                'test_name': 'SQLite Complete Rollback Sequence',
                'success': False,
                'error': str(e)
            }
            self.test_results['rollback_tests'].append(test_result)
            return False
    
    def _apply_initial_schema_sqlite(self, cursor):
        """Apply initial schema for SQLite"""
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
    
    def _apply_maritime_enhancement_sqlite(self, cursor):
        """Apply maritime enhancement migration for SQLite"""
        # Add maritime columns to vessels
        try:
            cursor.execute('ALTER TABLE vessels ADD COLUMN shipping_line VARCHAR(50)')
        except sqlite3.OperationalError:
            pass  # Column might already exist
        
        try:
            cursor.execute('ALTER TABLE vessels ADD COLUMN operation_type VARCHAR(50) DEFAULT "Discharge Only"')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE vessels ADD COLUMN total_vehicles INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE vessels ADD COLUMN expected_rate INTEGER DEFAULT 150')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE vessels ADD COLUMN progress INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        # Add maritime columns to users
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN department VARCHAR(50)')
        except sqlite3.OperationalError:
            pass
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS berths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                berth_number VARCHAR(20) NOT NULL UNIQUE,
                berth_name VARCHAR(100),
                berth_type VARCHAR(50),
                status VARCHAR(20) DEFAULT 'active',
                length_meters REAL,
                max_draft REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _rollback_maritime_enhancement_sqlite(self, cursor):
        """Rollback maritime enhancement for SQLite"""
        try:
            # Drop maritime tables
            cursor.execute('DROP TABLE IF EXISTS cargo_operations')
            cursor.execute('DROP TABLE IF EXISTS berths')
            
            # Note: SQLite doesn't support dropping columns, so we can't remove
            # the added columns from vessels and users tables. In a real scenario,
            # we would recreate the tables without the maritime columns.
            
            return True
            
        except Exception as e:
            logger.error(f"SQLite rollback error: {str(e)}")
            return False
    
    def _take_data_snapshot_sqlite(self, cursor):
        """Take a snapshot of current data state"""
        snapshot = {}
        
        try:
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                snapshot[table] = {'count': count}
                
                # Get sample data for verification
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                sample_data = cursor.fetchall()
                snapshot[table]['sample'] = sample_data
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error taking data snapshot: {str(e)}")
            return {}
    
    def _compare_snapshots(self, before, after):
        """Compare data snapshots to verify integrity"""
        try:
            # Check that base tables are preserved
            base_tables = ['users', 'vessels', 'tasks']
            
            for table in base_tables:
                if table not in before or table not in after:
                    logger.error(f"Base table {table} missing from snapshots")
                    return False
                
                if before[table]['count'] != after[table]['count']:
                    logger.error(f"Data count mismatch in table {table}: {before[table]['count']} vs {after[table]['count']}")
                    return False
            
            # Check that maritime tables are removed
            maritime_tables = ['cargo_operations', 'berths']
            
            for table in maritime_tables:
                if table in after:
                    logger.error(f"Maritime table {table} still exists after rollback")
                    return False
            
            logger.info("Data integrity check passed")
            return True
            
        except Exception as e:
            logger.error(f"Error comparing snapshots: {str(e)}")
            return False
    
    def test_foreign_key_integrity(self):
        """Test foreign key integrity during rollback"""
        logger.info("Testing foreign key integrity during rollback...")
        
        try:
            db_path = os.path.join(self.temp_dir, 'fk_test.db')
            conn = sqlite3.connect(db_path)
            conn.execute('PRAGMA foreign_keys = ON')
            cursor = conn.cursor()
            
            # Create schema with foreign keys
            self._apply_initial_schema_sqlite(cursor)
            self._apply_maritime_enhancement_sqlite(cursor)
            
            # Insert test data with foreign key relationships
            cursor.execute("INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)",
                         ('test@example.com', 'testuser', 'hash', 'admin'))
            
            cursor.execute("INSERT INTO vessels (name, vessel_type) VALUES (?, ?)",
                         ('Test Ship', 'Container'))
            
            cursor.execute("INSERT INTO cargo_operations (vessel_id, zone, quantity) VALUES (?, ?, ?)",
                         (1, 'BRV', 100))
            
            # Verify foreign key relationships
            cursor.execute('''
                SELECT co.id, v.name 
                FROM cargo_operations co 
                JOIN vessels v ON co.vessel_id = v.id
            ''')
            fk_result = cursor.fetchall()
            
            if not fk_result:
                logger.error("Foreign key relationship not working")
                return False
            
            # Perform rollback
            self._rollback_maritime_enhancement_sqlite(cursor)
            
            # Verify base data is still intact
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM vessels")
            vessel_count = cursor.fetchone()[0]
            
            if user_count != 1 or vessel_count != 1:
                logger.error("Base data was affected during rollback")
                return False
            
            conn.close()
            
            test_result = {
                'test_name': 'Foreign Key Integrity Test',
                'success': True,
                'details': 'Foreign key relationships maintained during rollback'
            }
            
            self.test_results['foreign_key_tests'].append(test_result)
            
            logger.info("✓ Foreign key integrity test passed")
            return True
            
        except Exception as e:
            logger.error(f"Foreign key integrity test error: {str(e)}")
            test_result = {
                'test_name': 'Foreign Key Integrity Test',
                'success': False,
                'error': str(e)
            }
            self.test_results['foreign_key_tests'].append(test_result)
            return False
    
    def test_constraint_preservation(self):
        """Test that constraints are properly handled during rollback"""
        logger.info("Testing constraint preservation during rollback...")
        
        try:
            db_path = os.path.join(self.temp_dir, 'constraint_test.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create schema
            self._apply_initial_schema_sqlite(cursor)
            
            # Test unique constraints
            cursor.execute("INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)",
                         ('test1@example.com', 'user1', 'hash', 'admin'))
            
            # Try to insert duplicate email (should fail)
            try:
                cursor.execute("INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)",
                             ('test1@example.com', 'user2', 'hash', 'admin'))
                logger.error("Unique constraint not enforced")
                return False
            except sqlite3.IntegrityError:
                # Expected behavior
                pass
            
            # Apply maritime enhancement
            self._apply_maritime_enhancement_sqlite(cursor)
            
            # Rollback
            self._rollback_maritime_enhancement_sqlite(cursor)
            
            # Test that constraints still work
            try:
                cursor.execute("INSERT INTO users (email, username, password_hash, role) VALUES (?, ?, ?, ?)",
                             ('test1@example.com', 'user3', 'hash', 'admin'))
                logger.error("Unique constraint not enforced after rollback")
                return False
            except sqlite3.IntegrityError:
                # Expected behavior
                pass
            
            conn.close()
            
            test_result = {
                'test_name': 'Constraint Preservation Test',
                'success': True,
                'details': 'Database constraints maintained after rollback'
            }
            
            self.test_results['constraint_tests'].append(test_result)
            
            logger.info("✓ Constraint preservation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Constraint preservation test error: {str(e)}")
            test_result = {
                'test_name': 'Constraint Preservation Test',
                'success': False,
                'error': str(e)
            }
            self.test_results['constraint_tests'].append(test_result)
            return False
    
    def generate_rollback_report(self):
        """Generate comprehensive rollback verification report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_environment': self.temp_dir,
            'test_results': self.test_results,
            'summary': {
                'total_tests': sum(len(tests) for tests in self.test_results.values()),
                'passed_tests': sum(
                    len([t for t in tests if t.get('success', False)]) 
                    for tests in self.test_results.values()
                ),
                'failed_tests': sum(
                    len([t for t in tests if not t.get('success', True)]) 
                    for tests in self.test_results.values()
                )
            }
        }
        
        # Save report
        report_path = os.path.join(self.temp_dir, 'rollback_verification_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("MARITIME DATABASE ROLLBACK VERIFICATION REPORT")
        print("="*60)
        print(f"Test Environment: {self.temp_dir}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"\nSummary:")
        print(f"  Total Tests: {report['summary']['total_tests']}")
        print(f"  Passed: {report['summary']['passed_tests']}")
        print(f"  Failed: {report['summary']['failed_tests']}")
        
        for category, tests in self.test_results.items():
            if tests:
                print(f"\n{category.replace('_', ' ').title()}:")
                for test in tests:
                    status = "✓" if test.get('success', False) else "✗"
                    print(f"  {status} {test['test_name']}")
                    if 'error' in test:
                        print(f"    Error: {test['error']}")
        
        print(f"\nDetailed report saved to: {report_path}")
        print("="*60)
        
        return report
    
    def run_all_rollback_tests(self):
        """Run all rollback verification tests"""
        logger.info("Starting rollback verification tests...")
        
        if not self.setup_test_environment():
            logger.error("Failed to setup test environment")
            return False
        
        try:
            # Run all tests
            tests = [
                self.test_sqlite_rollback_sequence,
                self.test_foreign_key_integrity,
                self.test_constraint_preservation
            ]
            
            all_passed = True
            for test in tests:
                try:
                    result = test()
                    if not result:
                        all_passed = False
                except Exception as e:
                    logger.error(f"Test {test.__name__} failed with error: {str(e)}")
                    all_passed = False
            
            # Generate report
            report = self.generate_rollback_report()
            
            return all_passed
            
        finally:
            self.cleanup_test_environment()


def main():
    """Main function to run rollback verification"""
    verifier = RollbackVerifier()
    
    try:
        success = verifier.run_all_rollback_tests()
        
        if success:
            logger.info("All rollback verification tests passed!")
            sys.exit(0)
        else:
            logger.error("Some rollback verification tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Rollback verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Rollback verification error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()