#!/usr/bin/env python3
"""
Lightweight Integration Validator - Agent 4
Fast validation without full app initialization
"""

import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import time

def log_status(message: str, level: str = "INFO"):
    """Log status messages with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def validate_syntax(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate Python file syntax using AST"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content, filename=str(file_path))
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Parse error: {str(e)}"

def check_import_syntax(file_path: Path) -> Dict[str, Any]:
    """Check import statements in a file without executing them"""
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
        
        # Look for enhanced_* imports
        enhanced_imports = [imp for imp in imports if "enhanced_" in imp]
        
        return {
            "success": True,
            "all_imports": imports,
            "enhanced_imports": enhanced_imports,
            "enhanced_count": len(enhanced_imports)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "enhanced_imports": [],
            "enhanced_count": 0
        }

def analyze_enhanced_model_files() -> Dict[str, Any]:
    """Analyze the enhanced model files directly"""
    log_status("Analyzing enhanced model files...")
    
    project_root = Path(".").resolve()
    results = {}
    
    enhanced_files = [
        "models/models/enhanced_vessel.py",
        "models/models/enhanced_task.py"
    ]
    
    for file_path in enhanced_files:
        full_path = project_root / file_path
        if not full_path.exists():
            results[file_path] = {"exists": False, "error": "File not found"}
            continue
        
        # Validate syntax
        syntax_valid, syntax_error = validate_syntax(full_path)
        
        # Analyze imports
        import_analysis = check_import_syntax(full_path)
        
        # Analyze model definition
        model_info = analyze_model_definition(full_path)
        
        results[file_path] = {
            "exists": True,
            "syntax_valid": syntax_valid,
            "syntax_error": syntax_error,
            "import_analysis": import_analysis,
            "model_info": model_info
        }
        
        if syntax_valid:
            log_status(f"✓ {file_path} - syntax valid")
        else:
            log_status(f"✗ {file_path} - syntax error: {syntax_error}", "ERROR")
    
    return results

def analyze_model_definition(file_path: Path) -> Dict[str, Any]:
    """Analyze SQLAlchemy model definition in file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from db.Model or similar
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Attribute):
                        base_names.append(f"{base.value.id}.{base.attr}")
                    elif isinstance(base, ast.Name):
                        base_names.append(base.id)
                
                classes.append({
                    "name": node.name,
                    "bases": base_names,
                    "is_sqlalchemy_model": any("Model" in base for base in base_names)
                })
        
        return {
            "classes": classes,
            "has_sqlalchemy_models": any(cls["is_sqlalchemy_model"] for cls in classes)
        }
        
    except Exception as e:
        return {"error": str(e), "classes": [], "has_sqlalchemy_models": False}

def scan_for_enhanced_imports() -> Dict[str, List[str]]:
    """Scan all Python files for enhanced_* imports"""
    log_status("Scanning for enhanced_* imports...")
    
    project_root = Path(".").resolve()
    files_with_enhanced_imports = {}
    
    # Get all Python files, excluding venv
    python_files = [f for f in project_root.rglob("*.py") if "venv" not in str(f)]
    
    for file_path in python_files:
        import_analysis = check_import_syntax(file_path)
        if import_analysis["enhanced_count"] > 0:
            rel_path = str(file_path.relative_to(project_root))
            files_with_enhanced_imports[rel_path] = import_analysis["enhanced_imports"]
    
    log_status(f"Found {len(files_with_enhanced_imports)} files with enhanced_* imports")
    return files_with_enhanced_imports

def check_models_init() -> Dict[str, Any]:
    """Check the models/__init__.py file"""
    log_status("Checking models/__init__.py...")
    
    init_file = Path("models/models/__init__.py")
    if not init_file.exists():
        return {"exists": False, "error": "models/__init__.py not found"}
    
    # Validate syntax
    syntax_valid, syntax_error = validate_syntax(init_file)
    
    # Analyze imports
    import_analysis = check_import_syntax(init_file)
    
    return {
        "exists": True,
        "syntax_valid": syntax_valid,
        "syntax_error": syntax_error,
        "import_analysis": import_analysis
    }

def run_lightweight_validation():
    """Run lightweight validation without app initialization"""
    log_status("=" * 60)
    log_status("LIGHTWEIGHT INTEGRATION VALIDATION")
    log_status("=" * 60)
    
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "enhanced_model_analysis": analyze_enhanced_model_files(),
        "enhanced_import_scan": scan_for_enhanced_imports(),
        "models_init_analysis": check_models_init()
    }
    
    # Summary
    log_status("=" * 60)
    log_status("VALIDATION SUMMARY")
    log_status("=" * 60)
    
    critical_errors = []
    warnings = []
    
    # Check enhanced model files
    for file_path, analysis in results["enhanced_model_analysis"].items():
        if not analysis.get("exists"):
            critical_errors.append(f"Missing file: {file_path}")
        elif not analysis.get("syntax_valid"):
            critical_errors.append(f"Syntax error in {file_path}: {analysis.get('syntax_error')}")
    
    # Check models init
    models_init = results["models_init_analysis"]
    if not models_init.get("exists"):
        critical_errors.append("Missing models/__init__.py")
    elif not models_init.get("syntax_valid"):
        critical_errors.append(f"Syntax error in models/__init__.py: {models_init.get('syntax_error')}")
    
    # Report import dependencies
    import_files = results["enhanced_import_scan"]
    log_status(f"Files depending on enhanced_* models: {len(import_files)}")
    for file_path, imports in import_files.items():
        log_status(f"  {file_path}: {len(imports)} enhanced imports")
    
    if critical_errors:
        log_status(f"✗ {len(critical_errors)} CRITICAL ERRORS", "ERROR")
        for error in critical_errors:
            log_status(f"  - {error}", "ERROR")
    else:
        log_status("✓ NO CRITICAL SYNTAX/STRUCTURE ERRORS")
    
    if warnings:
        log_status(f"⚠ {len(warnings)} warnings", "WARNING")
        for warning in warnings:
            log_status(f"  - {warning}", "WARNING")
    
    system_healthy = len(critical_errors) == 0
    log_status(f"STRUCTURE STATUS: {'HEALTHY' if system_healthy else 'UNHEALTHY'}")
    
    results["critical_errors"] = critical_errors
    results["warnings"] = warnings
    results["system_healthy"] = system_healthy
    
    return results

if __name__ == "__main__":
    results = run_lightweight_validation()
    
    # Write results to file
    import json
    with open("lightweight_validation_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    sys.exit(0 if results["system_healthy"] else 1)