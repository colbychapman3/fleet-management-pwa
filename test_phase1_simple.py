#!/usr/bin/env python3
"""
Simple test for Phase 1: Database Schema Enhancement
Tests components that don't require full Flask app context
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_validation_standalone():
    """Test validation without app context"""
    print("Testing MaritimeValidator...")
    
    try:
        from models.maritime.validation import MaritimeValidator
        print("✓ MaritimeValidator imported successfully")
        
        # Test valid data
        valid_data = {
            'vessel_name': 'MSC Daniella',
            'vessel_type': 'container',
            'shipping_line': 'MSC',
            'operation_type': 'discharging',
            'status': 'pending',
            'total_vehicles': 1500,
            'progress': 0,
            'operation_manager': 'Colby Chapman'
        }
        
        is_valid, errors = MaritimeValidator.validate_maritime_operation(valid_data)
        
        if is_valid:
            print("✓ Valid data test passed")
        else:
            print(f"✗ Valid data test failed: {errors}")
            return False
        
        # Test invalid data scenarios
        invalid_tests = [
            # Empty vessel name
            ({'vessel_name': '', 'vessel_type': 'container', 'shipping_line': 'MSC', 'operation_type': 'discharging'}, 
             'vessel_name is required'),
            
            # Invalid vessel type
            ({'vessel_name': 'Test', 'vessel_type': 'invalid', 'shipping_line': 'MSC', 'operation_type': 'discharging'}, 
             'Invalid vessel type'),
            
            # Invalid IMO number
            ({'vessel_name': 'Test', 'vessel_type': 'container', 'shipping_line': 'MSC', 'operation_type': 'discharging', 'imo_number': 'invalid'}, 
             'IMO number must be in format'),
            
            # Invalid progress
            ({'vessel_name': 'Test', 'vessel_type': 'container', 'shipping_line': 'MSC', 'operation_type': 'discharging', 'progress': 150}, 
             'Progress must be no more than 100'),
        ]
        
        for test_data, expected_error in invalid_tests:
            is_valid, errors = MaritimeValidator.validate_maritime_operation(test_data)
            
            if is_valid:
                print(f"✗ Invalid data was accepted: {test_data}")
                return False
            
            if not any(expected_error in error for error in errors):
                print(f"✗ Expected error '{expected_error}' not found in: {errors}")
                return False
        
        print("✓ Invalid data tests passed")
        
        # Test field-specific validations
        field_tests = [
            (MaritimeValidator.validate_vessel_name, ('Valid Vessel',), None),
            (MaritimeValidator.validate_vessel_name, ('',), 'required'),
            (MaritimeValidator.validate_imo_number, ('IMO1234567',), None),
            (MaritimeValidator.validate_imo_number, ('invalid',), 'format'),
            (MaritimeValidator.validate_mmsi, ('123456789',), None),
            (MaritimeValidator.validate_mmsi, ('12345',), 'exactly 9 digits'),
            (MaritimeValidator.validate_progress, (50,), None),
            (MaritimeValidator.validate_progress, (150,), 'no more than 100'),
        ]
        
        for validator_func, args, expected_error in field_tests:
            result = validator_func(*args)
            
            if expected_error is None and result is not None:
                print(f"✗ Field validation failed: {validator_func.__name__} returned {result}")
                return False
            
            if expected_error is not None and (result is None or expected_error not in result):
                print(f"✗ Field validation missing expected error: {validator_func.__name__} expected '{expected_error}', got '{result}'")
                return False
        
        print("✓ Field-specific validation tests passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing validation: {e}")
        return False

def test_migration_syntax():
    """Test that migration file has correct syntax"""
    print("\nTesting migration file syntax...")
    
    try:
        migration_file = 'migrations/versions/004_enhance_maritime_operations.py'
        
        if not os.path.exists(migration_file):
            print(f"✗ Migration file not found: {migration_file}")
            return False
        
        # Try to compile the migration file
        with open(migration_file, 'r') as f:
            content = f.read()
        
        compile(content, migration_file, 'exec')
        print("✓ Migration file syntax is valid")
        
        # Check for required components
        required_components = [
            'def upgrade():',
            'def downgrade():',
            'revision = \'004\'',
            'add_column',
            'drop_column',
            'vessel_name',
            'operation_manager',
            'total_vehicles',
            'deck_data'
        ]
        
        missing_components = [comp for comp in required_components if comp not in content]
        
        if missing_components:
            print(f"✗ Migration missing components: {missing_components}")
            return False
        
        print("✓ Migration file has all required components")
        return True
        
    except Exception as e:
        print(f"✗ Error testing migration syntax: {e}")
        return False

def test_model_structure():
    """Test model structure without database connection"""
    print("\nTesting model structure...")
    
    try:
        # Read the model file and check structure
        model_file = 'models/maritime/maritime_operation.py'
        
        with open(model_file, 'r') as f:
            content = f.read()
        
        # Check for required components
        required_components = [
            'class MaritimeOperation',
            '__tablename__ = \'maritime_operations\'',
            'vessel_name = db.Column',
            'operation_manager = db.Column',
            'total_vehicles = db.Column',
            'deck_data = db.Column',
            'def get_team_summary',
            'def get_cargo_breakdown',
            'def to_dict',
            'def create_from_wizard_data'
        ]
        
        missing_components = [comp for comp in required_components if comp not in content]
        
        if missing_components:
            print(f"✗ Model missing components: {missing_components}")
            return False
        
        print("✓ Model has all required components")
        
        # Check for backward compatibility (original fields)
        original_fields = [
            'id = db.Column',
            'vessel_id = db.Column',
            'operation_type = db.Column',
            'status = db.Column',
            'created_at = db.Column',
            'updated_at = db.Column'
        ]
        
        missing_original = [field for field in original_fields if field not in content]
        
        if missing_original:
            print(f"✗ Model missing original fields: {missing_original}")
            return False
        
        print("✓ Model maintains backward compatibility")
        return True
        
    except Exception as e:
        print(f"✗ Error testing model structure: {e}")
        return False

def run_tests():
    """Run all standalone tests"""
    print("=" * 60)
    print("PHASE 1: Database Schema Enhancement - Standalone Tests")
    print("=" * 60)
    
    tests = [
        ("Validation Module", test_validation_standalone),
        ("Migration Syntax", test_migration_syntax),
        ("Model Structure", test_model_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 Phase 1 standalone tests completed successfully!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run database migration: flask db upgrade")
        print("3. Test with full app context")
        return True
    else:
        print("⚠️  Phase 1 has issues that need to be resolved")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)