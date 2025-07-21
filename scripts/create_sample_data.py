#!/usr/bin/env python3
"""
Sample Data Creator for Operations Dashboard
Creates sample ship operations, stevedore teams, and vessel data for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.models.enhanced_vessel import Vessel
from models.models.user import User
from models.maritime.ship_operation import ShipOperation
from models.maritime.stevedore_team import StevedoreTeam, StevedoreTeamMember
from datetime import datetime, timedelta
import random

def create_sample_vessels():
    """Create sample vessels"""
    vessels_data = [
        {
            'name': 'MV ATLANTIC STAR',
            'imo_number': 'IMO1234567',
            'vessel_type': 'Container Ship',
            'gross_tonnage': 95000,
            'deadweight_tonnage': 105000,
            'length': 334,
            'beam': 43,
            'draft': 14.5,
            'flag_state': 'Liberia',
            'call_sign': 'A8BC123',
            'classification_society': 'Lloyds Register'
        },
        {
            'name': 'MV PACIFIC HORIZON',
            'imo_number': 'IMO2345678',
            'vessel_type': 'Bulk Carrier',
            'gross_tonnage': 85000,
            'deadweight_tonnage': 98000,
            'length': 280,
            'beam': 45,
            'draft': 16.2,
            'flag_state': 'Panama',
            'call_sign': 'HP8234',
            'classification_society': 'ABS'
        },
        {
            'name': 'MV BALTIC BREEZE',
            'imo_number': 'IMO3456789',
            'vessel_type': 'General Cargo',
            'gross_tonnage': 25000,
            'deadweight_tonnage': 35000,
            'length': 180,
            'beam': 28,
            'draft': 10.5,
            'flag_state': 'Marshall Islands',
            'call_sign': 'V7AB123',
            'classification_society': 'DNV GL'
        },
        {
            'name': 'MV NORTHERN LIGHT',
            'imo_number': 'IMO4567890',
            'vessel_type': 'Tanker',
            'gross_tonnage': 75000,
            'deadweight_tonnage': 115000,
            'length': 250,
            'beam': 44,
            'draft': 15.8,
            'flag_state': 'Singapore',
            'call_sign': 'S6XY789',
            'classification_society': 'BV'
        },
        {
            'name': 'MV SOUTHERN CROSS',
            'imo_number': 'IMO5678901',
            'vessel_type': 'Container Ship',
            'gross_tonnage': 120000,
            'deadweight_tonnage': 140000,
            'length': 380,
            'beam': 48,
            'draft': 16.0,
            'flag_state': 'Hong Kong',
            'call_sign': 'VR2DEF',
            'classification_society': 'CCS'
        }
    ]
    
    vessels = []
    for vessel_data in vessels_data:
        vessel = Vessel.query.filter_by(imo_number=vessel_data['imo_number']).first()
        if not vessel:
            vessel = Vessel(**vessel_data)
            db.session.add(vessel)
            vessels.append(vessel)
    
    db.session.commit()
    return vessels

def create_sample_users():
    """Create sample users for teams"""
    users_data = [
        {'username': 'john_smith', 'first_name': 'John', 'last_name': 'Smith', 'role': 'manager'},
        {'username': 'mary_johnson', 'first_name': 'Mary', 'last_name': 'Johnson', 'role': 'worker'},
        {'username': 'david_brown', 'first_name': 'David', 'last_name': 'Brown', 'role': 'worker'},
        {'username': 'lisa_wilson', 'first_name': 'Lisa', 'last_name': 'Wilson', 'role': 'worker'},
        {'username': 'mike_davis', 'first_name': 'Mike', 'last_name': 'Davis', 'role': 'worker'},
        {'username': 'sarah_miller', 'first_name': 'Sarah', 'last_name': 'Miller', 'role': 'worker'},
        {'username': 'tom_garcia', 'first_name': 'Tom', 'last_name': 'Garcia', 'role': 'worker'},
        {'username': 'anna_rodriguez', 'first_name': 'Anna', 'last_name': 'Rodriguez', 'role': 'worker'}
    ]
    
    users = []
    for user_data in users_data:
        user = User.query.filter_by(username=user_data['username']).first()
        if not user:
            user = User(
                username=user_data['username'],
                email=f"{user_data['username']}@fleet.com",
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                employee_id=f"EMP{random.randint(1000, 9999)}",
                is_active=True
            )
            user.set_password('password123')  # Default password for demo
            db.session.add(user)
            users.append(user)
    
    db.session.commit()
    return users

def create_sample_teams():
    """Create sample stevedore teams"""
    users = User.query.filter_by(role='worker').all()
    if len(users) < 6:
        print("Not enough users to create teams. Creating users first...")
        users = create_sample_users()
        users = [u for u in users if u.role == 'worker']
    
    teams_data = [
        {
            'team_name': 'Alpha Team',
            'shift_pattern': 'day',
            'zone_assignment': 'BRV',
            'cargo_specialization': ['containers', 'general_cargo'],
            'productivity_rating': 8.5,
            'safety_record': 9.2
        },
        {
            'team_name': 'Bravo Team',
            'shift_pattern': 'night',
            'zone_assignment': 'ZEE',
            'cargo_specialization': ['bulk_cargo', 'grain'],
            'productivity_rating': 7.8,
            'safety_record': 8.9
        },
        {
            'team_name': 'Charlie Team',
            'shift_pattern': 'day',
            'zone_assignment': 'SOU',
            'cargo_specialization': ['liquid_cargo', 'chemicals'],
            'productivity_rating': 9.1,
            'safety_record': 9.5
        },
        {
            'team_name': 'Delta Team',
            'shift_pattern': 'rotating',
            'zone_assignment': None,  # Flexible zone
            'cargo_specialization': ['containers', 'general_cargo', 'project_cargo'],
            'productivity_rating': 8.2,
            'safety_record': 8.7
        }
    ]
    
    teams = []
    for i, team_data in enumerate(teams_data):
        team_id = StevedoreTeam.generate_team_id(team_data['team_name'])
        
        team = StevedoreTeam.query.filter_by(team_name=team_data['team_name']).first()
        if not team:
            # Assign team leader
            leader = users[i] if i < len(users) else users[0]
            
            team = StevedoreTeam(
                team_id=team_id,
                team_name=team_data['team_name'],
                team_leader_id=leader.id,
                shift_pattern=team_data['shift_pattern'],
                zone_assignment=team_data['zone_assignment'],
                cargo_specialization=team_data['cargo_specialization'],
                productivity_rating=team_data['productivity_rating'],
                safety_record=team_data['safety_record'],
                certified_equipment=['crane', 'forklift', 'reach_stacker'],
                status='available'
            )
            db.session.add(team)
            teams.append(team)
    
    db.session.commit()
    
    # Add members to teams
    for i, team in enumerate(teams):
        # Add 2-3 members per team
        start_idx = i * 2
        end_idx = min(start_idx + 3, len(users))
        
        for j in range(start_idx, end_idx):
            if j < len(users):
                user = users[j]
                roles = ['foreman', 'crane_operator', 'signalman', 'general_worker']
                role = roles[j % len(roles)]
                
                team.add_member(user.id, role, hourly_rate=25.0 + random.randint(0, 15))
    
    db.session.commit()
    return teams

def create_sample_operations():
    """Create sample ship operations"""
    vessels = Vessel.query.all()
    teams = StevedoreTeam.query.all()
    
    if not vessels:
        print("No vessels found. Creating vessels first...")
        vessels = create_sample_vessels()
    
    if not teams:
        print("No teams found. Creating teams first...")
        teams = create_sample_teams()
    
    operations_data = [
        {
            'vessel': vessels[0],
            'operation_type': 'discharge',
            'berth_assigned': '1',
            'status': 'in_progress',
            'priority': 'high',
            'current_step': 3,
            'cargo_type': 'containers',
            'total_cargo_quantity': 1500.0,
            'processed_cargo_quantity': 900.0,
            'zone_assignment': 'BRV'
        },
        {
            'vessel': vessels[1],
            'operation_type': 'loading',
            'berth_assigned': '2',
            'status': 'in_progress',
            'priority': 'medium',
            'current_step': 2,
            'cargo_type': 'bulk_grain',
            'total_cargo_quantity': 25000.0,
            'processed_cargo_quantity': 5000.0,
            'zone_assignment': 'ZEE'
        },
        {
            'vessel': vessels[2],
            'operation_type': 'discharge',
            'berth_assigned': None,  # Waiting for berth
            'status': 'initiated',
            'priority': 'urgent',
            'current_step': 1,
            'cargo_type': 'general_cargo',
            'total_cargo_quantity': 800.0,
            'processed_cargo_quantity': 0.0,
            'zone_assignment': 'SOU'
        },
        {
            'vessel': vessels[3],
            'operation_type': 'bunkering',
            'berth_assigned': '3',
            'status': 'in_progress',
            'priority': 'low',
            'current_step': 4,
            'cargo_type': 'fuel_oil',
            'total_cargo_quantity': 2000.0,
            'processed_cargo_quantity': 1800.0,
            'zone_assignment': 'SOU'
        }
    ]
    
    operations = []
    for i, op_data in enumerate(operations_data):
        vessel = op_data['vessel']
        
        # Check if operation already exists for this vessel
        existing_op = ShipOperation.query.filter_by(
            vessel_id=vessel.id,
            status__in=['initiated', 'in_progress']
        ).first()
        
        if not existing_op:
            operation_id = ShipOperation.generate_operation_id(vessel.name, op_data['operation_type'])
            
            operation = ShipOperation(
                operation_id=operation_id,
                vessel_id=vessel.id,
                operation_type=op_data['operation_type'],
                status=op_data['status'],
                priority=op_data['priority'],
                current_step=op_data['current_step'],
                berth_assigned=op_data['berth_assigned'],
                cargo_type=op_data['cargo_type'],
                total_cargo_quantity=op_data['total_cargo_quantity'],
                processed_cargo_quantity=op_data['processed_cargo_quantity'],
                zone_assignment=op_data['zone_assignment'],
                arrival_datetime=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                operation_manager_id=User.query.filter_by(role='manager').first().id if User.query.filter_by(role='manager').first() else None
            )
            
            # Set step completion based on current step
            if operation.current_step >= 1:
                operation.step_1_completed = True
                operation.pilot_embarked = True
                operation.customs_clearance = True
                operation.immigration_clearance = True
                operation.port_health_clearance = True
                operation.manifest_submitted = True
            
            if operation.current_step >= 2:
                operation.step_2_completed = True
                operation.mooring_completed = True
                operation.safety_briefing_completed = True
                operation.berth_assignment_time = datetime.utcnow() - timedelta(hours=random.randint(1, 12))
            
            if operation.current_step >= 3:
                operation.step_3_completed = False  # Still in progress
                operation.cargo_operation_start = datetime.utcnow() - timedelta(hours=random.randint(1, 8))
                # Assign a team
                if teams:
                    available_team = next((t for t in teams if t.is_available_for_assignment()), None)
                    if available_team:
                        operation.stevedore_team_id = available_team.id
                        available_team.assign_to_operation(f"{vessel.name} - {operation.operation_type}")
            
            if operation.current_step >= 4:
                operation.step_4_completed = False  # Still in progress
            
            db.session.add(operation)
            operations.append(operation)
    
    db.session.commit()
    return operations

def main():
    """Create all sample data"""
    with app.app_context():
        print("Creating sample data for Operations Dashboard...")
        
        try:
            # Create tables if they don't exist
            db.create_all()
            
            print("Creating sample vessels...")
            vessels = create_sample_vessels()
            print(f"Created {len(vessels)} vessels")
            
            print("Creating sample users...")
            users = create_sample_users()
            print(f"Created {len(users)} users")
            
            print("Creating sample teams...")
            teams = create_sample_teams()
            print(f"Created {len(teams)} teams")
            
            print("Creating sample operations...")
            operations = create_sample_operations()
            print(f"Created {len(operations)} operations")
            
            print("\nSample data creation completed successfully!")
            print("\nSummary:")
            print(f"- Vessels: {Vessel.query.count()}")
            print(f"- Users: {User.query.count()}")
            print(f"- Teams: {StevedoreTeam.query.count()}")
            print(f"- Operations: {ShipOperation.query.count()}")
            
            print("\nYou can now access the Operations Dashboard with sample data.")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()