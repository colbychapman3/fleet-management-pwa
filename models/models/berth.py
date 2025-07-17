"""
Berth model for port berth management
"""
from datetime import datetime
from app import db

class Berth(db.Model):
    """Berth model for port infrastructure"""
    
    __tablename__ = 'berths'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic berth information
    berth_number = db.Column(db.String(20), nullable=False, unique=True, index=True)
    berth_name = db.Column(db.String(100), nullable=True)
    berth_type = db.Column(db.String(50), nullable=True)  # Container, RoRo, General Cargo
    
    # Physical specifications
    length_meters = db.Column(db.Float, nullable=True)
    depth_meters = db.Column(db.Float, nullable=True)
    max_draft = db.Column(db.Float, nullable=True)
    max_loa = db.Column(db.Float, nullable=True)  # Length Overall
    
    # Infrastructure
    bollards_count = db.Column(db.Integer, nullable=True)
    crane_capacity = db.Column(db.Integer, nullable=True)  # In tons
    electrical_capacity = db.Column(db.Integer, nullable=True)  # In kW
    water_supply = db.Column(db.Boolean, default=False, nullable=False)
    fuel_supply = db.Column(db.Boolean, default=False, nullable=False)
    
    # Status and rates
    status = db.Column(db.String(20), default='active', nullable=False)  # active, maintenance, closed
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)
    daily_rate = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Additional data
    facilities = db.Column(db.Text, nullable=True)  # JSON of available facilities
    restrictions = db.Column(db.Text, nullable=True)  # JSON of restrictions/limitations
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    vessels = db.relationship('Vessel', foreign_keys='Vessel.current_berth_id', back_populates='berth', lazy='dynamic')
    
    def __repr__(self):
        return f'<Berth {self.berth_number}: {self.berth_name}>'
    
    def to_dict(self):
        """Convert berth to dictionary"""
        return {
            'id': self.id,
            'berth_number': self.berth_number,
            'berth_name': self.berth_name,
            'berth_type': self.berth_type,
            'length_meters': self.length_meters,
            'depth_meters': self.depth_meters,
            'max_draft': self.max_draft,
            'max_loa': self.max_loa,
            'bollards_count': self.bollards_count,
            'crane_capacity': self.crane_capacity,
            'electrical_capacity': self.electrical_capacity,
            'water_supply': self.water_supply,
            'fuel_supply': self.fuel_supply,
            'status': self.status,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'daily_rate': float(self.daily_rate) if self.daily_rate else None,
            'facilities': self.facilities,
            'restrictions': self.restrictions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }