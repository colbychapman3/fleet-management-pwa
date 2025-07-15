"""
StevedoreTeam model for team composition and assignment management
"""

from datetime import datetime, time
from app import db


class StevedoreTeam(db.Model):
    """Stevedore team model for managing team composition and assignments"""
    
    __tablename__ = 'stevedore_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    team_name = db.Column(db.String(100), nullable=False)
    
    # Team Leadership
    team_leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    
    # Team Composition
    total_members = db.Column(db.Integer, default=0)
    active_members = db.Column(db.Integer, default=0)
    specialized_roles = db.Column(db.JSON)  # Dict of role: count
    
    # Operational Details
    shift_pattern = db.Column(db.String(20), default='day')  # day, night, rotating, on_call
    shift_start_time = db.Column(db.Time)
    shift_end_time = db.Column(db.Time)
    zone_assignment = db.Column(db.String(10))  # BRV, ZEE, SOU
    cargo_specialization = db.Column(db.JSON)  # List of cargo types they handle
    
    # Equipment and Certifications
    certified_equipment = db.Column(db.JSON)  # List of equipment they're certified to use
    safety_certifications = db.Column(db.JSON)  # Safety certifications
    hazmat_certified = db.Column(db.Boolean, default=False)
    crane_certified = db.Column(db.Boolean, default=False)
    forklift_certified = db.Column(db.Boolean, default=False)
    
    # Performance Metrics
    productivity_rating = db.Column(db.Float, default=0.0)  # 0-10 scale
    safety_record = db.Column(db.Float, default=10.0)  # 10 is perfect safety record
    experience_level = db.Column(db.String(20), default='intermediate')  # novice, intermediate, expert
    
    # Availability and Status
    status = db.Column(db.String(20), default='available', index=True)  # available, assigned, off_duty, training
    current_assignment = db.Column(db.String(100))  # Current operation/vessel
    availability_notes = db.Column(db.Text)
    
    # Team Communication
    radio_channel = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(100))
    team_phone = db.Column(db.String(20))
    
    # Contract and Administrative
    contract_type = db.Column(db.String(20), default='permanent')  # permanent, temporary, contractor
    hourly_rate = db.Column(db.Float)
    overtime_rate = db.Column(db.Float)
    union_affiliation = db.Column(db.String(100))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_assignment = db.Column(db.DateTime)
    
    # Relationships
    team_leader = db.relationship('User', foreign_keys=[team_leader_id], backref='led_teams', lazy=True)
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref='supervised_teams', lazy=True)
    team_members = db.relationship('StevedoreTeamMember', backref='team', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_stevedore_teams_status', 'status'),
        db.Index('idx_stevedore_teams_zone', 'zone_assignment'),
        db.Index('idx_stevedore_teams_shift', 'shift_pattern'),
    )
    
    def __repr__(self):
        return f'<StevedoreTeam {self.team_name}>'
    
    def get_active_members_list(self):
        """Get list of active team members"""
        return self.team_members.filter_by(status='active').all()
    
    def get_member_count_by_role(self, role):
        """Get count of members with specific role"""
        return self.team_members.filter_by(role=role, status='active').count()
    
    def is_available_for_assignment(self):
        """Check if team is available for new assignment"""
        return self.status == 'available' and self.active_members > 0
    
    def has_cargo_specialization(self, cargo_type):
        """Check if team is specialized for specific cargo type"""
        if not self.cargo_specialization:
            return False
        return cargo_type in self.cargo_specialization
    
    def has_equipment_certification(self, equipment_type):
        """Check if team has certification for specific equipment"""
        if not self.certified_equipment:
            return False
        return equipment_type in self.certified_equipment
    
    def is_zone_compatible(self, zone):
        """Check if team can work in specified zone"""
        return self.zone_assignment == zone or self.zone_assignment is None
    
    def is_shift_compatible(self, operation_time):
        """Check if team can work at specified time"""
        if self.shift_pattern == 'on_call':
            return True
        
        if not self.shift_start_time or not self.shift_end_time:
            return True
        
        # Convert operation_time to time object if it's datetime
        if isinstance(operation_time, datetime):
            operation_time = operation_time.time()
        
        # Handle overnight shifts
        if self.shift_start_time > self.shift_end_time:
            return operation_time >= self.shift_start_time or operation_time <= self.shift_end_time
        else:
            return self.shift_start_time <= operation_time <= self.shift_end_time
    
    def assign_to_operation(self, operation_description):
        """Assign team to an operation"""
        if not self.is_available_for_assignment():
            return False
        
        self.status = 'assigned'
        self.current_assignment = operation_description
        self.last_assignment = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True
    
    def complete_assignment(self):
        """Mark assignment as completed"""
        self.status = 'available'
        self.current_assignment = None
        self.updated_at = datetime.utcnow()
    
    def add_member(self, user_id, role, hourly_rate=None):
        """Add a member to the team"""
        # Check if user is already a member
        existing_member = self.team_members.filter_by(user_id=user_id).first()
        if existing_member and existing_member.status == 'active':
            return False
        
        # If user was previously a member, reactivate
        if existing_member:
            existing_member.status = 'active'
            existing_member.role = role
            existing_member.hourly_rate = hourly_rate
        else:
            new_member = StevedoreTeamMember(
                user_id=user_id,
                role=role,
                hourly_rate=hourly_rate,
                status='active'
            )
            self.team_members.append(new_member)
        
        self.update_member_counts()
        return True
    
    def remove_member(self, user_id):
        """Remove a member from the team"""
        member = self.team_members.filter_by(user_id=user_id, status='active').first()
        if member:
            member.status = 'inactive'
            member.departure_date = datetime.utcnow()
            self.update_member_counts()
            return True
        return False
    
    def update_member_counts(self):
        """Update total and active member counts"""
        self.active_members = self.team_members.filter_by(status='active').count()
        self.total_members = self.team_members.count()
        
        # Update specialized roles count
        active_members = self.get_active_members_list()
        role_counts = {}
        for member in active_members:
            role = member.role
            role_counts[role] = role_counts.get(role, 0) + 1
        
        self.specialized_roles = role_counts
        self.updated_at = datetime.utcnow()
    
    def update_productivity_rating(self, rating):
        """Update team productivity rating"""
        if 0 <= rating <= 10:
            self.productivity_rating = rating
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def update_safety_record(self, rating):
        """Update team safety record"""
        if 0 <= rating <= 10:
            self.safety_record = rating
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_performance_summary(self):
        """Get team performance summary"""
        return {
            'productivity_rating': self.productivity_rating,
            'safety_record': self.safety_record,
            'experience_level': self.experience_level,
            'total_assignments': self.get_assignment_count(),
            'average_assignment_duration': self.get_average_assignment_duration()
        }
    
    def get_assignment_count(self):
        """Get total number of assignments completed"""
        # This would typically query assignment history
        # For now, returning placeholder
        return 0
    
    def get_average_assignment_duration(self):
        """Get average duration of assignments"""
        # This would calculate from assignment history
        # For now, returning placeholder
        return 0.0
    
    def to_dict(self):
        """Convert stevedore team to dictionary for API responses"""
        return {
            'id': self.id,
            'team_id': self.team_id,
            'team_name': self.team_name,
            'team_leader_id': self.team_leader_id,
            'supervisor_id': self.supervisor_id,
            'total_members': self.total_members,
            'active_members': self.active_members,
            'specialized_roles': self.specialized_roles,
            
            # Operational details
            'shift_pattern': self.shift_pattern,
            'shift_start_time': self.shift_start_time.isoformat() if self.shift_start_time else None,
            'shift_end_time': self.shift_end_time.isoformat() if self.shift_end_time else None,
            'zone_assignment': self.zone_assignment,
            'cargo_specialization': self.cargo_specialization,
            
            # Equipment and certifications
            'certified_equipment': self.certified_equipment,
            'safety_certifications': self.safety_certifications,
            'hazmat_certified': self.hazmat_certified,
            'crane_certified': self.crane_certified,
            'forklift_certified': self.forklift_certified,
            
            # Performance metrics
            'productivity_rating': self.productivity_rating,
            'safety_record': self.safety_record,
            'experience_level': self.experience_level,
            'performance_summary': self.get_performance_summary(),
            
            # Availability and status
            'status': self.status,
            'current_assignment': self.current_assignment,
            'availability_notes': self.availability_notes,
            'is_available': self.is_available_for_assignment(),
            
            # Communication
            'radio_channel': self.radio_channel,
            'emergency_contact': self.emergency_contact,
            'team_phone': self.team_phone,
            
            # Contract and administrative
            'contract_type': self.contract_type,
            'hourly_rate': self.hourly_rate,
            'overtime_rate': self.overtime_rate,
            'union_affiliation': self.union_affiliation,
            
            # Timestamps
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_assignment': self.last_assignment.isoformat() if self.last_assignment else None,
            
            # Related data
            'team_leader_name': self.team_leader.get_full_name() if self.team_leader else None,
            'supervisor_name': self.supervisor.get_full_name() if self.supervisor else None,
            'members': [member.to_dict() for member in self.get_active_members_list()]
        }
    
    @staticmethod
    def get_available_teams():
        """Get all available stevedore teams"""
        return StevedoreTeam.query.filter_by(status='available').order_by(
            StevedoreTeam.productivity_rating.desc()
        ).all()
    
    @staticmethod
    def get_teams_by_zone(zone):
        """Get teams assigned to or compatible with a specific zone"""
        return StevedoreTeam.query.filter(
            db.or_(
                StevedoreTeam.zone_assignment == zone,
                StevedoreTeam.zone_assignment.is_(None)
            )
        ).all()
    
    @staticmethod
    def get_teams_by_cargo_specialization(cargo_type):
        """Get teams specialized in specific cargo type"""
        return StevedoreTeam.query.filter(
            StevedoreTeam.cargo_specialization.contains([cargo_type])
        ).all()
    
    @staticmethod
    def get_teams_by_shift(shift_pattern):
        """Get teams working specific shift pattern"""
        return StevedoreTeam.query.filter_by(shift_pattern=shift_pattern).all()
    
    @staticmethod
    def get_teams_with_certification(equipment_type):
        """Get teams certified for specific equipment"""
        return StevedoreTeam.query.filter(
            StevedoreTeam.certified_equipment.contains([equipment_type])
        ).all()
    
    @staticmethod
    def find_best_team_for_operation(cargo_type, zone, equipment_needed=None, shift_time=None):
        """Find the best team for a specific operation"""
        query = StevedoreTeam.query.filter_by(status='available')
        
        # Filter by zone compatibility
        query = query.filter(
            db.or_(
                StevedoreTeam.zone_assignment == zone,
                StevedoreTeam.zone_assignment.is_(None)
            )
        )
        
        # Filter by cargo specialization
        query = query.filter(
            StevedoreTeam.cargo_specialization.contains([cargo_type])
        )
        
        # Filter by equipment certification if specified
        if equipment_needed:
            query = query.filter(
                StevedoreTeam.certified_equipment.contains([equipment_needed])
            )
        
        # Order by productivity rating and safety record
        teams = query.order_by(
            StevedoreTeam.productivity_rating.desc(),
            StevedoreTeam.safety_record.desc()
        ).all()
        
        # Filter by shift compatibility if specified
        if shift_time:
            compatible_teams = [team for team in teams if team.is_shift_compatible(shift_time)]
            return compatible_teams[0] if compatible_teams else None
        
        return teams[0] if teams else None
    
    @staticmethod
    def get_team_statistics():
        """Get overall team statistics"""
        total_teams = StevedoreTeam.query.count()
        available_teams = StevedoreTeam.query.filter_by(status='available').count()
        assigned_teams = StevedoreTeam.query.filter_by(status='assigned').count()
        
        avg_productivity = db.session.query(db.func.avg(StevedoreTeam.productivity_rating)).scalar() or 0
        avg_safety = db.session.query(db.func.avg(StevedoreTeam.safety_record)).scalar() or 0
        
        return {
            'total_teams': total_teams,
            'available_teams': available_teams,
            'assigned_teams': assigned_teams,
            'average_productivity': round(avg_productivity, 2),
            'average_safety_record': round(avg_safety, 2)
        }
    
    @staticmethod
    def generate_team_id(team_name):
        """Generate unique team ID"""
        # Extract first 3 letters and add timestamp
        name_part = ''.join([c for c in team_name.upper() if c.isalpha()])[:3]
        timestamp = datetime.utcnow().strftime('%m%d%H%M')
        return f"TEAM-{name_part}-{timestamp}"


class StevedoreTeamMember(db.Model):
    """Individual stevedore team member model"""
    
    __tablename__ = 'stevedore_team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Role and Position
    role = db.Column(db.String(50), nullable=False)  # foreman, crane_operator, signalman, general_worker
    seniority_level = db.Column(db.String(20), default='junior')  # junior, senior, lead
    
    # Employment Details
    status = db.Column(db.String(20), default='active')  # active, inactive, on_leave
    join_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    departure_date = db.Column(db.DateTime)
    hourly_rate = db.Column(db.Float)
    
    # Performance and Training
    individual_productivity = db.Column(db.Float, default=0.0)
    safety_incidents = db.Column(db.Integer, default=0)
    training_completed = db.Column(db.JSON)  # List of completed training
    certifications = db.Column(db.JSON)  # Individual certifications
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='stevedore_memberships', lazy=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_team_members_user_status', 'user_id', 'status'),
        db.Index('idx_team_members_role', 'role'),
        db.UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
    )
    
    def __repr__(self):
        return f'<StevedoreTeamMember {self.user_id} in team {self.team_id}>'
    
    def to_dict(self):
        """Convert team member to dictionary for API responses"""
        return {
            'id': self.id,
            'team_id': self.team_id,
            'user_id': self.user_id,
            'role': self.role,
            'seniority_level': self.seniority_level,
            'status': self.status,
            'join_date': self.join_date.isoformat(),
            'departure_date': self.departure_date.isoformat() if self.departure_date else None,
            'hourly_rate': self.hourly_rate,
            'individual_productivity': self.individual_productivity,
            'safety_incidents': self.safety_incidents,
            'training_completed': self.training_completed,
            'certifications': self.certifications,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            
            # Related data
            'user_name': self.user.get_full_name() if self.user else None,
            'user_employee_id': self.user.employee_id if self.user else None
        }