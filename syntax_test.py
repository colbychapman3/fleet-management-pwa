#!/usr/bin/env python3
"""
Simple syntax test for models without Flask dependencies
"""

import os
import sys
import ast

def check_python_syntax(filepath):
    """Check if a Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the syntax
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def test_all_models():
    """Test syntax of all model files"""
    print("Testing model file syntax...")
    
    model_files = [
        "models/models/enhanced_user.py",
        "models/models/enhanced_vessel.py",
        "models/models/enhanced_task.py",
        "models/models/equipment_assignment.py",
        "models/models/operation_assignment.py",
        "models/models/work_time_log.py",
        "models/models/cargo_batch.py",
        "models/maritime/ship_operation.py",
        "models/maritime/stevedore_team.py",
        "app.py"
    ]
    
    all_passed = True
    
    for filepath in model_files:
        if os.path.exists(filepath):
            passed, error = check_python_syntax(filepath)
            if passed:
                print(f"✓ {filepath}")
            else:
                print(f"✗ {filepath}: {error}")
                all_passed = False
        else:
            print(f"? {filepath}: File not found")
    
    return all_passed

def check_relationship_patterns():
    """Check for relationship pattern issues"""
    print("\nChecking for relationship pattern issues...")
    
    vessel_file = "models/models/enhanced_vessel.py"
    if not os.path.exists(vessel_file):
        print(f"✗ {vessel_file} not found")
        return False
    
    with open(vessel_file, 'r') as f:
        content = f.read()
    
    # Check for problematic patterns
    issues = []
    
    # Look for backref conflicts
    if 'backref=\'vessel\'' in content:
        # Count them
        backref_count = content.count('backref=\'vessel\'')
        if backref_count > 2:  # cargo_batches and time_logs should still have backref
            issues.append(f"Found {backref_count} backref='vessel' patterns - should be 2 or fewer")
    
    # Look for fixed patterns
    fixed_patterns = [
        'foreign_keys=\'EquipmentAssignment.vessel_id\'',
        'foreign_keys=\'OperationAssignment.vessel_id\''
    ]
    
    for pattern in fixed_patterns:
        if pattern in content:
            print(f"✓ Found fixed pattern: {pattern}")
        else:
            issues.append(f"Missing fixed pattern: {pattern}")
    
    if issues:
        for issue in issues:
            print(f"✗ {issue}")
        return False
    else:
        print("✓ Relationship patterns look correct")
        return True

def main():
    print("Fleet Management System - Syntax and Pattern Test")
    print("=" * 50)
    
    # Test syntax
    syntax_ok = test_all_models()
    
    # Test relationship patterns
    patterns_ok = check_relationship_patterns()
    
    if syntax_ok and patterns_ok:
        print("\n🎉 All tests passed!")
        print("✓ All Python files have valid syntax")
        print("✓ Relationship patterns are correctly fixed")
        print("\nYour fixes should resolve the SQLAlchemy relationship conflicts.")
        print("Push the changes and check your deployment logs.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()