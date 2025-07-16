"""
Enhanced TICO vehicle model for stevedoring operations
Handles vehicle management, zone assignments, and location tracking
"""

from datetime import datetime, timedelta
from sqlalchemy import and_, func
from app import db
import json
import math


class TicoVehicle(db.Model):
    """Enhanced TICO transportation vehicles for driver transport in stevedoring operations"""
    
    __tablename__ = 'tico_vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False, index=True)
    vehicle_type = db.Column(db.String(20), nullable=False, index=True)  # van, station_wagon
    license_plate = db.Column(db.String(20), unique=True, nullable=False, index=True)
    capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='available', nullable=False, index=True)  # available, assigned, in_transit, maintenance
    current_location = db.Column(db.String(100))  # Current GPS or zone location
    zone_assignment = db.Column(db.String(10), index=True)  # BRV, ZEE, SOU, etc.
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    current_load = db.Column(db.Integer, default=0, nullable=False)
    last_maintenance = db.Column(db.DateTime)
    next_maintenance = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vessel = db.relationship('Vessel', backref='tico_vehicles')
    driver = db.relationship('User', backref='assigned_tico_vehicles')
    
    def __repr__(self):
        return f'<TicoVehicle {self.license_plate} ({self.vehicle_type}) in {self.zone_assignment}>'
    
    def get_available_capacity(self):
        """Get remaining passenger capacity"""
        return max(0, self.capacity - self.current_load)
    
    def get_capacity_percentage(self):
        """Get current load as percentage of capacity"""
        if not self.capacity or self.capacity == 0:
            return 0
        return min(100, (self.current_load / self.capacity) * 100)
    
    def is_available(self):
        """Check if vehicle is available for assignment"""
        return (self.status == 'available' and 
                self.get_available_capacity() > 0 and 
                not self.needs_maintenance())
    
    def can_accommodate(self, passenger_count):
        """Check if vehicle can accommodate specified number of passengers"""
        return self.is_available() and self.get_available_capacity() >= passenger_count
    
    def needs_maintenance(self):
        """Check if vehicle needs maintenance"""
        if not self.next_maintenance:
            return False
        return datetime.utcnow() >= self.next_maintenance
    
    def assign_to_zone(self, zone, driver_id=None):
        """Assign vehicle to a specific zone"""
        if not self.is_available():
            return False, "Vehicle is not available for assignment"
        
        self.zone_assignment = zone
        self.status = 'assigned'
        if driver_id:
            self.driver_id = driver_id
        self.updated_at = datetime.utcnow()
        
        # Create assignment record
        assignment = TicoVehicleAssignment(
            vehicle_id=self.id,
            zone=zone,
            driver_id=driver_id,
            assigned_at=datetime.utcnow()
        )
        db.session.add(assignment)
        
        return True, "Vehicle assigned successfully"
    
    def update_location(self, location, coordinates=None):
        """Update vehicle's current location"""
        self.current_location = location
        self.updated_at = datetime.utcnow()
        
        # Create location history record
        location_history = TicoVehicleLocation(
            vehicle_id=self.id,
            location=location,
            coordinates=coordinates,
            timestamp=datetime.utcnow()
        )
        db.session.add(location_history)
        
        return True
    
    def get_utilization(self, hours=24):
        """Calculate vehicle utilization over specified hours"""
        from_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get assignments in the time period
        assignments = TicoVehicleAssignment.query.filter(
            TicoVehicleAssignment.vehicle_id == self.id,
            TicoVehicleAssignment.assigned_at >= from_time
        ).all()
        
        if not assignments:
            return 0.0
        
        # Calculate total assigned time
        total_assigned_minutes = 0
        for assignment in assignments:
            start_time = assignment.assigned_at
            end_time = assignment.completed_at or datetime.utcnow()
            
            # Only count time within our window
            if start_time < from_time:
                start_time = from_time
            
            duration = end_time - start_time
            total_assigned_minutes += duration.total_seconds() / 60
        
        total_minutes = hours * 60
        return min(100.0, (total_assigned_minutes / total_minutes) * 100)
    
    def get_distance_to_zone(self, target_zone):
        """Calculate estimated distance to target zone (simplified)"""
        zone_coordinates = {
            'BRV': (0, 0),
            'ZEE': (2, 3),
            'SOU': (-1, 4)
        }
        
        if not self.zone_assignment or target_zone not in zone_coordinates:
            return float('inf')
        
        if self.zone_assignment not in zone_coordinates:
            return float('inf')
        
        current_coords = zone_coordinates[self.zone_assignment]
        target_coords = zone_coordinates[target_zone]
        
        # Simple Euclidean distance
        distance = math.sqrt(
            (target_coords[0] - current_coords[0]) ** 2 +
            (target_coords[1] - current_coords[1]) ** 2
        )
        
        return distance
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'vehicle_type': self.vehicle_type,
            'license_plate': self.license_plate,
            'capacity': self.capacity,
            'current_load': self.current_load,
            'available_capacity': self.get_available_capacity(),
            'capacity_percentage': self.get_capacity_percentage(),
            'status': self.status,
            'current_location': self.current_location,
            'zone_assignment': self.zone_assignment,
            'driver_id': self.driver_id,
            'driver_name': self.driver.get_full_name() if self.driver else None,
            'is_available': self.is_available(),
            'needs_maintenance': self.needs_maintenance(),
            'utilization_24h': self.get_utilization(24),
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'next_maintenance': self.next_maintenance.isoformat() if self.next_maintenance else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_available_vehicles(vessel_id=None, zone=None, min_capacity=1):
        """Get available vehicles with optional filters"""
        query = TicoVehicle.query.filter_by(status='available')
        
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        
        if zone:
            query = query.filter_by(zone_assignment=zone)
        
        if min_capacity > 0:
            query = query.filter(TicoVehicle.capacity - TicoVehicle.current_load >= min_capacity)
        
        return query.order_by(TicoVehicle.capacity.desc()).all()
    
    @staticmethod
    def get_zone_vehicles(zone, vessel_id=None):
        """Get all vehicles assigned to a specific zone"""
        query = TicoVehicle.query.filter_by(zone_assignment=zone)
        
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        
        return query.all()
    
    @staticmethod
    def get_utilization_summary(vessel_id=None, hours=24):
        """Get utilization summary for all vehicles"""
        query = TicoVehicle.query
        
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        
        vehicles = query.all()
        
        total_vehicles = len(vehicles)
        if total_vehicles == 0:
            return {
                'total_vehicles': 0,
                'average_utilization': 0,
                'high_utilization_count': 0,
                'low_utilization_count': 0
            }
        
        utilizations = [v.get_utilization(hours) for v in vehicles]
        average_utilization = sum(utilizations) / total_vehicles
        
        high_util_count = sum(1 for u in utilizations if u >= 80)
        low_util_count = sum(1 for u in utilizations if u < 20)
        
        return {
            'total_vehicles': total_vehicles,
            'average_utilization': round(average_utilization, 2),
            'high_utilization_count': high_util_count,
            'low_utilization_count': low_util_count,
            'utilizations': utilizations
        }


class TicoVehicleAssignment(db.Model):
    """Track vehicle assignments to zones and operations"""
    
    __tablename__ = 'tico_vehicle_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('tico_vehicles.id'), nullable=False, index=True)
    zone = db.Column(db.String(10), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    passenger_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    # Relationships
    vehicle = db.relationship('TicoVehicle', backref='assignments')
    driver = db.relationship('User', backref='vehicle_assignments')
    
    def __repr__(self):
        return f'<TicoVehicleAssignment Vehicle {self.vehicle_id} to {self.zone}>'
    
    def get_duration(self):
        """Get assignment duration in minutes"""
        if not self.completed_at:
            return (datetime.utcnow() - self.assigned_at).total_seconds() / 60
        return (self.completed_at - self.assigned_at).total_seconds() / 60
    
    def complete_assignment(self):
        """Mark assignment as completed"""
        self.completed_at = datetime.utcnow()
        if self.vehicle:
            self.vehicle.status = 'available'
            self.vehicle.current_load = 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'vehicle_license': self.vehicle.license_plate if self.vehicle else None,
            'zone': self.zone,
            'driver_id': self.driver_id,
            'driver_name': self.driver.get_full_name() if self.driver else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_minutes': self.get_duration(),
            'passenger_count': self.passenger_count,
            'notes': self.notes
        }


class TicoVehicleLocation(db.Model):
    """Track vehicle location history"""
    
    __tablename__ = 'tico_vehicle_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('tico_vehicles.id'), nullable=False, index=True)
    location = db.Column(db.String(100), nullable=False)
    coordinates = db.Column(db.String(50))  # lat,lng format
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    vehicle = db.relationship('TicoVehicle', backref='location_history')
    
    def __repr__(self):
        return f'<TicoVehicleLocation Vehicle {self.vehicle_id} at {self.location}>'
    
    def get_coordinates(self):
        """Get coordinates as tuple (lat, lng)"""
        if not self.coordinates:
            return None
        try:
            parts = self.coordinates.split(',')
            return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            return None
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'location': self.location,
            'coordinates': self.coordinates,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class TicoRouteOptimizer:
    """Helper class for TICO vehicle route optimization"""
    
    @staticmethod
    def calculate_optimal_assignments(vessel_id, zone_demands):
        """
        Calculate optimal vehicle assignments based on zone demands
        
        Args:
            vessel_id: ID of the vessel
            zone_demands: Dict of {zone: required_capacity}
        
        Returns:
            Dict with assignment recommendations
        """
        available_vehicles = TicoVehicle.get_available_vehicles(vessel_id=vessel_id)
        
        if not available_vehicles:
            return {
                'assignments': [],
                'unmet_demand': zone_demands.copy(),
                'total_capacity': 0,
                'efficiency': 0
            }
        
        assignments = []
        unmet_demand = zone_demands.copy()
        total_capacity = sum(v.capacity for v in available_vehicles)
        
        # Sort zones by demand (highest first)
        sorted_zones = sorted(zone_demands.items(), key=lambda x: x[1], reverse=True)
        
        for zone, demand in sorted_zones:
            if demand <= 0:
                continue
            
            # Find best vehicle for this zone
            best_vehicle = None
            best_score = -1
            
            for vehicle in available_vehicles:
                if vehicle.get_available_capacity() <= 0:
                    continue
                
                # Calculate score based on capacity match and distance
                capacity_match = min(vehicle.get_available_capacity(), demand)
                distance_penalty = vehicle.get_distance_to_zone(zone)
                score = capacity_match - (distance_penalty * 5)  # Penalize distance
                
                if score > best_score:
                    best_score = score
                    best_vehicle = vehicle
            
            if best_vehicle:
                capacity_to_assign = min(best_vehicle.get_available_capacity(), demand)
                
                assignments.append({
                    'vehicle_id': best_vehicle.id,
                    'license_plate': best_vehicle.license_plate,
                    'zone': zone,
                    'capacity_assigned': capacity_to_assign,
                    'distance': best_vehicle.get_distance_to_zone(zone),
                    'estimated_travel_time': best_vehicle.get_distance_to_zone(zone) * 10  # 10 min per unit
                })
                
                # Update vehicle availability
                best_vehicle.current_load += capacity_to_assign
                unmet_demand[zone] -= capacity_to_assign
                
                if unmet_demand[zone] <= 0:
                    del unmet_demand[zone]
        
        # Calculate efficiency
        total_demand = sum(zone_demands.values())
        met_demand = total_demand - sum(unmet_demand.values())
        efficiency = (met_demand / total_demand * 100) if total_demand > 0 else 0
        
        return {
            'assignments': assignments,
            'unmet_demand': unmet_demand,
            'total_capacity': total_capacity,
            'efficiency': round(efficiency, 2),
            'total_vehicles_used': len(assignments)
        }
    
    @staticmethod
    def minimize_travel_time(assignments):
        """
        Optimize assignments to minimize total travel time
        
        Args:
            assignments: List of vehicle assignments
        
        Returns:
            Optimized assignment order
        """
        # Simple greedy approach - sort by travel time
        return sorted(assignments, key=lambda x: x.get('estimated_travel_time', 0))
    
    @staticmethod
    def balance_vehicle_workload(vessel_id):
        """
        Balance workload across all vehicles
        
        Args:
            vessel_id: ID of the vessel
        
        Returns:
            Workload balance recommendations
        """
        vehicles = TicoVehicle.query.filter_by(vessel_id=vessel_id).all()
        
        if not vehicles:
            return {'recommendations': [], 'balance_score': 0}
        
        # Calculate utilization for each vehicle
        utilizations = [(v, v.get_utilization(24)) for v in vehicles]
        utilizations.sort(key=lambda x: x[1])  # Sort by utilization
        
        recommendations = []
        balance_score = 0
        
        if len(utilizations) > 1:
            # Calculate standard deviation of utilizations
            utils = [u[1] for u in utilizations]
            mean_util = sum(utils) / len(utils)
            variance = sum((u - mean_util) ** 2 for u in utils) / len(utils)
            std_dev = math.sqrt(variance)
            
            balance_score = max(0, 100 - std_dev)  # Better balance = higher score
            
            # Identify over/under utilized vehicles
            overutilized = [u for u in utilizations if u[1] > mean_util + std_dev]
            underutilized = [u for u in utilizations if u[1] < mean_util - std_dev]
            
            for vehicle, util in overutilized:
                recommendations.append({
                    'vehicle_id': vehicle.id,
                    'license_plate': vehicle.license_plate,
                    'current_utilization': util,
                    'recommendation': 'Reduce workload - consider maintenance or redistribution',
                    'priority': 'high' if util > 90 else 'medium'
                })
            
            for vehicle, util in underutilized:
                recommendations.append({
                    'vehicle_id': vehicle.id,
                    'license_plate': vehicle.license_plate,
                    'current_utilization': util,
                    'recommendation': 'Increase utilization - available for additional assignments',
                    'priority': 'low'
                })
        
        return {
            'recommendations': recommendations,
            'balance_score': round(balance_score, 2),
            'mean_utilization': round(sum(u[1] for u in utilizations) / len(utilizations), 2)
        }
    
    @staticmethod
    def get_automated_dispatch_recommendations(vessel_id, current_demands):
        """
        Generate automated dispatch recommendations
        
        Args:
            vessel_id: ID of the vessel
            current_demands: Current zone demands
        
        Returns:
            Automated dispatch recommendations
        """
        # Get optimal assignments
        optimal = TicoRouteOptimizer.calculate_optimal_assignments(vessel_id, current_demands)
        
        # Get workload balance
        balance = TicoRouteOptimizer.balance_vehicle_workload(vessel_id)
        
        # Generate recommendations
        recommendations = []
        
        for assignment in optimal['assignments']:
            recommendations.append({
                'type': 'dispatch',
                'vehicle_id': assignment['vehicle_id'],
                'license_plate': assignment['license_plate'],
                'action': f"Dispatch to {assignment['zone']}",
                'priority': 'high',
                'estimated_time': assignment['estimated_travel_time'],
                'capacity_utilization': assignment['capacity_assigned']
            })
        
        # Add balance recommendations
        for rec in balance['recommendations']:
            if rec['priority'] == 'high':
                recommendations.append({
                    'type': 'maintenance',
                    'vehicle_id': rec['vehicle_id'],
                    'license_plate': rec['license_plate'],
                    'action': rec['recommendation'],
                    'priority': rec['priority'],
                    'utilization': rec['current_utilization']
                })
        
        return {
            'recommendations': recommendations,
            'optimization_efficiency': optimal['efficiency'],
            'balance_score': balance['balance_score'],
            'timestamp': datetime.utcnow().isoformat()
        }