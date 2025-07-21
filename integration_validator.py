#!/usr/bin/env python3
"""
Integration Validator - Agent 4
Real-time validation of system integrity during consolidation
"""

import os
import sys
import ast
import importlib.util
import inspect
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import time

class IntegrationValidator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.validation_results = {}
        self.import_matrix = {}
        self.model_registry = {}
        self.critical_errors = []
        self.warnings = []
        
    def log_status(self, message: str, level: str = "INFO"):
        """Log status messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def validate_syntax(self, file_path: Path) -> Tuple[bool, Optional[str]]:
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
    
    def test_import_resolution(self, import_statement: str, description: str = "") -> Tuple[bool, Optional[str]]:
        """Test if an import statement resolves correctly"""
        try:
            # Change to project root for import testing
            original_path = sys.path.copy()
            if str(self.project_root) not in sys.path:
                sys.path.insert(0, str(self.project_root))
            
            # Handle different import types
            if import_statement.startswith("from "):
                # from module import item
                parts = import_statement.replace("from ", "").split(" import ")
                module_name = parts[0].strip()
                import_items = [item.strip() for item in parts[1].split(",")]
                
                module = importlib.import_module(module_name)
                for item in import_items:
                    if not hasattr(module, item):
                        return False, f"Module {module_name} has no attribute {item}"
                        
            elif import_statement.startswith("import "):
                # import module
                module_name = import_statement.replace("import ", "").strip()
                importlib.import_module(module_name)
            
            return True, None
            
        except ImportError as e:
            return False, f"Import error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
        finally:
            sys.path = original_path
    
    def validate_enhanced_imports(self) -> Dict[str, Any]:
        """Validate all enhanced_* model imports"""
        self.log_status("Validating enhanced_* model imports...")
        
        enhanced_imports = [
            ("import models.models.enhanced_vessel", "Enhanced Vessel module import"),
            ("import models.models.enhanced_task", "Enhanced Task module import"),
            ("from models.models.enhanced_vessel import Vessel", "Direct Vessel import"),
            ("from models.models.enhanced_task import Task", "Direct Task import"),
            ("from models.models import Vessel, Task", "Models package import"),
        ]
        
        results = {}
        for import_stmt, desc in enhanced_imports:
            success, error = self.test_import_resolution(import_stmt, desc)
            results[import_stmt] = {
                "success": success,
                "error": error,
                "description": desc
            }
            
            if success:
                self.log_status(f"✓ {desc}")
            else:
                self.log_status(f"✗ {desc}: {error}", "ERROR")
                self.critical_errors.append(f"Import failure: {desc} - {error}")
        
        return results
    
    def validate_file_existence(self) -> Dict[str, bool]:
        """Validate that all referenced files exist"""
        self.log_status("Validating file existence...")
        
        critical_files = [
            "models/models/enhanced_vessel.py",
            "models/models/enhanced_task.py", 
            "models/models/__init__.py",
            "app.py",
            "run_migrations.py"
        ]
        
        results = {}
        for file_path in critical_files:
            full_path = self.project_root / file_path
            exists = full_path.exists()
            results[file_path] = exists
            
            if exists:
                self.log_status(f"✓ {file_path}")
            else:
                self.log_status(f"✗ {file_path} - FILE NOT FOUND", "ERROR")
                self.critical_errors.append(f"Missing file: {file_path}")
        
        return results
    
    def validate_syntax_all_files(self) -> Dict[str, Any]:
        """Validate syntax of all Python files"""
        self.log_status("Validating Python file syntax...")
        
        results = {}
        python_files = list(self.project_root.rglob("*.py"))
        
        # Filter out venv files
        python_files = [f for f in python_files if "venv" not in str(f)]
        
        for file_path in python_files:
            rel_path = file_path.relative_to(self.project_root)
            success, error = self.validate_syntax(file_path)
            results[str(rel_path)] = {
                "success": success,
                "error": error
            }
            
            if not success:
                self.log_status(f"✗ Syntax error in {rel_path}: {error}", "ERROR")
                self.critical_errors.append(f"Syntax error in {rel_path}: {error}")
        
        syntax_errors = sum(1 for r in results.values() if not r["success"])
        if syntax_errors == 0:
            self.log_status(f"✓ All {len(results)} Python files have valid syntax")
        else:
            self.log_status(f"✗ {syntax_errors} files have syntax errors", "ERROR")
        
        return results
    
    def validate_sqlalchemy_models(self) -> Dict[str, Any]:
        """Validate SQLAlchemy model loading and relationships"""
        self.log_status("Validating SQLAlchemy models...")
        
        try:
            # Add project root to path
            original_path = sys.path.copy()
            if str(self.project_root) not in sys.path:
                sys.path.insert(0, str(self.project_root))
            
            # Import models
            from models.models.enhanced_vessel import Vessel
            from models.models.enhanced_task import Task
            
            results = {
                "vessel_model": self._analyze_model(Vessel, "Vessel"),
                "task_model": self._analyze_model(Task, "Task"),
                "relationship_validation": self._validate_relationships(Vessel, Task)
            }
            
            self.log_status("✓ SQLAlchemy models loaded successfully")
            return results
            
        except Exception as e:
            error_msg = f"Failed to load SQLAlchemy models: {str(e)}"
            self.log_status(f"✗ {error_msg}", "ERROR")
            self.critical_errors.append(error_msg)
            return {"error": error_msg, "traceback": traceback.format_exc()}
        finally:
            sys.path = original_path
    
    def _analyze_model(self, model_class, name: str) -> Dict[str, Any]:
        """Analyze a SQLAlchemy model class"""
        try:
            # Check if it's a SQLAlchemy model
            if not hasattr(model_class, '__table__'):
                return {"error": f"{name} is not a SQLAlchemy model"}
            
            # Get table info
            table = model_class.__table__
            columns = [col.name for col in table.columns]
            
            # Get relationships
            relationships = []
            if hasattr(model_class, '__mapper__'):
                for rel in model_class.__mapper__.relationships:
                    relationships.append({
                        "name": rel.key,
                        "target": str(rel.mapper.class_),
                        "direction": str(rel.direction)
                    })
            
            return {
                "table_name": table.name,
                "columns": columns,
                "relationships": relationships,
                "column_count": len(columns),
                "relationship_count": len(relationships)
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze {name}: {str(e)}"}
    
    def _validate_relationships(self, vessel_class, task_class) -> Dict[str, Any]:
        """Validate model relationships"""
        try:
            results = {}
            
            # Check Vessel relationships
            if hasattr(vessel_class, '__mapper__'):
                vessel_rels = [rel.key for rel in vessel_class.__mapper__.relationships]
                results["vessel_relationships"] = vessel_rels
                
                # Check for tasks relationship
                if 'tasks' in vessel_rels:
                    results["vessel_has_tasks_relationship"] = True
                else:
                    self.warnings.append("Vessel model missing 'tasks' relationship")
                    results["vessel_has_tasks_relationship"] = False
            
            # Check Task relationships  
            if hasattr(task_class, '__mapper__'):
                task_rels = [rel.key for rel in task_class.__mapper__.relationships]
                results["task_relationships"] = task_rels
                
                # Check for vessel relationship
                if 'vessel' in task_rels:
                    results["task_has_vessel_relationship"] = True
                else:
                    self.warnings.append("Task model missing 'vessel' relationship")
                    results["task_has_vessel_relationship"] = False
            
            return results
            
        except Exception as e:
            return {"error": f"Relationship validation failed: {str(e)}"}
    
    def run_baseline_validation(self) -> Dict[str, Any]:
        """Run complete baseline system validation"""
        self.log_status("=" * 60)
        self.log_status("STARTING BASELINE SYSTEM VALIDATION")
        self.log_status("=" * 60)
        
        baseline_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file_existence": self.validate_file_existence(),
            "syntax_validation": self.validate_syntax_all_files(),
            "import_validation": self.validate_enhanced_imports(),
            "sqlalchemy_validation": self.validate_sqlalchemy_models(),
            "critical_errors": self.critical_errors,
            "warnings": self.warnings
        }
        
        # Summary
        self.log_status("=" * 60)
        self.log_status("BASELINE VALIDATION SUMMARY")
        self.log_status("=" * 60)
        
        if self.critical_errors:
            self.log_status(f"✗ {len(self.critical_errors)} CRITICAL ERRORS DETECTED", "ERROR")
            for error in self.critical_errors:
                self.log_status(f"  - {error}", "ERROR")
        else:
            self.log_status("✓ NO CRITICAL ERRORS DETECTED")
        
        if self.warnings:
            self.log_status(f"⚠ {len(self.warnings)} warnings", "WARNING")
            for warning in self.warnings:
                self.log_status(f"  - {warning}", "WARNING")
        
        # System status
        system_healthy = len(self.critical_errors) == 0
        self.log_status(f"SYSTEM STATUS: {'HEALTHY' if system_healthy else 'UNHEALTHY'}")
        
        if not system_healthy:
            self.log_status("🛑 CONSOLIDATION SHOULD NOT PROCEED", "ERROR")
        else:
            self.log_status("✅ SYSTEM READY FOR CONSOLIDATION")
        
        baseline_results["system_healthy"] = system_healthy
        return baseline_results
    
    def monitor_consolidation_step(self, step_name: str, modified_files: List[str]) -> Dict[str, Any]:
        """Monitor a specific consolidation step"""
        self.log_status(f"Monitoring consolidation step: {step_name}")
        
        step_results = {
            "step_name": step_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modified_files": modified_files,
            "file_validation": {},
            "import_validation": {}
        }
        
        # Validate modified files
        for file_path in modified_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                success, error = self.validate_syntax(full_path)
                step_results["file_validation"][file_path] = {
                    "syntax_valid": success,
                    "error": error
                }
                
                if not success:
                    self.critical_errors.append(f"Syntax error in {file_path} after {step_name}: {error}")
        
        # Re-test critical imports
        import_results = self.validate_enhanced_imports()
        step_results["import_validation"] = import_results
        
        # Check for new critical errors
        step_healthy = all(
            result["syntax_valid"] for result in step_results["file_validation"].values()
        ) and all(
            result["success"] for result in import_results.values()
        )
        
        step_results["step_healthy"] = step_healthy
        
        if step_healthy:
            self.log_status(f"✅ Step '{step_name}' completed successfully")
        else:
            self.log_status(f"🛑 Step '{step_name}' introduced errors - HALT CONSOLIDATION", "ERROR")
        
        return step_results

if __name__ == "__main__":
    validator = IntegrationValidator()
    results = validator.run_baseline_validation()
    
    # Write results to file
    import json
    with open("baseline_validation_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Exit with appropriate code
    sys.exit(0 if results["system_healthy"] else 1)