#!/usr/bin/env python3
"""
Create sample TICO vehicle data for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models.models.tico_vehicle import TicoVehicle, TicoVehicleAssignment, TicoVehicleLocation
from models.models.vessel import Vessel
from models.models.user import User
from datetime import datetime, timedelta
import random

def create_tico_vehicles():
    """Create sample TICO vehicles for testing"""
    
    app = create_app()
    
    with app.app_context():
        print("Creating TICO vehicle sample data...")
        
        # Get existing vessels
        vessels = Vessel.query.all()
        if not vessels:
            print("No vessels found. Please create vessels first.")
            return
        
        # Get existing users (drivers)
        drivers = User.query.filter_by(role='worker').all()
        if not drivers:
            print("No worker users found. Please create worker users first.")
            return
        
        # Sample vehicle data
        sample_vehicles = [
            {
                'vehicle_type': 'van',
                'license_plate': 'TICO-V001',
                'capacity': 7,
                'zone_assignment': 'BRV',
                'current_location': 'BRV Zone Gate'
            },
            {
                'vehicle_type': 'van',
                'license_plate': 'TICO-V002',
                'capacity': 7,
                'zone_assignment': 'ZEE',
                'current_location': 'ZEE Zone Parking'
            },
            {
                'vehicle_type': 'station_wagon',
                'license_plate': 'TICO-SW001',
                'capacity': 5,
                'zone_assignment': 'SOU',
                'current_location': 'SOU Zone Office'
            },
            {
                'vehicle_type': 'van',
                'license_plate': 'TICO-V003',
                'capacity': 7,
                'zone_assignment': 'BRV',
                'current_location': 'BRV Zone Terminal'
            },
            {
                'vehicle_type': 'station_wagon',
                'license_plate': 'TICO-SW002',
                'capacity': 5,
                'zone_assignment': None,
                'current_location': 'Main Depot'
            },
            {
                'vehicle_type': 'van',
                'license_plate': 'TICO-V004',
                'capacity': 7,
                'zone_assignment': 'ZEE',
                'current_location': 'ZEE Zone Berth 2'
            },
            {
                'vehicle_type': 'station_wagon',
                'license_plate': 'TICO-SW003',
                'capacity': 5,
                'zone_assignment': 'SOU',
                'current_location': 'SOU Zone Checkpoint'
            },
            {
                'vehicle_type': 'van',
                'license_plate': 'TICO-V005',
                'capacity': 7,
                'zone_assignment': None,
                'current_location': 'Maintenance Bay'
            }
        ]
        
        created_vehicles = []
        
        # Create vehicles
        for vehicle_data in sample_vehicles:
            # Assign to random vessel
            vessel = random.choice(vessels)
            
            # Assign random driver (optional)
            driver = random.choice(drivers + [None, None])  # 33% chance of no driver
            
            # Create vehicle
            vehicle = TicoVehicle(
                vessel_id=vessel.id,
                vehicle_type=vehicle_data['vehicle_type'],
                license_plate=vehicle_data['license_plate'],
                capacity=vehicle_data['capacity'],
                zone_assignment=vehicle_data['zone_assignment'],
                driver_id=driver.id if driver else None,
                current_location=vehicle_data['current_location'],
                status='available',
                current_load=random.randint(0, vehicle_data['capacity'] // 2),
                next_maintenance=datetime.utcnow() + timedelta(days=random.randint(30, 90))
            )
            
            db.session.add(vehicle)
            created_vehicles.append(vehicle)
            
            print(f"Created vehicle: {vehicle.license_plate} ({vehicle.vehicle_type})")
        
        # Commit vehicles first
        db.session.commit()
        
        # Create some sample assignments
        print("\nCreating sample vehicle assignments...")
        
        for i, vehicle in enumerate(created_vehicles[:4]):  # Only first 4 vehicles
            if vehicle.zone_assignment:
                assignment = TicoVehicleAssignment(
                    vehicle_id=vehicle.id,
                    zone=vehicle.zone_assignment,
                    driver_id=vehicle.driver_id,
                    assigned_at=datetime.utcnow() - timedelta(hours=random.randint(1, 8)),
                    passenger_count=random.randint(1, vehicle.capacity),
                    notes=f"Sample assignment for testing zone {vehicle.zone_assignment}"
                )
                
                # Complete some assignments
                if i < 2:
                    assignment.completed_at = datetime.utcnow() - timedelta(minutes=random.randint(30, 180))
                
                db.session.add(assignment)
                print(f"Created assignment: {vehicle.license_plate} to {vehicle.zone_assignment}")
        
        # Create sample location history
        print("\nCreating sample location history...")
        
        sample_locations = [
            'Main Gate',
            'Parking Area A',
            'Parking Area B',
            'BRV Zone Gate',
            'BRV Zone Terminal',
            'ZEE Zone Parking',
            'ZEE Zone Berth 1',
            'ZEE Zone Berth 2',
            'SOU Zone Office',
            'SOU Zone Checkpoint',
            'Maintenance Bay',
            'Fuel Station',
            'Administration Building'
        ]
        
        for vehicle in created_vehicles:
            # Create 3-5 location entries per vehicle
            for j in range(random.randint(3, 5)):
                location = TicoVehicleLocation(
                    vehicle_id=vehicle.id,
                    location=random.choice(sample_locations),
                    coordinates=f"{random.uniform(-6.2, -6.1):.6f},{random.uniform(106.8, 106.9):.6f}",
                    timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                )
                
                db.session.add(location)
        
        # Commit all changes
        db.session.commit()
        
        print(f"\nSample data created successfully!")
        print(f"- Created {len(created_vehicles)} TICO vehicles")
        print(f"- Created sample assignments and location history")
        print(f"- Vehicle types: {len([v for v in created_vehicles if v.vehicle_type == 'van'])} vans, {len([v for v in created_vehicles if v.vehicle_type == 'station_wagon'])} station wagons")
        
        # Display summary
        print("\nVehicle Summary:")
        for zone in ['BRV', 'ZEE', 'SOU', None]:
            zone_vehicles = [v for v in created_vehicles if v.zone_assignment == zone]
            zone_name = zone if zone else 'Unassigned'
            print(f"  {zone_name}: {len(zone_vehicles)} vehicles")

if __name__ == '__main__':
    create_tico_vehicles()