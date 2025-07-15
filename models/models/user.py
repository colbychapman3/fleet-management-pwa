"""
User model for authentication and role management
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash

# Import db from app.py to avoid circular imports
from app import db

class User(UserMixin, db.Model):
    """User model with role-based access control"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='worker')  # 'manager', 'worker', 'auto_ops_lead', 'heavy_ops_lead', 'stevedore', 'driver'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    last_sync = db.Column(db.DateTime)
    
    # Profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True)
    
    # Maritime-specific fields (merged from both versions)
    employee_id = db.Column(db.String(20), unique=True, index=True)
    license_number = db.Column(db.String(50))
    license_expiry = db.Column(db.Date)
    certification_level = db.Column(db.String(50))  # Basic, Advanced, Expert
    zone_access = db.Column(db.JSON)  # List of zones user can access ['BRV', 'ZEE', 'SOU']
    shift_schedule = db.Column(db.JSON)  # Shift pattern information
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Stevedore-specific fields
    specialization = db.Column(db.String(50))  # 'auto_ops', 'heavy_ops', 'general', 'crane_operator', etc.
    experience_years = db.Column(db.Integer, default=0)
    current_shift = db.Column(db.String(20))  # 'day', 'night', 'swing'
    is_team_lead = db.Column(db.Boolean, default=False)
    safety_rating = db.Column(db.Float, default=100.0)  # Safety score out of 100
    
    # Performance metrics
    operations_completed = db.Column(db.Integer, default=0)
    average_efficiency = db.Column(db.Float, default=0.0)
    safety_incidents = db.Column(db.Integer, default=0)
    
    # Relationships
    vessel = db.relationship('Vessel', backref='crew_members', lazy=True)
    tasks_assigned = db.relationship('Task', foreign_keys='Task.assigned_to_id', 
                                   backref='assigned_to', lazy='dynamic')
    tasks_created = db.relationship('Task', foreign_keys='Task.created_by_id', 
                                  backref='created_by', lazy='dynamic')
    sync_logs = db.relationship('SyncLog', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_manager(self):
        """Check if user has manager role"""
        return self.role == 'manager'
    
    def is_worker(self):
        """Check if user has worker role"""
        return self.role == 'worker'
    
    def is_auto_ops_lead(self):
        """Check if user has auto operations lead role"""
        return self.role == 'auto_ops_lead'
    
    def is_heavy_ops_lead(self):
        """Check if user has heavy operations lead role"""
        return self.role == 'heavy_ops_lead'
    
    def is_stevedore(self):
        """Check if user has stevedore role"""
        return self.role == 'stevedore'
    
    def is_driver(self):
        """Check if user has driver role"""
        return self.role == 'driver'
    
    def has_zone_access(self, zone):
        """Check if user has access to a specific zone"""
        if not self.zone_access:
            return False
        return zone in self.zone_access
    
    def is_license_valid(self):
        """Check if user's license is still valid"""
        if not self.license_expiry:
            return True
        from datetime import date
        return self.license_expiry > date.today()
    
    def get_maritime_role_display(self):
        """Get user-friendly maritime role display"""
        role_map = {
            'manager': 'Operations Manager',
            'worker': 'Port Worker',
            'auto_ops_lead': 'Automobile Operations Lead',
            'heavy_ops_lead': 'Heavy Operations Lead',
            'stevedore': 'Stevedore',
            'driver': 'TICO Driver'
        }
        return role_map.get(self.role, self.role.title())
    
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
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary for API responses"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'vessel_id': self.vessel_id,
            'full_name': self.get_full_name(),
            'employee_id': self.employee_id,
            'license_number': self.license_number,
            'license_expiry': self.license_expiry.isoformat() if self.license_expiry else None,
            'certification_level': self.certification_level,
            'zone_access': self.zone_access,
            'shift_schedule': self.shift_schedule,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'maritime_role_display': self.get_maritime_role_display(),
            'is_license_valid': self.is_license_valid()
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    @staticmethod
    def get_active_users_count():
        """Get count of active users"""
        return User.query.filter_by(is_active=True).count()
    
    @staticmethod
    def get_managers():
        """Get all manager users"""
        return User.query.filter_by(role='manager', is_active=True).all()
    
    @staticmethod
    def get_workers():
        """Get all worker users"""
        return User.query.filter_by(role='worker', is_active=True).all()
    
    @staticmethod
    def get_by_vessel(vessel_id):
        """Get all users assigned to a specific vessel"""
        return User.query.filter_by(vessel_id=vessel_id, is_active=True).all()
    
    @staticmethod
    def get_by_role(role):
        """Get all users with a specific role"""
        return User.query.filter_by(role=role, is_active=True).all()
    
    @staticmethod
    def get_by_zone_access(zone):
        """Get all users with access to a specific zone"""
        return User.query.filter(
            User.zone_access.contains([zone]),
            User.is_active == True
        ).all()
    
    @staticmethod
    def get_stevedores():
        """Get all stevedore users"""
        return User.query.filter_by(role='stevedore', is_active=True).all()
    
    @staticmethod
    def get_drivers():
        """Get all driver users"""
        return User.query.filter_by(role='driver', is_active=True).all()
    
    @staticmethod
    def get_ops_leads():
        """Get all operations lead users"""
        return User.query.filter(
            User.role.in_(['auto_ops_lead', 'heavy_ops_lead']),
            User.is_active == True
        ).all()
    
    @staticmethod
    def get_expired_licenses():
        """Get users with expired licenses"""
        from datetime import date
        return User.query.filter(
            User.license_expiry < date.today(),
            User.is_active == True
        ).all()