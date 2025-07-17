"""
Maritime-specific models for stevedoring operations
"""

from datetime import datetime
from app import db
import json

class CargoOperation(db.Model):
    """Cargo operations tracking for maritime stevedoring"""
    
    __tablename__ = 'cargo_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False, index=True)
    zone = db.Column(db.String(10), index=True)  # BRV, ZEE, SOU
    vehicle_type = db.Column(db.String(50))  # Sedan, SUV, Truck, etc.
    quantity = db.Column(db.Integer)
    discharged = db.Column(db.Integer, default=0, nullable=False)
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CargoOperation {self.vehicle_type} in {self.zone}>'
    
    def get_progress_percentage(self):
        """Calculate discharge progress percentage"""
        if not self.quantity or self.quantity == 0:
            return 0
        return min(100, (self.discharged / self.quantity) * 100)
    
    def is_complete(self):
        """Check if cargo operation is complete"""
        return self.discharged >= self.quantity if self.quantity else False
    
    def remaining_quantity(self):
        """Get remaining quantity to discharge"""
        return max(0, (self.quantity or 0) - self.discharged)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'zone': self.zone,
            'vehicle_type': self.vehicle_type,
            'quantity': self.quantity,
            'discharged': self.discharged,
            'remaining': self.remaining_quantity(),
            'progress_percentage': self.get_progress_percentage(),
            'location': self.location,
            'is_complete': self.is_complete(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }





class MaritimeDocument(db.Model):
    """Maritime document uploads and processing"""
    
    __tablename__ = 'maritime_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True, index=True)
    document_type = db.Column(db.String(50), index=True)  # Cargo Manifest, Work Order, etc.
    file_path = db.Column(db.String(255))
    processed_data = db.Column(db.Text)  # JSON of extracted data
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    vessel = db.relationship('Vessel', backref='maritime_documents')
    uploader = db.relationship('User', backref='uploaded_documents')
    
    def __repr__(self):
        return f'<MaritimeDocument {self.document_type} for Vessel {self.vessel_id}>'
    
    def get_processed_data(self):
        """Get processed data as dictionary"""
        if not self.processed_data:
            return {}
        try:
            return json.loads(self.processed_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_processed_data(self, data_dict):
        """Set processed data from dictionary"""
        self.processed_data = json.dumps(data_dict) if data_dict else None
    
    def get_file_size(self):
        """Get file size if file exists"""
        import os
        if self.file_path and os.path.exists(self.file_path):
            return os.path.getsize(self.file_path)
        return 0
    
    def get_file_extension(self):
        """Get file extension"""
        if not self.file_path:
            return None
        return self.file_path.split('.')[-1].lower() if '.' in self.file_path else None
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'vessel_name': self.vessel.name if self.vessel else None,
            'document_type': self.document_type,
            'file_path': self.file_path,
            'file_size': self.get_file_size(),
            'file_extension': self.get_file_extension(),
            'processed_data': self.get_processed_data(),
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.get_full_name() if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DischargeProgress(db.Model):
    """Real-time discharge progress tracking"""
    
    __tablename__ = 'discharge_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False, index=True)
    zone = db.Column(db.String(10), index=True)  # BRV, ZEE, SOU
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    vehicles_discharged = db.Column(db.Integer)
    hourly_rate = db.Column(db.Numeric(5, 2))
    total_progress = db.Column(db.Numeric(5, 2))  # Percentage
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    vessel = db.relationship('Vessel', backref='discharge_progress')
    creator = db.relationship('User', backref='progress_updates')
    
    def __repr__(self):
        return f'<DischargeProgress {self.zone} for Vessel {self.vessel_id} at {self.timestamp}>'
    
    def get_progress_percentage(self):
        """Get progress as percentage"""
        return float(self.total_progress) if self.total_progress else 0
    
    def get_hourly_rate_float(self):
        """Get hourly rate as float"""
        return float(self.hourly_rate) if self.hourly_rate else 0
    
    def is_recent(self, minutes=60):
        """Check if progress update is recent"""
        if not self.timestamp:
            return False
        delta = datetime.utcnow() - self.timestamp
        return delta.total_seconds() < (minutes * 60)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'zone': self.zone,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'vehicles_discharged': self.vehicles_discharged,
            'hourly_rate': self.get_hourly_rate_float(),
            'total_progress': self.get_progress_percentage(),
            'created_by': self.created_by,
            'creator_name': self.creator.get_full_name() if self.creator else None,
            'is_recent': self.is_recent()
        }
    
    @staticmethod
    def get_latest_progress_by_vessel(vessel_id):
        """Get latest progress update for a vessel"""
        return DischargeProgress.query.filter_by(vessel_id=vessel_id)\
                                    .order_by(DischargeProgress.timestamp.desc())\
                                    .first()
    
    @staticmethod
    def get_progress_by_zone(vessel_id, zone):
        """Get progress updates for specific vessel and zone"""
        return DischargeProgress.query.filter_by(vessel_id=vessel_id, zone=zone)\
                                    .order_by(DischargeProgress.timestamp.asc())\
                                    .all()
    
    @staticmethod
    def calculate_average_hourly_rate(vessel_id, hours=24):
        """Calculate average hourly rate over specified hours"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        progress_updates = DischargeProgress.query.filter(
            DischargeProgress.vessel_id == vessel_id,
            DischargeProgress.timestamp >= cutoff_time,
            DischargeProgress.hourly_rate.isnot(None)
        ).all()
        
        if not progress_updates:
            return 0
        
        total_rate = sum(float(p.hourly_rate) for p in progress_updates)
        return total_rate / len(progress_updates)


# Helper functions for maritime operations
class MaritimeOperationsHelper:
    """Helper class for maritime operations calculations and utilities"""
    
    ZONE_CAPACITY = {
        'BRV': 1000,  # Default capacity per zone
        'ZEE': 800,
        'SOU': 1200
    }
    
    VEHICLE_TYPES = [
        'Sedan', 'Hatchback', 'SUV', 'Pickup Truck', 'Van', 'Bus',
        'Heavy Truck', 'Trailer', 'Construction Vehicle', 'Electric Vehicle'
    ]
    
    TICO_VEHICLE_CAPACITY = {
        'Van': 7,
        'Station Wagon': 5
    }
    
    @staticmethod
    def calculate_estimated_completion(vessel_id):
        """Calculate estimated completion time for vessel operations"""
        from models.models.vessel import Vessel
        
        vessel = Vessel.query.get(vessel_id)
        if not vessel:
            return None
        
        total_vehicles = vessel.total_vehicles or 0
        expected_rate = vessel.expected_rate or 150
        
        if expected_rate <= 0:
            return None
        
        # Calculate latest progress
        latest_progress = DischargeProgress.get_latest_progress_by_vessel(vessel_id)
        vehicles_remaining = total_vehicles
        
        if latest_progress:
            vehicles_discharged = latest_progress.vehicles_discharged or 0
            vehicles_remaining = max(0, total_vehicles - vehicles_discharged)
        
        if vehicles_remaining <= 0:
            return datetime.utcnow()  # Already complete
        
        # Calculate hours remaining
        hours_remaining = vehicles_remaining / expected_rate
        
        return datetime.utcnow() + timedelta(hours=hours_remaining)
    
    @staticmethod
    def get_zone_summary(vessel_id):
        """Get summary of all zones for a vessel"""
        cargo_ops = CargoOperation.query.filter_by(vessel_id=vessel_id).all()
        
        zone_summary = {}
        for op in cargo_ops:
            zone = op.zone or 'General'
            if zone not in zone_summary:
                zone_summary[zone] = {
                    'total_quantity': 0,
                    'discharged': 0,
                    'remaining': 0,
                    'progress_percentage': 0,
                    'vehicle_types': []
                }
            
            zone_summary[zone]['total_quantity'] += op.quantity or 0
            zone_summary[zone]['discharged'] += op.discharged
            zone_summary[zone]['remaining'] = zone_summary[zone]['total_quantity'] - zone_summary[zone]['discharged']
            
            if zone_summary[zone]['total_quantity'] > 0:
                zone_summary[zone]['progress_percentage'] = (
                    zone_summary[zone]['discharged'] / zone_summary[zone]['total_quantity']
                ) * 100
            
            if op.vehicle_type and op.vehicle_type not in zone_summary[zone]['vehicle_types']:
                zone_summary[zone]['vehicle_types'].append(op.vehicle_type)
        
        return zone_summary
    
    @staticmethod
    def optimize_tico_assignments(vessel_id, drivers_needed):
        """Optimize TICO vehicle assignments for driver transport"""
        vehicles = TicoVehicle.query.filter_by(
            vessel_id=vessel_id, 
            status='available'
        ).order_by(TicoVehicle.capacity.desc()).all()
        
        assignments = []
        remaining_drivers = drivers_needed
        
        for vehicle in vehicles:
            if remaining_drivers <= 0:
                break
            
            can_transport = min(vehicle.get_available_capacity(), remaining_drivers)
            if can_transport > 0:
                assignments.append({
                    'vehicle_id': vehicle.id,
                    'vehicle_type': vehicle.vehicle_type,
                    'drivers_assigned': can_transport,
                    'capacity_used': vehicle.get_capacity_percentage() + (can_transport / vehicle.capacity * 100)
                })
                remaining_drivers -= can_transport
        
        return {
            'assignments': assignments,
            'drivers_accommodated': drivers_needed - remaining_drivers,
            'drivers_remaining': remaining_drivers,
            'vehicles_needed': len(assignments)
        }