"""
Team management models for stevedore operations
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
import json

class StevedoreTeam(db.Model):
    """Team model for stevedore operations"""
    
    __tablename__ = 'stevedore_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team_type = db.Column(db.String(50), nullable=False)  # 'auto_ops', 'heavy_ops', 'general'
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive', 'assigned'
    shift = db.Column(db.String(20), default='day')  # 'day', 'night', 'rotating'
    
    # Performance metrics
    total_operations = db.Column(db.Integer, default=0)
    successful_operations = db.Column(db.Integer, default=0)
    average_efficiency = db.Column(db.Float, default=0.0)  # percentage
    safety_incidents = db.Column(db.Integer, default=0)
    last_operation_date = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy='dynamic')
    assignments = db.relationship('TeamAssignment', backref='team', lazy='dynamic')
    
    def __repr__(self):
        return f'<StevedoreTeam {self.name}>'
    
    def get_team_lead(self):
        """Get team lead member"""
        return self.members.filter_by(role='lead', status='active').first()
    
    def get_team_assistant(self):
        """Get team assistant member"""
        return self.members.filter_by(role='assistant', status='active').first()
    
    def get_team_workers(self):
        """Get regular team workers"""
        return self.members.filter_by(role='worker', status='active').all()
    
    def get_performance_rating(self):
        """Calculate team performance rating"""
        if self.total_operations == 0:
            return 0
        success_rate = (self.successful_operations / self.total_operations) * 100
        # Factor in safety record
        safety_score = max(0, 100 - (self.safety_incidents * 10))
        return min(100, (success_rate + safety_score + self.average_efficiency) / 3)
    
    def update_performance(self, operation_success=True, efficiency_score=None):
        """Update team performance metrics"""
        self.total_operations += 1
        if operation_success:
            self.successful_operations += 1
        
        if efficiency_score is not None:
            # Calculate running average
            if self.average_efficiency == 0:
                self.average_efficiency = efficiency_score
            else:
                self.average_efficiency = (self.average_efficiency + efficiency_score) / 2
        
        self.last_operation_date = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'team_type': self.team_type,
            'status': self.status,
            'shift': self.shift,
            'total_operations': self.total_operations,
            'successful_operations': self.successful_operations,
            'average_efficiency': self.average_efficiency,
            'safety_incidents': self.safety_incidents,
            'performance_rating': self.get_performance_rating(),
            'last_operation_date': self.last_operation_date.isoformat() if self.last_operation_date else None,
            'created_at': self.created_at.isoformat(),
            'team_lead': self.get_team_lead().to_dict() if self.get_team_lead() else None,
            'team_assistant': self.get_team_assistant().to_dict() if self.get_team_assistant() else None,
            'member_count': self.members.filter_by(status='active').count()
        }

class TeamMember(db.Model):
    """Team member model linking users to teams"""
    
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'lead', 'assistant', 'worker'
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive', 'on_leave'
    
    # Performance tracking
    operations_completed = db.Column(db.Integer, default=0)
    efficiency_rating = db.Column(db.Float, default=0.0)
    safety_record = db.Column(db.Integer, default=0)  # incidents count
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='team_memberships')
    
    def __repr__(self):
        return f'<TeamMember {self.user.username} in {self.team.name}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'team_id': self.team_id,
            'role': self.role,
            'status': self.status,
            'operations_completed': self.operations_completed,
            'efficiency_rating': self.efficiency_rating,
            'safety_record': self.safety_record,
            'joined_at': self.joined_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'full_name': self.user.get_full_name(),
                'email': self.user.email
            }
        }

class TeamAssignment(db.Model):
    """Team assignment to maritime operations"""
    
    __tablename__ = 'team_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'), nullable=False)
    maritime_operation_id = db.Column(db.Integer, db.ForeignKey('maritime_operations.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'auto_ops', 'heavy_ops', 'general'
    status = db.Column(db.String(20), default='assigned')  # 'assigned', 'active', 'completed'
    
    # Performance tracking
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    efficiency_score = db.Column(db.Float)
    completion_notes = db.Column(db.Text)
    
    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maritime_operation = db.relationship('MaritimeOperation', backref='team_assignments')
    
    def __repr__(self):
        return f'<TeamAssignment {self.team.name} to Operation {self.maritime_operation_id}>'
    
    def get_duration_hours(self):
        """Calculate assignment duration in hours"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() / 3600
        return 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'team_id': self.team_id,
            'maritime_operation_id': self.maritime_operation_id,
            'role': self.role,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'efficiency_score': self.efficiency_score,
            'completion_notes': self.completion_notes,
            'duration_hours': self.get_duration_hours(),
            'assigned_at': self.assigned_at.isoformat(),
            'team': self.team.to_dict()
        }

class EquipmentCertification(db.Model):
    """Equipment certification tracking for team members"""
    
    __tablename__ = 'equipment_certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    equipment_type = db.Column(db.String(100), nullable=False)  # 'crane', 'forklift', 'container_handler', etc.
    certification_level = db.Column(db.String(20), nullable=False)  # 'basic', 'intermediate', 'advanced'
    status = db.Column(db.String(20), default='active')  # 'active', 'expired', 'suspended'
    
    # Certification details
    certification_number = db.Column(db.String(50))
    issued_by = db.Column(db.String(100))
    issued_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    renewal_date = db.Column(db.Date)
    
    # Training records
    training_hours = db.Column(db.Integer, default=0)
    practical_hours = db.Column(db.Integer, default=0)
    assessment_score = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='equipment_certifications')
    
    def __repr__(self):
        return f'<EquipmentCertification {self.user.username} - {self.equipment_type}>'
    
    def is_expired(self):
        """Check if certification is expired"""
        if self.expiry_date:
            return datetime.now().date() > self.expiry_date
        return False
    
    def days_until_expiry(self):
        """Calculate days until certification expires"""
        if self.expiry_date:
            delta = self.expiry_date - datetime.now().date()
            return delta.days
        return None
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'equipment_type': self.equipment_type,
            'certification_level': self.certification_level,
            'status': self.status,
            'certification_number': self.certification_number,
            'issued_by': self.issued_by,
            'issued_date': self.issued_date.isoformat() if self.issued_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'renewal_date': self.renewal_date.isoformat() if self.renewal_date else None,
            'training_hours': self.training_hours,
            'practical_hours': self.practical_hours,
            'assessment_score': self.assessment_score,
            'is_expired': self.is_expired(),
            'days_until_expiry': self.days_until_expiry(),
            'created_at': self.created_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'full_name': self.user.get_full_name()
            }
        }

class ShiftSchedule(db.Model):
    """Shift management for stevedore teams"""
    
    __tablename__ = 'shift_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    shift_type = db.Column(db.String(20), nullable=False)  # 'day', 'night', 'swing'
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'active', 'completed', 'cancelled'
    
    # Shift details
    expected_workload = db.Column(db.Integer, default=0)
    actual_workload = db.Column(db.Integer, default=0)
    break_duration = db.Column(db.Integer, default=30)  # minutes
    overtime_hours = db.Column(db.Float, default=0.0)
    
    # Performance
    productivity_score = db.Column(db.Float)
    incidents_reported = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = db.relationship('StevedoreTeam', backref='shift_schedules')
    
    def __repr__(self):
        return f'<ShiftSchedule {self.team.name} - {self.shift_date}>'
    
    def get_shift_duration_hours(self):
        """Calculate shift duration in hours"""
        from datetime import datetime, timedelta
        start_dt = datetime.combine(self.shift_date, self.start_time)
        end_dt = datetime.combine(self.shift_date, self.end_time)
        
        # Handle overnight shifts
        if self.end_time < self.start_time:
            end_dt += timedelta(days=1)
        
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'team_id': self.team_id,
            'shift_date': self.shift_date.isoformat(),
            'shift_type': self.shift_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'status': self.status,
            'expected_workload': self.expected_workload,
            'actual_workload': self.actual_workload,
            'break_duration': self.break_duration,
            'overtime_hours': self.overtime_hours,
            'productivity_score': self.productivity_score,
            'incidents_reported': self.incidents_reported,
            'notes': self.notes,
            'shift_duration_hours': self.get_shift_duration_hours(),
            'created_at': self.created_at.isoformat(),
            'team': {
                'id': self.team.id,
                'name': self.team.name,
                'team_type': self.team.team_type
            }
        }