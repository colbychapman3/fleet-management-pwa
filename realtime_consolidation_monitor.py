#!/usr/bin/env python3
"""
Real-time Consolidation Monitor - Agent 4
Monitors file system changes and validates integrity during consolidation
"""

import os
import sys
import json
import time
import ast
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationResult:
    success: bool
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class FileState:
    path: str
    exists: bool
    size: int
    mtime: float
    hash: str
    syntax_valid: bool
    syntax_error: Optional[str] = None

class ConsolidationMonitor:
    def __init__(self):
        self.project_root = Path(".").resolve()
        self.monitoring_active = False
        self.file_states = {}
        self.validation_history = []
        self.critical_errors = []
        self.warnings = []
        
        # Load import matrix for reference
        self.import_matrix = self._load_import_matrix()
        self.critical_files = self._get_critical_files()
        
    def log_status(self, message: str, level: str = "INFO"):
        """Log status with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level}] MONITOR: {message}")
        
        # Also log to validation history
        self.validation_history.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
    
    def _load_import_matrix(self) -> Dict[str, Any]:
        """Load the import validation matrix"""
        try:
            with open("import_validation_matrix.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.log_status("Import matrix not found - limited monitoring capabilities", "WARNING")
            return {}
    
    def _get_critical_files(self) -> List[str]:
        """Get list of critical files from import matrix"""
        if not self.import_matrix:
            # Fallback to hardcoded critical files
            return [
                "models/models/enhanced_vessel.py",
                "models/models/enhanced_task.py",
                "models/models/__init__.py",
                "app.py",
                "run_migrations.py"
            ]
        
        critical_files = []
        
        # Add enhanced model files
        for model_name, model_info in self.import_matrix.get("enhanced_models", {}).items():
            critical_files.append(model_info["file_path"])
        
        # Add critical dependent files
        consolidation_impact = self.import_matrix.get("consolidation_impact", {})
        critical_files.extend(consolidation_impact.get("critical_files", []))
        
        return list(set(critical_files))  # Remove duplicates
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file contents"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _validate_file_syntax(self, file_path: Path) -> ValidationResult:
        """Validate Python file syntax"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content, filename=str(file_path))
            return ValidationResult(success=True)
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            return ValidationResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Parse error: {str(e)}"
            return ValidationResult(success=False, error=error_msg)
    
    def _test_import_resolution(self, file_path: str) -> ValidationResult:
        """Test if imports in a file resolve correctly"""
        try:
            # Get the file's imports from the matrix
            if self.import_matrix and file_path in self.import_matrix.get("dependent_files", {}):
                imports = self.import_matrix["dependent_files"][file_path]["import_statements"]
                
                # Change to project root for import testing
                original_path = sys.path.copy()
                if str(self.project_root) not in sys.path:
                    sys.path.insert(0, str(self.project_root))
                
                failed_imports = []
                for import_stmt in imports:
                    try:
                        if import_stmt.startswith("from "):
                            # from module import item
                            parts = import_stmt.replace("from ", "").split(" import ")
                            module_name = parts[0].strip()
                            import_items = [item.strip() for item in parts[1].split(",")]
                            
                            # Test import (but don't actually import to avoid side effects)
                            import importlib.util
                            spec = importlib.util.find_spec(module_name)
                            if spec is None:
                                failed_imports.append(f"{import_stmt} - module not found")
                        
                        elif import_stmt.startswith("import "):
                            # import module
                            module_name = import_stmt.replace("import ", "").strip()
                            import importlib.util
                            spec = importlib.util.find_spec(module_name)
                            if spec is None:
                                failed_imports.append(f"{import_stmt} - module not found")
                    
                    except Exception as e:
                        failed_imports.append(f"{import_stmt} - {str(e)}")
                
                if failed_imports:
                    return ValidationResult(
                        success=False, 
                        error=f"Import failures: {'; '.join(failed_imports)}",
                        details={"failed_imports": failed_imports}
                    )
                else:
                    return ValidationResult(success=True)
                    
            else:
                # File not in matrix - assume imports are OK
                return ValidationResult(success=True, details={"note": "File not in import matrix"})
                
        except Exception as e:
            return ValidationResult(success=False, error=f"Import test failed: {str(e)}")
        finally:
            if 'original_path' in locals():
                sys.path = original_path
    
    def capture_baseline_state(self) -> Dict[str, FileState]:
        """Capture current state of all critical files"""
        self.log_status("Capturing baseline file states...")
        
        baseline_states = {}
        
        for file_path_str in self.critical_files:
            file_path = self.project_root / file_path_str
            
            if file_path.exists():
                stat = file_path.stat()
                syntax_result = self._validate_file_syntax(file_path)
                
                state = FileState(
                    path=file_path_str,
                    exists=True,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                    hash=self._get_file_hash(file_path),
                    syntax_valid=syntax_result.success,
                    syntax_error=syntax_result.error
                )
            else:
                state = FileState(
                    path=file_path_str,
                    exists=False,
                    size=0,
                    mtime=0,
                    hash="",
                    syntax_valid=False,
                    syntax_error="File does not exist"
                )
            
            baseline_states[file_path_str] = state
            
            if state.exists and state.syntax_valid:
                self.log_status(f"✓ {file_path_str} - baseline captured")
            elif state.exists and not state.syntax_valid:
                self.log_status(f"✗ {file_path_str} - syntax error: {state.syntax_error}", "ERROR")
                self.critical_errors.append(f"Baseline syntax error in {file_path_str}: {state.syntax_error}")
            else:
                self.log_status(f"✗ {file_path_str} - file missing", "ERROR")
                self.critical_errors.append(f"Missing file in baseline: {file_path_str}")
        
        self.file_states = baseline_states
        return baseline_states
    
    def validate_consolidation_step(self, step_name: str, modified_files: List[str]) -> ValidationResult:
        """Validate a specific consolidation step"""
        self.log_status(f"🔍 Validating consolidation step: {step_name}")
        
        step_start_time = time.time()
        step_errors = []
        step_warnings = []
        
        # Check each modified file
        for file_path_str in modified_files:
            file_path = self.project_root / file_path_str
            
            # Update file state
            new_state = self._capture_file_state(file_path_str)
            old_state = self.file_states.get(file_path_str)
            
            # Validate changes
            if new_state.exists:
                # Syntax validation
                if not new_state.syntax_valid:
                    error_msg = f"Syntax error in {file_path_str}: {new_state.syntax_error}"
                    step_errors.append(error_msg)
                    self.log_status(f"✗ {error_msg}", "ERROR")
                else:
                    self.log_status(f"✓ {file_path_str} - syntax valid")
                
                # Import validation for files with enhanced imports
                import_result = self._test_import_resolution(file_path_str)
                if not import_result.success:
                    error_msg = f"Import error in {file_path_str}: {import_result.error}"
                    step_errors.append(error_msg)
                    self.log_status(f"✗ {error_msg}", "ERROR")
                else:
                    self.log_status(f"✓ {file_path_str} - imports valid")
                
                # Change detection
                if old_state and old_state.exists:
                    if new_state.hash != old_state.hash:
                        self.log_status(f"📝 {file_path_str} - content changed")
                    if new_state.size != old_state.size:
                        size_diff = new_state.size - old_state.size
                        self.log_status(f"📏 {file_path_str} - size changed by {size_diff:+d} bytes")
            
            else:
                if old_state and old_state.exists:
                    error_msg = f"File deleted: {file_path_str}"
                    step_errors.append(error_msg)
                    self.log_status(f"✗ {error_msg}", "ERROR")
            
            # Update state tracking
            self.file_states[file_path_str] = new_state
        
        # Overall step validation
        step_duration = time.time() - step_start_time
        step_success = len(step_errors) == 0
        
        if step_success:
            self.log_status(f"✅ Step '{step_name}' completed successfully in {step_duration:.2f}s")
        else:
            self.log_status(f"🛑 Step '{step_name}' FAILED with {len(step_errors)} errors", "ERROR")
            self.critical_errors.extend(step_errors)
        
        if step_warnings:
            self.warnings.extend(step_warnings)
        
        return ValidationResult(
            success=step_success,
            error=f"{len(step_errors)} errors" if step_errors else None,
            details={
                "step_name": step_name,
                "duration": step_duration,
                "modified_files": modified_files,
                "errors": step_errors,
                "warnings": step_warnings
            }
        )
    
    def _capture_file_state(self, file_path_str: str) -> FileState:
        """Capture current state of a single file"""
        file_path = self.project_root / file_path_str
        
        if file_path.exists():
            stat = file_path.stat()
            syntax_result = self._validate_file_syntax(file_path)
            
            return FileState(
                path=file_path_str,
                exists=True,
                size=stat.st_size,
                mtime=stat.st_mtime,
                hash=self._get_file_hash(file_path),
                syntax_valid=syntax_result.success,
                syntax_error=syntax_result.error
            )
        else:
            return FileState(
                path=file_path_str,
                exists=False,
                size=0,
                mtime=0,
                hash="",
                syntax_valid=False,
                syntax_error="File does not exist"
            )
    
    def generate_go_no_go_decision(self) -> Dict[str, Any]:
        """Generate go/no-go decision for consolidation"""
        self.log_status("🎯 Generating go/no-go decision...")
        
        # Count issues
        critical_error_count = len(self.critical_errors)
        warning_count = len(self.warnings)
        
        # Analyze file states
        total_files = len(self.file_states)
        healthy_files = sum(1 for state in self.file_states.values() 
                          if state.exists and state.syntax_valid)
        missing_files = sum(1 for state in self.file_states.values() if not state.exists)
        syntax_error_files = sum(1 for state in self.file_states.values() 
                               if state.exists and not state.syntax_valid)
        
        # Decision logic
        go_decision = (
            critical_error_count == 0 and 
            missing_files == 0 and 
            syntax_error_files == 0
        )
        
        decision = {
            "decision": "GO" if go_decision else "NO-GO",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files_monitored": total_files,
                "healthy_files": healthy_files,
                "missing_files": missing_files,
                "syntax_error_files": syntax_error_files,
                "critical_errors": critical_error_count,
                "warnings": warning_count
            },
            "critical_errors": self.critical_errors,
            "warnings": self.warnings,
            "recommendation": self._get_recommendation(go_decision, critical_error_count, warning_count)
        }
        
        # Log decision
        if go_decision:
            self.log_status("✅ GO DECISION: System is healthy for consolidation")
        else:
            self.log_status("🛑 NO-GO DECISION: Critical issues detected", "ERROR")
        
        return decision
    
    def _get_recommendation(self, go_decision: bool, error_count: int, warning_count: int) -> str:
        """Get recommendation based on current state"""
        if go_decision:
            if warning_count == 0:
                return "System is healthy. Proceed with consolidation with confidence."
            else:
                return f"System is healthy but has {warning_count} warnings. Proceed with caution."
        else:
            if error_count > 0:
                return f"HALT CONSOLIDATION. {error_count} critical errors must be resolved before proceeding."
            else:
                return "System state is unclear. Investigate before proceeding."
    
    def save_monitoring_report(self, filename: str = "consolidation_monitoring_report.json"):
        """Save complete monitoring report"""
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "monitor_version": "1.0"
            },
            "file_states": {
                path: {
                    "exists": state.exists,
                    "size": state.size,
                    "syntax_valid": state.syntax_valid,
                    "syntax_error": state.syntax_error,
                    "hash": state.hash
                }
                for path, state in self.file_states.items()
            },
            "validation_history": self.validation_history,
            "critical_errors": self.critical_errors,
            "warnings": self.warnings,
            "go_no_go_decision": self.generate_go_no_go_decision()
        }
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        
        self.log_status(f"Monitoring report saved to {filename}")

def main():
    monitor = ConsolidationMonitor()
    
    # Capture baseline
    monitor.capture_baseline_state()
    
    # Generate initial go/no-go decision
    decision = monitor.generate_go_no_go_decision()
    
    # Save report
    monitor.save_monitoring_report()
    
    # Print summary
    print("\n" + "="*60)
    print("CONSOLIDATION READINESS ASSESSMENT")
    print("="*60)
    print(f"Decision: {decision['decision']}")
    print(f"Recommendation: {decision['recommendation']}")
    print(f"Files monitored: {decision['summary']['total_files_monitored']}")
    print(f"Healthy files: {decision['summary']['healthy_files']}")
    print(f"Critical errors: {decision['summary']['critical_errors']}")
    print(f"Warnings: {decision['summary']['warnings']}")
    
    # Exit with appropriate code
    sys.exit(0 if decision['decision'] == 'GO' else 1)

if __name__ == "__main__":
    main()