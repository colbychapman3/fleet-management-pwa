#!/usr/bin/env python3
"""
Test script to check for model relationship issues
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that all models can be imported without errors"""
    print("Testing model imports...")
    
    try:
        # Test basic imports
        from models.models.enhanced_user import User
        print("✓ User model imported successfully")
        
        from models.models.enhanced_vessel import Vessel
        print("✓ Vessel model imported successfully")
        
        from models.models.enhanced_task import Task
        print("✓ Task model imported successfully")
        
        from models.models.equipment_assignment import EquipmentAssignment
        print("✓ EquipmentAssignment model imported successfully")
        
        from models.models.operation_assignment import OperationAssignment
        print("✓ OperationAssignment model imported successfully")
        
        from models.models.work_time_log import WorkTimeLog
        print("✓ WorkTimeLog model imported successfully")
        
        from models.models.cargo_batch import CargoBatch
        print("✓ CargoBatch model imported successfully")
        
        from models.maritime.ship_operation import ShipOperation
        print("✓ ShipOperation model imported successfully")
        
        from models.maritime.stevedore_team import StevedoreTeam
        print("✓ StevedoreTeam model imported successfully")
        
        print("\n✓ All model imports successful!")
        return True
        
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        return False

def test_relationship_conflicts():
    """Test for relationship conflicts"""
    print("\nTesting relationship conflicts...")
    
    try:
        # Try to create a simple Flask app context
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        # Import models after setting up app context
        with app.app_context():
            from models.models.enhanced_vessel import Vessel
            from models.models.equipment_assignment import EquipmentAssignment
            from models.models.operation_assignment import OperationAssignment
            
            # Try to create tables
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Test that relationships work
            vessel = Vessel(name="Test Vessel")
            db.session.add(vessel)
            db.session.commit()
            
            # Test equipment assignment relationship
            equipment = EquipmentAssignment(
                user_id=1,
                vessel_id=vessel.id,
                equipment_type="crane",
                equipment_id="CR001"
            )
            db.session.add(equipment)
            db.session.commit()
            
            # Test that relationship works
            assert vessel.equipment_assignments.count() == 1
            print("✓ Equipment assignment relationship works")
            
            # Test operation assignment relationship
            operation = OperationAssignment(
                user_id=1,
                operation_id=1,
                vessel_id=vessel.id,
                role="operator"
            )
            db.session.add(operation)
            db.session.commit()
            
            # Test that relationship works
            assert vessel.operation_assignments.count() == 1
            print("✓ Operation assignment relationship works")
            
        print("\n✓ All relationship tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Relationship test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Fleet Management System - Model Relationship Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_model_imports()
    
    if imports_ok:
        # Test relationships
        relationships_ok = test_relationship_conflicts()
        
        if relationships_ok:
            print("\n🎉 All tests passed! The relationship conflicts have been resolved.")
            print("Your application should now deploy successfully.")
        else:
            print("\n❌ Relationship tests failed. Check the errors above.")
    else:
        print("\n❌ Model import tests failed. Fix import issues first.")

if __name__ == "__main__":
    main()