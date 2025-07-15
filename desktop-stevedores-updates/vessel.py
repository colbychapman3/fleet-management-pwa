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
            'completed_tasks_count': self.get_completed_tasks_count()
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