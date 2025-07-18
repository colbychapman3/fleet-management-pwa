"""
WorkTimeLog model for tracking worker clock-in/clock-out times
"""

from datetime import datetime
from app import db

class WorkTimeLog(db.Model):
    """Model for tracking worker time logs"""
    
    __tablename__ = 'work_time_logs'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True, index=True)
    
    # Time tracking
    clock_in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    clock_out_time = db.Column(db.DateTime, nullable=True)
    hours_worked = db.Column(db.Float, nullable=True)
    
    # Location and context
    location = db.Column(db.String(100), nullable=True)
    work_type = db.Column(db.String(50), nullable=True)  # 'stevedoring', 'maintenance', 'admin'
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (will be established by User and Vessel models)
    
    def __repr__(self):
        return f'<WorkTimeLog {self.id}: {self.user_id} - {self.clock_in_time}>'
    
    def calculate_hours_worked(self):
        """Calculate hours worked if clock_out_time is set"""
        if self.clock_out_time and self.clock_in_time:
            delta = self.clock_out_time - self.clock_in_time
            self.hours_worked = round(delta.total_seconds() / 3600, 2)
            return self.hours_worked
        return None
    
    def is_active(self):
        """Check if this is an active (not clocked out) time log"""
        return self.clock_out_time is None
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vessel_id': self.vessel_id,
            'clock_in_time': self.clock_in_time.isoformat() if self.clock_in_time else None,
            'clock_out_time': self.clock_out_time.isoformat() if self.clock_out_time else None,
            'hours_worked': self.hours_worked,
            'location': self.location,
            'work_type': self.work_type,
            'notes': self.notes,
            'is_active': self.is_active(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }