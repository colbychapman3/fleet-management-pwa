#!/usr/bin/env python3
"""
Test script for Phase 1: Database Schema Enhancement
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_model_import():
    """Test that the enhanced maritime model can be imported"""
    try:
        from models.maritime.maritime_operation import MaritimeOperation
        print("✓ Enhanced MaritimeOperation model imported successfully")
        
        # Check if new fields are present
        expected_fields = [
            'vessel_name', 'vessel_type', 'shipping_line', 'operation_manager',
            'auto_ops_lead', 'total_vehicles', 'brv_target', 'progress',
            'deck_data', 'imo_number'
        ]
        
        model_fields = [c.name for c in MaritimeOperation.__table__.columns]
        missing_fields = [field for field in expected_fields if field not in model_fields]
        
        if missing_fields:
            print(f"✗ Missing fields: {missing_fields}")
            return False
        else:
            print("✓ All expected fields present in model")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to import MaritimeOperation model: {e}")
        return False

def test_validation_import():
    """Test that the validation module can be imported"""
    try:
        from models.maritime.validation import MaritimeValidator
        print("✓ MaritimeValidator imported successfully")
        
        # Test basic validation
        test_data = {
            'vessel_name': 'Test Vessel',
            'vessel_type': 'container',
            'shipping_line': 'MSC',
            'operation_type': 'discharging'
        }
        
        is_valid, errors = MaritimeValidator.validate_maritime_operation(test_data)
        
        if is_valid:
            print("✓ Basic validation test passed")
        else:
            print(f"✗ Validation test failed: {errors}")
            return False
            
        # Test invalid data
        invalid_data = {
            'vessel_name': '',  # Empty name should fail
            'vessel_type': 'invalid_type',
            'shipping_line': 'MSC',
            'operation_type': 'discharging'
        }
        
        is_valid, errors = MaritimeValidator.validate_maritime_operation(invalid_data)
        
        if not is_valid and len(errors) > 0:
            print("✓ Invalid data correctly rejected")
        else:
            print("✗ Invalid data was not rejected")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Failed to import or test MaritimeValidator: {e}")
        return False

def test_migration_file():
    """Test that the migration file is properly formatted"""
    try:
        migration_file = 'migrations/versions/004_enhance_maritime_operations.py'
        
        if not os.path.exists(migration_file):
            print(f"✗ Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            content = f.read()
            
        # Check for required migration elements
        required_elements = [
            'def upgrade():', 'def downgrade():', 'revision = \'004\'',
            'vessel_name', 'operation_manager', 'total_vehicles'
        ]
        
        missing_elements = [elem for elem in required_elements if elem not in content]
        
        if missing_elements:
            print(f"✗ Migration file missing elements: {missing_elements}")
            return False
        
        print("✓ Migration file structure is correct")
        return True
        
    except Exception as e:
        print(f"✗ Failed to validate migration file: {e}")
        return False

def test_backward_compatibility():
    """Test that existing fields are preserved"""
    try:
        from models.maritime.maritime_operation import MaritimeOperation
        
        # Check that original fields still exist
        original_fields = ['id', 'vessel_id', 'operation_type', 'status', 'created_at', 'updated_at']
        model_fields = [c.name for c in MaritimeOperation.__table__.columns]
        
        missing_original = [field for field in original_fields if field not in model_fields]
        
        if missing_original:
            print(f"✗ Backward compatibility broken - missing original fields: {missing_original}")
            return False
        
        print("✓ Backward compatibility maintained")
        return True
        
    except Exception as e:
        print(f"✗ Failed to test backward compatibility: {e}")
        return False

def run_all_tests():
    """Run all Phase 1 tests"""
    print("=" * 60)
    print("PHASE 1: Database Schema Enhancement - Test Results")
    print("=" * 60)
    
    tests = [
        ("Model Import Test", test_model_import),
        ("Validation Test", test_validation_import),
        ("Migration File Test", test_migration_file),
        ("Backward Compatibility Test", test_backward_compatibility)
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
        print("🎉 Phase 1 implementation is ready!")
        print("Next: Run migration with 'flask db upgrade'")
        return True
    else:
        print("⚠️  Phase 1 needs attention before proceeding")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)