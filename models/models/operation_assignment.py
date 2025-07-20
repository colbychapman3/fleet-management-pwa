"""
OperationAssignment model for tracking user assignments to maritime operations
"""
from datetime import datetime
from app import db

class OperationAssignment(db.Model):
    """Track user assignments to maritime operations"""
    
    __tablename__ = 'operation_assignments'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    operation_id = db.Column(db.Integer, db.ForeignKey('ship_operations.id'), nullable=False, index=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True, index=True)
    
    # Assignment details
    role = db.Column(db.String(50), nullable=False)  # 'operator', 'supervisor', 'manager', 'specialist'
    assignment_type = db.Column(db.String(30), nullable=False)  # 'primary', 'backup', 'support'
    status = db.Column(db.String(20), default='assigned', nullable=False)  # 'assigned', 'active', 'completed', 'cancelled'
    
    # Scheduling
    scheduled_start = db.Column(db.DateTime, nullable=True)
    scheduled_end = db.Column(db.DateTime, nullable=True)
    actual_start = db.Column(db.DateTime, nullable=True)
    actual_end = db.Column(db.DateTime, nullable=True)
    
    # Assignment metadata
    priority = db.Column(db.String(20), default='normal', nullable=False)  # 'low', 'normal', 'high', 'urgent'
    notes = db.Column(db.Text, nullable=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    operation = db.relationship('ShipOperation', foreign_keys=[operation_id])
    vessel = db.relationship('Vessel', foreign_keys=[vessel_id], back_populates='operation_assignments')
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id])
    
    def __repr__(self):
        return f'<OperationAssignment {self.user_id} -> {self.operation_id} ({self.role})>'
    
    def start_assignment(self):
        """Mark assignment as active and record start time"""
        self.status = 'active'
        self.actual_start = datetime.utcnow()
        db.session.commit()
    
    def complete_assignment(self):
        """Mark assignment as completed and record end time"""
        self.status = 'completed'
        self.actual_end = datetime.utcnow()
        db.session.commit()
    
    def cancel_assignment(self):
        """Cancel the assignment"""
        self.status = 'cancelled'
        db.session.commit()
    
    def to_dict(self):
        """Convert assignment to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'operation_id': self.operation_id,
            'vessel_id': self.vessel_id,
            'role': self.role,
            'assignment_type': self.assignment_type,
            'status': self.status,
            'scheduled_start': self.scheduled_start.isoformat() if self.scheduled_start else None,
            'scheduled_end': self.scheduled_end.isoformat() if self.scheduled_end else None,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'priority': self.priority,
            'notes': self.notes,
            'assigned_by_id': self.assigned_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_assignments(cls, user_id, status=None):
        """Get assignments for a specific user"""
        query = cls.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_operation_assignments(cls, operation_id):
        """Get all assignments for a specific operation"""
        return cls.query.filter_by(operation_id=operation_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_active_assignments(cls):
        """Get all active assignments"""
        return cls.query.filter_by(status='active').order_by(cls.created_at.desc()).all()