#!/usr/bin/env python3
"""
Import Validation Matrix - Agent 4
Comprehensive mapping and validation of all enhanced_* import dependencies
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Set

class ImportValidationMatrix:
    def __init__(self):
        self.project_root = Path(".").resolve()
        self.matrix = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "project_root": str(self.project_root),
                "validation_version": "1.0"
            },
            "enhanced_models": {},
            "dependent_files": {},
            "import_patterns": {},
            "consolidation_impact": {}
        }
        
    def log_status(self, message: str, level: str = "INFO"):
        """Log status messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] MATRIX: {message}")
    
    def load_validation_data(self):
        """Load existing validation data"""
        try:
            with open("lightweight_validation_report.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.log_status("No validation report found - run lightweight_validator.py first", "WARNING")
            return None
    
    def build_enhanced_models_map(self, validation_data: Dict[str, Any]):
        """Map enhanced model files and their properties"""
        self.log_status("Building enhanced models map...")
        
        for file_path, analysis in validation_data["enhanced_model_analysis"].items():
            model_info = {
                "file_path": file_path,
                "exists": analysis["exists"],
                "syntax_valid": analysis["syntax_valid"],
                "classes": [],
                "dependencies": analysis["import_analysis"]["all_imports"],
                "internal_enhanced_imports": analysis["import_analysis"]["enhanced_imports"]
            }
            
            if "model_info" in analysis:
                model_info["classes"] = analysis["model_info"]["classes"]
                model_info["has_sqlalchemy_models"] = analysis["model_info"]["has_sqlalchemy_models"]
            
            # Extract model name from file path
            model_name = Path(file_path).stem  # e.g., "enhanced_vessel" -> "enhanced_vessel"
            self.matrix["enhanced_models"][model_name] = model_info
    
    def build_dependent_files_map(self, validation_data: Dict[str, Any]):
        """Map all files that depend on enhanced models"""
        self.log_status("Building dependent files map...")
        
        enhanced_imports = validation_data["enhanced_import_scan"]
        
        for file_path, imports in enhanced_imports.items():
            # Analyze import patterns
            import_patterns = self._analyze_import_patterns(imports)
            
            # Categorize file type
            file_category = self._categorize_file(file_path)
            
            self.matrix["dependent_files"][file_path] = {
                "import_statements": imports,
                "import_count": len(imports),
                "import_patterns": import_patterns,
                "file_category": file_category,
                "criticality": self._assess_criticality(file_path, file_category),
                "consolidation_risk": self._assess_consolidation_risk(imports)
            }
    
    def _analyze_import_patterns(self, imports: List[str]) -> Dict[str, Any]:
        """Analyze patterns in import statements"""
        patterns = {
            "direct_imports": [],  # from models.models.enhanced_x import Y
            "module_imports": [],  # import models.models.enhanced_x
            "enhanced_models_used": set(),
            "import_styles": set()
        }
        
        for imp in imports:
            if imp.startswith("from models.models.enhanced_"):
                patterns["direct_imports"].append(imp)
                patterns["import_styles"].add("direct")
                # Extract model name
                model_part = imp.split("from models.models.")[1].split(" import")[0]
                patterns["enhanced_models_used"].add(model_part)
                
            elif imp.startswith("import models.models.enhanced_"):
                patterns["module_imports"].append(imp)
                patterns["import_styles"].add("module")
                # Extract model name
                model_part = imp.replace("import models.models.", "")
                patterns["enhanced_models_used"].add(model_part)
                
            elif "enhanced_" in imp:
                # Relative or other enhanced imports
                patterns["import_styles"].add("other")
                if "enhanced_vessel" in imp:
                    patterns["enhanced_models_used"].add("enhanced_vessel")
                if "enhanced_task" in imp:
                    patterns["enhanced_models_used"].add("enhanced_task")
        
        # Convert set to list for JSON serialization
        patterns["enhanced_models_used"] = list(patterns["enhanced_models_used"])
        patterns["import_styles"] = list(patterns["import_styles"])
        
        return patterns
    
    def _categorize_file(self, file_path: str) -> str:
        """Categorize file by its role in the application"""
        if file_path.startswith("routes/"):
            return "route_handler"
        elif file_path.startswith("models/"):
            return "model_definition"
        elif file_path.startswith("scripts/"):
            return "utility_script"
        elif file_path == "app.py":
            return "main_application"
        elif file_path == "run_migrations.py":
            return "migration_system"
        elif "test" in file_path or "validator" in file_path:
            return "testing_validation"
        else:
            return "other"
    
    def _assess_criticality(self, file_path: str, category: str) -> str:
        """Assess how critical the file is for system operation"""
        critical_files = ["app.py", "run_migrations.py"]
        critical_categories = ["main_application", "migration_system"]
        
        if file_path in critical_files or category in critical_categories:
            return "critical"
        elif category in ["route_handler", "model_definition"]:
            return "high"
        elif category in ["utility_script"]:
            return "medium"
        else:
            return "low"
    
    def _assess_consolidation_risk(self, imports: List[str]) -> str:
        """Assess risk level for consolidation changes"""
        # Higher risk if using multiple import styles or complex imports
        styles = set()
        for imp in imports:
            if imp.startswith("from models.models.enhanced_"):
                styles.add("direct")
            elif imp.startswith("import models.models.enhanced_"):
                styles.add("module")
            else:
                styles.add("other")
        
        if len(styles) > 1:
            return "high"
        elif len(imports) > 1:
            return "medium"
        else:
            return "low"
    
    def build_import_patterns_summary(self):
        """Build summary of import patterns across the codebase"""
        self.log_status("Building import patterns summary...")
        
        patterns_summary = {
            "total_files_with_enhanced_imports": len(self.matrix["dependent_files"]),
            "import_style_distribution": {},
            "model_usage_distribution": {},
            "file_category_distribution": {},
            "criticality_distribution": {},
            "consolidation_risk_distribution": {}
        }
        
        # Analyze distributions
        for file_data in self.matrix["dependent_files"].values():
            # Import styles
            for style in file_data["import_patterns"]["import_styles"]:
                patterns_summary["import_style_distribution"][style] = \
                    patterns_summary["import_style_distribution"].get(style, 0) + 1
            
            # Model usage
            for model in file_data["import_patterns"]["enhanced_models_used"]:
                patterns_summary["model_usage_distribution"][model] = \
                    patterns_summary["model_usage_distribution"].get(model, 0) + 1
            
            # File categories
            category = file_data["file_category"]
            patterns_summary["file_category_distribution"][category] = \
                patterns_summary["file_category_distribution"].get(category, 0) + 1
            
            # Criticality
            criticality = file_data["criticality"]
            patterns_summary["criticality_distribution"][criticality] = \
                patterns_summary["criticality_distribution"].get(criticality, 0) + 1
            
            # Risk
            risk = file_data["consolidation_risk"]
            patterns_summary["consolidation_risk_distribution"][risk] = \
                patterns_summary["consolidation_risk_distribution"].get(risk, 0) + 1
        
        self.matrix["import_patterns"] = patterns_summary
    
    def calculate_consolidation_impact(self):
        """Calculate expected impact of consolidation"""
        self.log_status("Calculating consolidation impact...")
        
        impact = {
            "files_requiring_updates": [],
            "high_risk_files": [],
            "critical_files": [],
            "import_statement_changes": {},
            "validation_checkpoints": []
        }
        
        for file_path, file_data in self.matrix["dependent_files"].items():
            # All files with enhanced imports will need updates
            impact["files_requiring_updates"].append({
                "file": file_path,
                "import_count": file_data["import_count"],
                "risk_level": file_data["consolidation_risk"],
                "criticality": file_data["criticality"]
            })
            
            # Track high-risk files
            if file_data["consolidation_risk"] == "high":
                impact["high_risk_files"].append(file_path)
            
            # Track critical files
            if file_data["criticality"] == "critical":
                impact["critical_files"].append(file_path)
            
            # Map required import changes
            current_imports = file_data["import_statements"]
            new_imports = self._calculate_new_imports(current_imports)
            if current_imports != new_imports:
                impact["import_statement_changes"][file_path] = {
                    "current": current_imports,
                    "new": new_imports,
                    "changes_count": len(current_imports)
                }
        
        # Define validation checkpoints
        impact["validation_checkpoints"] = [
            {
                "name": "Pre-consolidation baseline",
                "description": "Validate current system state",
                "files_to_check": impact["critical_files"]
            },
            {
                "name": "Models consolidation",
                "description": "Validate enhanced_* files are properly merged",
                "files_to_check": ["models/models/vessel.py", "models/models/task.py"]
            },
            {
                "name": "Import updates - critical files",
                "description": "Update imports in critical files first",
                "files_to_check": impact["critical_files"]
            },
            {
                "name": "Import updates - high-risk files", 
                "description": "Update imports in high-risk files",
                "files_to_check": impact["high_risk_files"]
            },
            {
                "name": "Import updates - remaining files",
                "description": "Update imports in remaining files",
                "files_to_check": [f["file"] for f in impact["files_requiring_updates"] 
                                 if f["file"] not in impact["critical_files"] + impact["high_risk_files"]]
            },
            {
                "name": "Final validation",
                "description": "Complete system validation",
                "files_to_check": "all"
            }
        ]
        
        self.matrix["consolidation_impact"] = impact
    
    def _calculate_new_imports(self, current_imports: List[str]) -> List[str]:
        """Calculate what the new import statements should be after consolidation"""
        new_imports = []
        
        for imp in current_imports:
            if "enhanced_vessel" in imp:
                # Replace enhanced_vessel with vessel
                new_imp = imp.replace("enhanced_vessel", "vessel")
                new_imports.append(new_imp)
            elif "enhanced_task" in imp:
                # Replace enhanced_task with task  
                new_imp = imp.replace("enhanced_task", "task")
                new_imports.append(new_imp)
            else:
                # Keep other imports as-is
                new_imports.append(imp)
        
        return new_imports
    
    def generate_validation_checklist(self) -> List[Dict[str, Any]]:
        """Generate detailed validation checklist for consolidation"""
        checklist = []
        
        # Pre-consolidation checks
        checklist.append({
            "phase": "pre_consolidation",
            "step": "baseline_validation",
            "description": "Validate current system state",
            "validation_points": [
                "All enhanced_* files exist and have valid syntax",
                "All import statements resolve correctly",
                "SQLAlchemy models load without errors",
                "No circular import dependencies"
            ],
            "files_to_monitor": list(self.matrix["dependent_files"].keys()),
            "critical_success_criteria": "Zero syntax errors, zero import resolution failures"
        })
        
        # Model consolidation checks
        for checkpoint in self.matrix["consolidation_impact"]["validation_checkpoints"]:
            checklist.append({
                "phase": "consolidation",
                "step": checkpoint["name"].lower().replace(" ", "_"),
                "description": checkpoint["description"],
                "files_to_monitor": checkpoint["files_to_check"],
                "validation_points": [
                    "Syntax validation after changes",
                    "Import resolution testing",
                    "Model loading verification"
                ],
                "rollback_trigger": "Any syntax error or import failure"
            })
        
        return checklist
    
    def save_matrix(self, filename: str = "import_validation_matrix.json"):
        """Save the complete validation matrix"""
        with open(filename, "w") as f:
            json.dump(self.matrix, f, indent=2, default=str)
        self.log_status(f"Matrix saved to {filename}")
    
    def print_summary(self):
        """Print a human-readable summary"""
        print("\n" + "="*60)
        print("IMPORT VALIDATION MATRIX SUMMARY")
        print("="*60)
        
        print(f"\nEnhanced Models: {len(self.matrix['enhanced_models'])}")
        for model_name, model_info in self.matrix["enhanced_models"].items():
            print(f"  • {model_name}: {'✓' if model_info['syntax_valid'] else '✗'}")
        
        print(f"\nDependent Files: {len(self.matrix['dependent_files'])}")
        for category, count in self.matrix["import_patterns"]["file_category_distribution"].items():
            print(f"  • {category}: {count} files")
        
        print(f"\nCriticality Distribution:")
        for level, count in self.matrix["import_patterns"]["criticality_distribution"].items():
            print(f"  • {level}: {count} files")
        
        print(f"\nConsolidation Risk Distribution:")
        for risk, count in self.matrix["import_patterns"]["consolidation_risk_distribution"].items():
            print(f"  • {risk}: {count} files")
        
        impact = self.matrix["consolidation_impact"]
        print(f"\nConsolidation Impact:")
        print(f"  • Files requiring updates: {len(impact['files_requiring_updates'])}")
        print(f"  • High-risk files: {len(impact['high_risk_files'])}")
        print(f"  • Critical files: {len(impact['critical_files'])}")
        print(f"  • Validation checkpoints: {len(impact['validation_checkpoints'])}")

def main():
    matrix_builder = ImportValidationMatrix()
    
    # Load validation data
    validation_data = matrix_builder.load_validation_data()
    if not validation_data:
        print("ERROR: Cannot build matrix without validation data")
        return
    
    # Build the matrix
    matrix_builder.build_enhanced_models_map(validation_data)
    matrix_builder.build_dependent_files_map(validation_data)
    matrix_builder.build_import_patterns_summary()
    matrix_builder.calculate_consolidation_impact()
    
    # Save and display
    matrix_builder.save_matrix()
    matrix_builder.print_summary()
    
    # Generate validation checklist
    checklist = matrix_builder.generate_validation_checklist()
    with open("consolidation_validation_checklist.json", "w") as f:
        json.dump(checklist, f, indent=2)
    matrix_builder.log_status("Validation checklist saved to consolidation_validation_checklist.json")

if __name__ == "__main__":
    main()