"""
CargoBatch model for tracking cargo batches on vessels
"""

from datetime import datetime
from app import db

class CargoBatch(db.Model):
    """Model for tracking cargo batches on vessels"""
    
    __tablename__ = 'cargo_batches'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False, index=True)
    
    # Batch identification
    batch_number = db.Column(db.String(50), nullable=False, index=True)
    batch_name = db.Column(db.String(100), nullable=True)
    
    # Cargo details
    cargo_type = db.Column(db.String(50), nullable=False)  # 'automobiles', 'containers', 'bulk', 'breakbulk'
    cargo_description = db.Column(db.Text, nullable=True)
    total_units = db.Column(db.Integer, nullable=False, default=0)
    processed_units = db.Column(db.Integer, nullable=False, default=0)
    
    # Zone assignment
    zone_assignment = db.Column(db.String(10), nullable=True)  # BRV, ZEE, SOU
    deck_level = db.Column(db.String(20), nullable=True)
    location_on_vessel = db.Column(db.String(100), nullable=True)
    
    # Status and priority
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, processing, completed, cancelled
    priority = db.Column(db.String(20), default='normal', nullable=False)  # low, normal, high, urgent
    
    # Timing
    scheduled_start = db.Column(db.DateTime, nullable=True)
    actual_start = db.Column(db.DateTime, nullable=True)
    scheduled_completion = db.Column(db.DateTime, nullable=True)
    actual_completion = db.Column(db.DateTime, nullable=True)
    
    # Weight and dimensions
    total_weight_kg = db.Column(db.Float, nullable=True)
    total_volume_m3 = db.Column(db.Float, nullable=True)
    dangerous_goods = db.Column(db.Boolean, default=False, nullable=False)
    hazmat_class = db.Column(db.String(20), nullable=True)
    
    # Documentation
    manifest_reference = db.Column(db.String(100), nullable=True)
    customs_reference = db.Column(db.String(100), nullable=True)
    special_handling_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (will be established by Vessel model)
    
    def __repr__(self):
        return f'<CargoBatch {self.batch_number}: {self.cargo_type}>'
    
    def get_progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_units == 0:
            return 0.0
        return round((self.processed_units / self.total_units) * 100, 2)
    
    def is_complete(self):
        """Check if batch is complete"""
        return self.processed_units >= self.total_units
    
    def get_remaining_units(self):
        """Get remaining units to process"""
        return max(0, self.total_units - self.processed_units)
    
    def update_progress(self, units_processed):
        """Update progress and auto-complete if needed"""
        self.processed_units = min(units_processed, self.total_units)
        
        if self.is_complete() and self.status == 'processing':
            self.status = 'completed'
            self.actual_completion = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
    
    def start_processing(self):
        """Mark batch as started"""
        if self.status == 'pending':
            self.status = 'processing'
            self.actual_start = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'batch_number': self.batch_number,
            'batch_name': self.batch_name,
            'cargo_type': self.cargo_type,
            'cargo_description': self.cargo_description,
            'total_units': self.total_units,
            'processed_units': self.processed_units,
            'remaining_units': self.get_remaining_units(),
            'progress_percentage': self.get_progress_percentage(),
            'zone_assignment': self.zone_assignment,
            'deck_level': self.deck_level,
            'location_on_vessel': self.location_on_vessel,
            'status': self.status,
            'priority': self.priority,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'scheduled_completion': self.scheduled_completion.isoformat() if self.scheduled_completion else None,
            'actual_completion': self.actual_completion.isoformat() if self.actual_completion else None,
            'total_weight_kg': self.total_weight_kg,
            'total_volume_m3': self.total_volume_m3,
            'dangerous_goods': self.dangerous_goods,
            'hazmat_class': self.hazmat_class,
            'manifest_reference': self.manifest_reference,
            'customs_reference': self.customs_reference,
            'special_handling_notes': self.special_handling_notes,
            'is_complete': self.is_complete(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }