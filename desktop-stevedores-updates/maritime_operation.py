from app import db
from datetime import datetime

class MaritimeOperation(db.Model):
    __tablename__ = 'maritime_operations'

    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False)
    operation_type = db.Column(db.String(100), nullable=False) # e.g., 'loading', 'discharging'
    status = db.Column(db.String(50), default='pending') # e.g., 'pending', 'in_progress', 'completed'
    
    # Step 2: Cargo Information
    cargo_type = db.Column(db.String(100))
    cargo_weight = db.Column(db.Float)
    cargo_description = db.Column(db.Text)
    cargo_origin = db.Column(db.String(100))
    cargo_destination = db.Column(db.String(100))
    
    # Step 3: Stowage Plan
    stowage_location = db.Column(db.String(100))
    stowage_notes = db.Column(db.Text)
    safety_requirements = db.Column(db.Text)
    loading_sequence = db.Column(db.Integer)
    
    # Step 4: Confirmation Details
    estimated_completion = db.Column(db.DateTime)
    special_instructions = db.Column(db.Text)
    priority_level = db.Column(db.String(20), default='normal') # low, normal, high, urgent
    assigned_crew = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to vessel
    vessel = db.relationship('Vessel', backref='maritime_operations')

    def __repr__(self):
        return f'<MaritimeOperation {self.id}: {self.operation_type} for Vessel {self.vessel_id}>'
    
    def to_dict(self):
        """Convert operation to dictionary for API responses"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'operation_type': self.operation_type,
            'status': self.status,
            'cargo_type': self.cargo_type,
            'cargo_weight': self.cargo_weight,
            'cargo_description': self.cargo_description,
            'cargo_origin': self.cargo_origin,
            'cargo_destination': self.cargo_destination,
            'stowage_location': self.stowage_location,
            'stowage_notes': self.stowage_notes,
            'safety_requirements': self.safety_requirements,
            'loading_sequence': self.loading_sequence,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'special_instructions': self.special_instructions,
            'priority_level': self.priority_level,
            'assigned_crew': self.assigned_crew,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
