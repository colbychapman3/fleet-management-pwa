"""
Vessel model for fleet management
"""

from datetime import datetime
from app import db

class Vessel(db.Model):
    """Vessel model for managing fleet information"""
    
    __tablename__ = 'vessels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    imo_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    vessel_type = db.Column(db.String(50), nullable=False)
    flag = db.Column(db.String(50))
    owner = db.Column(db.String(100))
    operator = db.Column(db.String(100))
    
    # Technical specifications
    length = db.Column(db.Float)  # meters
    beam = db.Column(db.Float)   # meters
    draft = db.Column(db.Float)  # meters
    gross_tonnage = db.Column(db.Integer)
    net_tonnage = db.Column(db.Integer)
    
    # Operational status
    status = db.Column(db.String(20), default='active')  # active, maintenance, decommissioned
    current_port = db.Column(db.String(100))
    destination_port = db.Column(db.String(100))
    eta = db.Column(db.DateTime)
    
    # Maritime-specific fields
    berth_assignment = db.Column(db.String(20), index=True)  # Berth number/designation
    cargo_capacity = db.Column(db.JSON)  # {'automobiles': 2000, 'containers': 500, 'bulk': 50000}
    zone_assignment = db.Column(db.String(10))  # BRV, ZEE, SOU
    operation_status = db.Column(db.String(20), default='at_anchor')  # at_anchor, at_berth, loading, discharging, departed
    cargo_type = db.Column(db.String(50))  # automobiles, containers, bulk, general_cargo
    agent_company = db.Column(db.String(100))
    pilot_required = db.Column(db.Boolean, default=True)
    pilot_embarked = db.Column(db.Boolean, default=False)
    customs_cleared = db.Column(db.Boolean, default=False)
    security_level = db.Column(db.Integer, default=1)  # ISPS security levels 1-3
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (backref in User model)
    tasks = db.relationship('Task', backref='vessel', lazy='dynamic')
    
    def __repr__(self):
        return f'<Vessel {self.name}>'
    
    def get_crew_count(self):
        """Get number of crew members assigned to vessel"""
        return len(self.crew_members)
    
    def get_active_tasks_count(self):
        """Get number of active tasks for vessel"""
        return self.tasks.filter_by(status='pending').count()
    
    def get_completed_tasks_count(self):
        """Get number of completed tasks for vessel"""
        return self.tasks.filter_by(status='completed').count()
    
    def is_at_berth(self):
        """Check if vessel is currently at berth"""
        return self.operation_status == 'at_berth' and self.berth_assignment is not None
    
    def can_accommodate_cargo_type(self, cargo_type):
        """Check if vessel can accommodate specific cargo type"""
        if not self.cargo_capacity or not isinstance(self.cargo_capacity, dict):
            return False
        return cargo_type in self.cargo_capacity
    
    def get_cargo_capacity_for_type(self, cargo_type):
        """Get cargo capacity for specific type"""
        if not self.cargo_capacity or not isinstance(self.cargo_capacity, dict):
            return 0
        return self.cargo_capacity.get(cargo_type, 0)
    
    def update_operation_status(self, new_status):
        """Update vessel operation status"""
        valid_statuses = ['at_anchor', 'at_berth', 'loading', 'discharging', 'departed']
        if new_status in valid_statuses:
            self.operation_status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def assign_to_berth(self, berth_number):
        """Assign vessel to a berth"""
        self.berth_assignment = berth_number
        self.operation_status = 'at_berth'
        self.updated_at = datetime.utcnow()
    
    def release_from_berth(self):
        """Release vessel from berth"""
        self.berth_assignment = None
        self.operation_status = 'at_anchor'
        self.updated_at = datetime.utcnow()
    
    def get_operation_status_display(self):
        """Get user-friendly operation status display"""
        status_map = {
            'at_anchor': 'At Anchor',
            'at_berth': 'At Berth',
            'loading': 'Loading Cargo',
            'discharging': 'Discharging Cargo',
            'departed': 'Departed'
        }
        return status_map.get(self.operation_status, self.operation_status.title())
    
    def to_dict(self):
        """Convert vessel to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'imo_number': self.imo_number,
            'vessel_type': self.vessel_type,
            'flag': self.flag,
            'owner': self.owner,
            'operator': self.operator,
            'length': self.length,
            'beam': self.beam,
            'draft': self.draft,
            'gross_tonnage': self.gross_tonnage,
            'net_tonnage': self.net_tonnage,
            'status': self.status,
            'current_port': self.current_port,
            'destination_port': self.destination_port,
            'eta': self.eta.isoformat() if self.eta else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'crew_count': self.get_crew_count(),
            'active_tasks_count': self.get_active_tasks_count(),
            'completed_tasks_count': self.get_completed_tasks_count(),
            'berth_assignment': self.berth_assignment,
            'cargo_capacity': self.cargo_capacity,
            'zone_assignment': self.zone_assignment,
            'operation_status': self.operation_status,
            'operation_status_display': self.get_operation_status_display(),
            'cargo_type': self.cargo_type,
            'agent_company': self.agent_company,
            'pilot_required': self.pilot_required,
            'pilot_embarked': self.pilot_embarked,
            'customs_cleared': self.customs_cleared,
            'security_level': self.security_level,
            'is_at_berth': self.is_at_berth()
        }
    
    @staticmethod
    def get_active_vessels():
        """Get all active vessels"""
        return Vessel.query.filter_by(status='active').all()
    
    @staticmethod
    def get_vessels_by_type(vessel_type):
        """Get vessels by type"""
        return Vessel.query.filter_by(vessel_type=vessel_type, status='active').all()
    
    @staticmethod
    def search_vessels(query):
        """Search vessels by name or IMO number"""
        search_term = f"%{query}%"
        return Vessel.query.filter(
            db.or_(
                Vessel.name.ilike(search_term),
                Vessel.imo_number.ilike(search_term)
            )
        ).all()
    
    @staticmethod
    def get_vessels_at_berth():
        """Get all vessels currently at berth"""
        return Vessel.query.filter_by(operation_status='at_berth').all()
    
    @staticmethod
    def get_vessels_by_zone(zone):
        """Get all vessels in a specific zone"""
        return Vessel.query.filter_by(zone_assignment=zone, status='active').all()
    
    @staticmethod
    def get_vessels_by_cargo_type(cargo_type):
        """Get vessels by cargo type"""
        return Vessel.query.filter_by(cargo_type=cargo_type, status='active').all()
    
    @staticmethod
    def get_vessels_by_operation_status(operation_status):
        """Get vessels by operation status"""
        return Vessel.query.filter_by(operation_status=operation_status, status='active').all()
    
    @staticmethod
    def get_available_berths():
        """Get list of vessels that are not occupying berths"""
        return Vessel.query.filter(
            Vessel.berth_assignment.is_(None),
            Vessel.status == 'active'
        ).all()
    
    @staticmethod
    def get_vessels_awaiting_pilot():
        """Get vessels that require but don't have a pilot"""
        return Vessel.query.filter(
            Vessel.pilot_required == True,
            Vessel.pilot_embarked == False,
            Vessel.status == 'active'
        ).all()
    
    @staticmethod
    def get_vessels_awaiting_customs():
        """Get vessels awaiting customs clearance"""
        return Vessel.query.filter(
            Vessel.customs_cleared == False,
            Vessel.status == 'active'
        ).all()