#!/usr/bin/env python3
"""
Import validation script for Agent 4 - Error Tracker
Validates Agent 3's import fixes without triggering full app initialization
"""

import sys
import os
import traceback

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_import(import_statement, description):
    """Validate a single import statement"""
    print(f"Testing: {description}")
    print(f"  Import: {import_statement}")
    
    try:
        # Use exec to test the import without triggering module initialization
        namespace = {}
        exec(import_statement, namespace)
        print(f"  ✓ SUCCESS: {description}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {description}")
        print(f"    Error: {e}")
        print(f"    Traceback: {traceback.format_exc().split('\\n')[-3]}")
        return False

def validate_file_structure():
    """Validate that required files exist"""
    print("\\n=== Validating File Structure ===")
    
    required_files = [
        "models/models/__init__.py",
        "models/models/user.py", 
        "models/models/vessel.py",
        "models/models/task.py",
        "models/maritime/ship_operation.py",
        "models/maritime/cargo_discharge.py",
        "models/models/tico_vehicle.py",
        "models/maritime/stevedore_team.py",
        "run_migrations.py",
        "scripts/create_sample_data.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ MISSING: {file_path}")
            all_exist = False
    
    return all_exist

def validate_syntax():
    """Validate Python syntax of key files"""
    print("\\n=== Validating Python Syntax ===")
    
    key_files = [
        "run_migrations.py",
        "scripts/create_sample_data.py",
        "models/models/__init__.py",
        "models/models/user.py",
        "models/models/vessel.py", 
        "models/models/task.py"
    ]
    
    all_valid = True
    for file_path in key_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                compile(source, file_path, 'exec')
                print(f"  ✓ Syntax OK: {file_path}")
            except SyntaxError as e:
                print(f"  ✗ SYNTAX ERROR: {file_path}")
                print(f"    Line {e.lineno}: {e.msg}")
                all_valid = False
            except Exception as e:
                print(f"  ✗ ERROR: {file_path} - {e}")
                all_valid = False
        else:
            print(f"  ✗ MISSING: {file_path}")
            all_valid = False
    
    return all_valid

def main():
    """Run all validation tests"""
    print("=== Agent 4: Import Validation Report ===")
    print("Validating Agent 3's import fixes...")
    
    # Test 1: File structure
    structure_ok = validate_file_structure()
    
    # Test 2: Python syntax 
    syntax_ok = validate_syntax()
    
    # Test 3: Import validation
    print("\\n=== Validating Import Statements ===")
    
    import_tests = [
        # Migration script imports (from run_migrations.py lines 86-88)
        ("import models.models.user", "User model import"),
        ("import models.models.vessel", "Vessel model import"),
        ("import models.models.task", "Task model import"),
        
        # Sample data script imports (from scripts/create_sample_data.py)
        ("from models.models.vessel import Vessel", "Direct Vessel import"),
        
        # Documentation/API example imports 
        ("from models.maritime.ship_operation import ShipOperation", "ShipOperation import"),
        ("from models.maritime.cargo_discharge import CargoDischarge", "CargoDischarge import"),
        
        # Alert system imports that were previously failing
        ("from models.models.tico_vehicle import TicoVehicle", "TicoVehicle import"),
        ("from models.maritime.stevedore_team import StevedoreTeam", "StevedoreTeam import"),
    ]
    
    passed_imports = 0
    total_imports = len(import_tests)
    
    for import_stmt, description in import_tests:
        if validate_import(import_stmt, description):
            passed_imports += 1
        print()
    
    # Summary
    print("=== VALIDATION SUMMARY ===")
    print(f"File Structure: {'✓ PASS' if structure_ok else '✗ FAIL'}")
    print(f"Python Syntax: {'✓ PASS' if syntax_ok else '✗ FAIL'}")
    print(f"Import Tests: {passed_imports}/{total_imports} passed")
    
    if structure_ok and syntax_ok and passed_imports == total_imports:
        print("\\n🎉 ALL VALIDATIONS PASSED!")
        print("Agent 3's import fixes appear to be working correctly.")
        return True
    else:
        print("\\n❌ VALIDATION FAILURES DETECTED")
        print("Some import issues remain to be resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)