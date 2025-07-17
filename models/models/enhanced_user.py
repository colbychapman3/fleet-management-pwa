"""
Enhanced User model with maritime-specific roles, certifications, and stevedoring operations
"""

from datetime import datetime, timedelta
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from sqlalchemy import Index, DECIMAL
from app import db

class User(UserMixin, db.Model):
    """Enhanced User model with maritime roles and stevedoring operations"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Enhanced role system for maritime operations
    role = db.Column(db.String(30), nullable=False, default='general_stevedore')
    # Roles: 'port_manager', 'operations_manager', 'auto_ops_lead', 'heavy_ops_lead', 
    #        'general_stevedore', 'equipment_operator', 'safety_officer', 'document_clerk'
    
    # Basic user information
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    last_sync = db.Column(db.DateTime)
    
    # Enhanced profile information for maritime operations
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    employee_id = db.Column(db.String(20), unique=True, index=True)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Maritime-specific fields
    maritime_license_number = db.Column(db.String(50))
    maritime_license_expiry = db.Column(db.Date)
    twic_card_number = db.Column(db.String(20))  # Transportation Worker Identification Credential
    twic_expiry = db.Column(db.Date)
    safety_training_completion = db.Column(db.Date)
    medical_clearance_date = db.Column(db.Date)
    
    # Stevedoring specializations
    auto_operations_certified = db.Column(db.Boolean, default=False)
    heavy_equipment_certified = db.Column(db.Boolean, default=False)
    crane_operator_certified = db.Column(db.Boolean, default=False)
    forklift_certified = db.Column(db.Boolean, default=False)
    dangerous_goods_certified = db.Column(db.Boolean, default=False)
    
    # Work assignment
    current_vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True)
    current_team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'), nullable=True)
    shift_start_time = db.Column(db.Time)
    shift_end_time = db.Column(db.Time)
    hourly_rate = db.Column(DECIMAL(10, 2))
    
    # Performance tracking
    total_hours_worked = db.Column(db.Integer, default=0)
    operations_completed = db.Column(db.Integer, default=0)
    safety_incidents = db.Column(db.Integer, default=0)
    last_safety_training = db.Column(db.Date)
    performance_rating = db.Column(db.Float)  # 1.0 - 5.0 scale
    
    # Availability and status
    availability_status = db.Column(db.String(20), default='available')
    # Status: 'available', 'assigned', 'on_break', 'off_duty', 'sick_leave', 'vacation'
    current_location = db.Column(db.String(100))  # Current work location in port
    radio_call_sign = db.Column(db.String(10))
    
    # Relationships
    current_vessel = db.relationship('Vessel', foreign_keys=[current_vessel_id], backref='current_crew', lazy=True)
    current_team = db.relationship('StevedoreTeam', foreign_keys=[current_team_id], backref='assigned_users', lazy=True)
    
    # Task relationships (from existing model)
    tasks_assigned = db.relationship('Task', foreign_keys='Task.assigned_to_id', 
                                   backref='assigned_to', lazy='dynamic')
    tasks_created = db.relationship('Task', foreign_keys='Task.created_by_id', 
                                  backref='created_by', lazy='dynamic')
    
    # Maritime-specific relationships
    operation_assignments = db.relationship('OperationAssignment', backref='worker', lazy='dynamic')
    equipment_assignments = db.relationship('EquipmentAssignment', backref='operator', lazy='dynamic')
    time_logs = db.relationship('WorkTimeLog', backref='worker', lazy='dynamic')
    
    # Offline sync tracking
    sync_logs = db.relationship('SyncLog', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    # Role checking methods
    def is_port_manager(self):
        return self.role == 'port_manager'
    
    def is_operations_manager(self):
        return self.role == 'operations_manager'
    
    def is_team_lead(self):
        return self.role in ['auto_ops_lead', 'heavy_ops_lead']
    
    def is_auto_ops_lead(self):
        return self.role == 'auto_ops_lead'
    
    def is_heavy_ops_lead(self):
        return self.role == 'heavy_ops_lead'
    
    def is_stevedore(self):
        return self.role == 'general_stevedore'
    
    def is_equipment_operator(self):
        return self.role == 'equipment_operator'
    
    def is_safety_officer(self):
        return self.role == 'safety_officer'
    
    def is_document_clerk(self):
        return self.role == 'document_clerk'
    
    def has_management_role(self):
        """Check if user has any management role"""
        return self.role in ['port_manager', 'operations_manager', 'auto_ops_lead', 'heavy_ops_lead']
    
    def can_assign_tasks(self):
        """Check if user can assign tasks to others"""
        return self.has_management_role() or self.is_safety_officer()
    
    def can_operate_equipment(self, equipment_type):
        """Check if user is certified to operate specific equipment"""
        equipment_certifications = {
            'crane': self.crane_operator_certified,
            'forklift': self.forklift_certified,
            'heavy_equipment': self.heavy_equipment_certified
        }
        return equipment_certifications.get(equipment_type.lower(), False)
    
    # Certification and training methods
    def is_twic_valid(self):
        """Check if TWIC card is valid"""
        if not self.twic_expiry:
            return False
        return self.twic_expiry > datetime.now().date()
    
    def is_maritime_license_valid(self):
        """Check if maritime license is valid"""
        if not self.maritime_license_expiry:
            return False
        return self.maritime_license_expiry > datetime.now().date()
    
    def is_safety_training_current(self):
        """Check if safety training is current (within 1 year)"""
        if not self.safety_training_completion:
            return False
        return (datetime.now().date() - self.safety_training_completion).days <= 365
    
    def is_medical_clearance_current(self):
        """Check if medical clearance is current (within 1 year)"""
        if not self.medical_clearance_date:
            return False
        return (datetime.now().date() - self.medical_clearance_date).days <= 365
    
    def is_fully_certified(self):
        """Check if user has all required certifications current"""
        return (self.is_twic_valid() and 
                self.is_maritime_license_valid() and 
                self.is_safety_training_current() and 
                self.is_medical_clearance_current())
    
    def get_certification_warnings(self):
        """Get list of certifications that are expiring or expired"""
        warnings = []
        warning_days = 30  # Warn 30 days before expiry
        
        if self.twic_expiry:
            days_to_expiry = (self.twic_expiry - datetime.now().date()).days
            if days_to_expiry <= 0:
                warnings.append(f"TWIC card expired {abs(days_to_expiry)} days ago")
            elif days_to_expiry <= warning_days:
                warnings.append(f"TWIC card expires in {days_to_expiry} days")
        
        if self.maritime_license_expiry:
            days_to_expiry = (self.maritime_license_expiry - datetime.now().date()).days
            if days_to_expiry <= 0:
                warnings.append(f"Maritime license expired {abs(days_to_expiry)} days ago")
            elif days_to_expiry <= warning_days:
                warnings.append(f"Maritime license expires in {days_to_expiry} days")
        
        if not self.is_safety_training_current():
            if self.safety_training_completion:
                days_since = (datetime.now().date() - self.safety_training_completion).days
                warnings.append(f"Safety training expired {days_since - 365} days ago")
            else:
                warnings.append("No safety training on record")
        
        if not self.is_medical_clearance_current():
            if self.medical_clearance_date:
                days_since = (datetime.now().date() - self.medical_clearance_date).days
                warnings.append(f"Medical clearance expired {days_since - 365} days ago")
            else:
                warnings.append("No medical clearance on record")
        
        return warnings
    
    # Work assignment methods
    def assign_to_vessel(self, vessel_id):
        """Assign user to a vessel"""
        self.current_vessel_id = vessel_id
        self.availability_status = 'assigned'
        db.session.commit()
    
    def assign_to_team(self, team_id):
        """Assign user to a stevedore team"""
        self.current_team_id = team_id
        db.session.commit()
    
    def set_availability(self, status):
        """Set user availability status"""
        valid_statuses = ['available', 'assigned', 'on_break', 'off_duty', 'sick_leave', 'vacation']
        if status in valid_statuses:
            self.availability_status = status
            db.session.commit()
    
    def clock_in(self, location=None):
        """Clock in for work"""
        from .work_time_log import WorkTimeLog
        
        # Close any open time logs
        open_log = WorkTimeLog.query.filter_by(
            worker_id=self.id,
            clock_out_time=None
        ).first()
        
        if open_log:
            open_log.clock_out_time = datetime.utcnow()
        
        # Create new time log
        time_log = WorkTimeLog(
            worker_id=self.id,
            clock_in_time=datetime.utcnow(),
            location=location or self.current_location
        )
        db.session.add(time_log)
        self.availability_status = 'assigned' if self.current_vessel_id else 'available'
        db.session.commit()
        return time_log
    
    def clock_out(self):
        """Clock out from work"""
        from .work_time_log import WorkTimeLog
        
        open_log = WorkTimeLog.query.filter_by(
            worker_id=self.id,
            clock_out_time=None
        ).first()
        
        if open_log:
            open_log.clock_out_time = datetime.utcnow()
            # Calculate hours worked
            hours_worked = (open_log.clock_out_time - open_log.clock_in_time).total_seconds() / 3600
            open_log.hours_worked = round(hours_worked, 2)
            self.total_hours_worked = (self.total_hours_worked or 0) + int(hours_worked)
            
        self.availability_status = 'off_duty'
        db.session.commit()
        return open_log
    
    # Performance and analytics methods
    def calculate_efficiency_rating(self):
        """Calculate worker efficiency based on completed operations"""
        if self.operations_completed == 0:
            return 0.0
        
        # Factor in safety incidents (negative impact)
        safety_factor = max(0.5, 1.0 - (self.safety_incidents * 0.1))
        
        # Factor in completed operations vs hours worked
        if self.total_hours_worked > 0:
            operations_per_hour = self.operations_completed / self.total_hours_worked
            efficiency = min(5.0, operations_per_hour * 10)  # Scale to 5.0 max
        else:
            efficiency = 0.0
        
        return round(efficiency * safety_factor, 2)
    
    def update_performance_rating(self):
        """Update performance rating based on recent work"""
        self.performance_rating = self.calculate_efficiency_rating()
        db.session.commit()
    
    def get_current_operation(self):
        """Get current active operation assignment"""
        return self.operation_assignments.filter_by(status='active').first()
    
    def get_work_history(self, days=30):
        """Get work history for specified number of days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.time_logs.filter(
            db.func.date(WorkTimeLog.clock_in_time) >= cutoff_date.date()
        ).order_by(WorkTimeLog.clock_in_time.desc()).all()
    
    # Utility methods
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def update_last_sync(self):
        """Update last sync timestamp"""
        self.last_sync = datetime.utcnow()
        db.session.commit()
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_display_role(self):
        """Get human-readable role display"""
        role_map = {
            'port_manager': 'Port Manager',
            'operations_manager': 'Operations Manager',
            'auto_ops_lead': 'Auto Operations Lead',
            'heavy_ops_lead': 'Heavy Operations Lead',
            'general_stevedore': 'General Stevedore',
            'equipment_operator': 'Equipment Operator',
            'safety_officer': 'Safety Officer',
            'document_clerk': 'Document Clerk'
        }
        return role_map.get(self.role, self.role.replace('_', ' ').title())
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary for API responses"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'display_role': self.get_display_role(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'phone': self.phone,
            'employee_id': self.employee_id,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            
            # Maritime credentials
            'maritime_license_number': self.maritime_license_number,
            'maritime_license_expiry': self.maritime_license_expiry.isoformat() if self.maritime_license_expiry else None,
            'twic_card_number': self.twic_card_number,
            'twic_expiry': self.twic_expiry.isoformat() if self.twic_expiry else None,
            'safety_training_completion': self.safety_training_completion.isoformat() if self.safety_training_completion else None,
            'medical_clearance_date': self.medical_clearance_date.isoformat() if self.medical_clearance_date else None,
            
            # Certifications
            'auto_operations_certified': self.auto_operations_certified,
            'heavy_equipment_certified': self.heavy_equipment_certified,
            'crane_operator_certified': self.crane_operator_certified,
            'forklift_certified': self.forklift_certified,
            'dangerous_goods_certified': self.dangerous_goods_certified,
            'is_fully_certified': self.is_fully_certified(),
            'certification_warnings': self.get_certification_warnings(),
            
            # Work assignment
            'current_vessel_id': self.current_vessel_id,
            'current_team_id': self.current_team_id,
            'shift_start_time': self.shift_start_time.isoformat() if self.shift_start_time else None,
            'shift_end_time': self.shift_end_time.isoformat() if self.shift_end_time else None,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            
            # Performance
            'total_hours_worked': self.total_hours_worked,
            'operations_completed': self.operations_completed,
            'safety_incidents': self.safety_incidents,
            'performance_rating': self.performance_rating,
            'availability_status': self.availability_status,
            'current_location': self.current_location,
            'radio_call_sign': self.radio_call_sign,
            
            # Relationships
            'current_vessel_name': self.current_vessel.name if self.current_vessel else None,
            'current_team_name': self.current_team.name if self.current_team else None
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    # Static methods for queries
    @staticmethod
    def get_active_users_count():
        """Get count of active users"""
        return User.query.filter_by(is_active=True).count()
    
    @staticmethod
    def get_by_role(role):
        """Get users by role"""
        return User.query.filter_by(role=role, is_active=True).all()
    
    @staticmethod
    def get_team_leads():
        """Get all team lead users"""
        return User.query.filter(
            User.role.in_(['auto_ops_lead', 'heavy_ops_lead']),
            User.is_active == True
        ).all()
    
    @staticmethod
    def get_certified_operators(equipment_type):
        """Get users certified to operate specific equipment"""
        certification_map = {
            'crane': User.crane_operator_certified,
            'forklift': User.forklift_certified,
            'heavy_equipment': User.heavy_equipment_certified
        }
        
        if equipment_type.lower() in certification_map:
            return User.query.filter(
                certification_map[equipment_type.lower()] == True,
                User.is_active == True
            ).all()
        return []
    
    @staticmethod
    def get_available_workers(vessel_id=None):
        """Get available workers, optionally for a specific vessel"""
        query = User.query.filter_by(
            availability_status='available',
            is_active=True
        )
        
        if vessel_id:
            query = query.filter(
                db.or_(
                    User.current_vessel_id == vessel_id,
                    User.current_vessel_id.is_(None)
                )
            )
        
        return query.all()
    
    @staticmethod
    def get_workers_needing_certification_renewal():
        """Get workers with expiring certifications"""
        warning_date = datetime.now().date() + timedelta(days=30)
        
        return User.query.filter(
            db.or_(
                User.twic_expiry <= warning_date,
                User.maritime_license_expiry <= warning_date,
                User.safety_training_completion <= datetime.now().date() - timedelta(days=335),  # 30 days before 1 year
                User.medical_clearance_date <= datetime.now().date() - timedelta(days=335)
            ),
            User.is_active == True
        ).all()

# Create indexes for performance
Index('idx_user_role_active', User.role, User.is_active)
Index('idx_user_vessel_availability', User.current_vessel_id, User.availability_status)
Index('idx_user_employee_id', User.employee_id)
Index('idx_user_certifications', User.auto_operations_certified, User.heavy_equipment_certified, 
      User.crane_operator_certified, User.forklift_certified)