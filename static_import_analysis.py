#!/usr/bin/env python3
"""
Static Import Analysis for Agent 4 - Error Tracker
Analyzes import statements without executing them to avoid app initialization
"""

import os
import re
import ast

def extract_imports_from_file(file_path):
    """Extract import statements from a Python file using AST"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"from {module} import {alias.name}")
        
        return imports
    except Exception as e:
        return [f"Error parsing {file_path}: {e}"]

def check_import_path_exists(import_statement):
    """Check if the import path exists in the file system"""
    # Parse different import patterns
    if import_statement.startswith("from "):
        # from models.models.user import User
        match = re.match(r"from ([\w.]+) import", import_statement)
        if match:
            module_path = match.group(1)
            return check_module_path(module_path)
    elif import_statement.startswith("import "):
        # import models.models.user
        match = re.match(r"import ([\w.]+)", import_statement)
        if match:
            module_path = match.group(1)
            return check_module_path(module_path)
    
    return False, "Could not parse import statement"

def check_module_path(module_path):
    """Check if a module path exists"""
    path_parts = module_path.split('.')
    
    # Start from current directory
    current_path = "/home/colby/fleet-management-pwa"
    
    for part in path_parts:
        current_path = os.path.join(current_path, part)
        
        # Check if it's a directory with __init__.py
        if os.path.isdir(current_path):
            init_path = os.path.join(current_path, "__init__.py")
            if os.path.exists(init_path):
                continue
            else:
                return False, f"Directory {current_path} exists but no __init__.py"
        
        # Check if it's a Python file
        py_path = current_path + ".py"
        if os.path.exists(py_path):
            return True, f"Module file exists: {py_path}"
        
        return False, f"Path not found: {current_path} or {py_path}"
    
    return True, f"Module path exists: {current_path}"

def analyze_agent3_fixes():
    """Analyze the specific import fixes Agent 3 was supposed to make"""
    print("=== Agent 4: Static Import Analysis ===")
    print("Analyzing Agent 3's import fixes without execution...")
    
    # Test cases based on Agent 3's work
    test_cases = [
        {
            "file": "run_migrations.py",
            "expected_imports": [
                "import models.models.user",
                "import models.models.vessel", 
                "import models.models.task"
            ]
        },
        {
            "file": "scripts/create_sample_data.py", 
            "expected_imports": [
                "from models.models.vessel import Vessel"
            ]
        },
        {
            "file": "Documentation examples",
            "expected_imports": [
                "from models.maritime.ship_operation import ShipOperation",
                "from models.maritime.cargo_discharge import CargoDischarge"
            ]
        },
        {
            "file": "Alert system imports",
            "expected_imports": [
                "from models.models.tico_vehicle import TicoVehicle",
                "from models.maritime.stevedore_team import StevedoreTeam"
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_case in test_cases:
        print(f"\\n--- Testing {test_case['file']} ---")
        
        for import_stmt in test_case['expected_imports']:
            total_tests += 1
            exists, message = check_import_path_exists(import_stmt)
            
            if exists:
                print(f"  ✓ {import_stmt}")
                print(f"    {message}")
                passed_tests += 1
            else:
                print(f"  ✗ {import_stmt}")
                print(f"    {message}")
    
    # Additional file-specific analysis
    print("\\n--- Analyzing Actual File Imports ---")
    
    files_to_analyze = [
        "run_migrations.py",
        "scripts/create_sample_data.py"
    ]
    
    for file_path in files_to_analyze:
        if os.path.exists(file_path):
            print(f"\\nImports found in {file_path}:")
            imports = extract_imports_from_file(file_path)
            for imp in imports:
                if "models.models" in imp or "models.maritime" in imp:
                    exists, message = check_import_path_exists(imp)
                    status = "✓" if exists else "✗"
                    print(f"  {status} {imp}")
                    if not exists:
                        print(f"    Issue: {message}")
    
    # Check models directory structure
    print("\\n--- Models Directory Structure Analysis ---")
    models_structure = {
        "models/__init__.py": os.path.exists("models/__init__.py"),
        "models/models/__init__.py": os.path.exists("models/models/__init__.py"),
        "models/models/user.py": os.path.exists("models/models/user.py"),
        "models/models/vessel.py": os.path.exists("models/models/vessel.py"),
        "models/models/task.py": os.path.exists("models/models/task.py"),
        "models/models/tico_vehicle.py": os.path.exists("models/models/tico_vehicle.py"),
        "models/maritime/__init__.py": os.path.exists("models/maritime/__init__.py"),
        "models/maritime/ship_operation.py": os.path.exists("models/maritime/ship_operation.py"),
        "models/maritime/cargo_discharge.py": os.path.exists("models/maritime/cargo_discharge.py"),
        "models/maritime/stevedore_team.py": os.path.exists("models/maritime/stevedore_team.py"),
    }
    
    for path, exists in models_structure.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {path}")
    
    # Summary
    print(f"\\n=== STATIC ANALYSIS SUMMARY ===")
    print(f"Import Path Tests: {passed_tests}/{total_tests} passed")
    
    missing_files = [path for path, exists in models_structure.items() if not exists]
    if missing_files:
        print(f"Missing Files: {len(missing_files)}")
        for file in missing_files:
            print(f"  - {file}")
    else:
        print("File Structure: All required files present")
    
    if passed_tests == total_tests and not missing_files:
        print("\\n🎉 STATIC ANALYSIS PASSED!")
        print("All import paths appear to be correctly structured.")
        return True
    else:
        print("\\n❌ STATIC ANALYSIS ISSUES FOUND")
        print("Some import paths or files are missing.")
        return False

if __name__ == "__main__":
    success = analyze_agent3_fixes()
    exit(0 if success else 1)