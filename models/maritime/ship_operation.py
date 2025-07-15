"""
ShipOperation model for tracking 4-step wizard operations
"""

from datetime import datetime
from app import db


class ShipOperation(db.Model):
    """Ship operation model for managing 4-step wizard workflow"""
    
    __tablename__ = 'ship_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False, index=True)
    operation_type = db.Column(db.String(50), nullable=False)  # loading, discharging, bunkering
    
    # 4-Step Wizard Progress
    current_step = db.Column(db.Integer, default=1)  # 1-4
    step_1_completed = db.Column(db.Boolean, default=False)  # Vessel arrival & documentation
    step_2_completed = db.Column(db.Boolean, default=False)  # Berth assignment & positioning
    step_3_completed = db.Column(db.Boolean, default=False)  # Cargo operations
    step_4_completed = db.Column(db.Boolean, default=False)  # Departure clearance
    
    # Step 1: Vessel Arrival & Documentation
    arrival_datetime = db.Column(db.DateTime)
    pilot_embarked = db.Column(db.Boolean, default=False)
    customs_clearance = db.Column(db.Boolean, default=False)
    immigration_clearance = db.Column(db.Boolean, default=False)
    port_health_clearance = db.Column(db.Boolean, default=False)
    manifest_submitted = db.Column(db.Boolean, default=False)
    documentation_notes = db.Column(db.Text)
    
    # Step 2: Berth Assignment & Positioning
    berth_assigned = db.Column(db.String(20))
    berth_assignment_time = db.Column(db.DateTime)
    tugboat_assistance = db.Column(db.Boolean, default=False)
    mooring_completed = db.Column(db.Boolean, default=False)
    gangway_position = db.Column(db.String(50))
    safety_briefing_completed = db.Column(db.Boolean, default=False)
    positioning_notes = db.Column(db.Text)
    
    # Step 3: Cargo Operations
    cargo_operation_start = db.Column(db.DateTime)
    cargo_operation_end = db.Column(db.DateTime)
    cargo_type = db.Column(db.String(50))
    total_cargo_quantity = db.Column(db.Float)
    processed_cargo_quantity = db.Column(db.Float, default=0)
    stevedore_team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'))
    equipment_used = db.Column(db.JSON)  # List of equipment IDs used
    zone_assignment = db.Column(db.String(10))  # BRV, ZEE, SOU
    cargo_notes = db.Column(db.Text)
    
    # Step 4: Departure Clearance
    cargo_completion_confirmed = db.Column(db.Boolean, default=False)
    final_customs_clearance = db.Column(db.Boolean, default=False)
    port_dues_paid = db.Column(db.Boolean, default=False)
    departure_clearance_issued = db.Column(db.Boolean, default=False)
    pilot_disembarked = db.Column(db.Boolean, default=False)
    departure_datetime = db.Column(db.DateTime)
    departure_notes = db.Column(db.Text)
    
    # Operation Status
    status = db.Column(db.String(20), default='initiated')  # initiated, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    
    # Personnel assignments
    operation_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    auto_ops_lead_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    heavy_ops_lead_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vessel = db.relationship('Vessel', backref='ship_operations', lazy=True)
    stevedore_team = db.relationship('StevedoreTeam', backref='ship_operations', lazy=True)
    operation_manager = db.relationship('User', foreign_keys=[operation_manager_id], backref='managed_operations', lazy=True)
    auto_ops_lead = db.relationship('User', foreign_keys=[auto_ops_lead_id], backref='auto_operations', lazy=True)
    heavy_ops_lead = db.relationship('User', foreign_keys=[heavy_ops_lead_id], backref='heavy_operations', lazy=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_ship_operations_vessel_status', 'vessel_id', 'status'),
        db.Index('idx_ship_operations_current_step', 'current_step'),
        db.Index('idx_ship_operations_zone', 'zone_assignment'),
    )
    
    def __repr__(self):
        return f'<ShipOperation {self.operation_id}>'
    
    def get_progress_percentage(self):
        """Calculate operation progress percentage"""
        steps_completed = sum([
            self.step_1_completed,
            self.step_2_completed,
            self.step_3_completed,
            self.step_4_completed
        ])
        return (steps_completed / 4) * 100
    
    def advance_to_next_step(self):
        """Advance to the next step if current step is completed"""
        if self.current_step == 1 and self.step_1_completed:
            self.current_step = 2
        elif self.current_step == 2 and self.step_2_completed:
            self.current_step = 3
        elif self.current_step == 3 and self.step_3_completed:
            self.current_step = 4
        elif self.current_step == 4 and self.step_4_completed:
            self.status = 'completed'
        
        self.updated_at = datetime.utcnow()
        return self.current_step
    
    def complete_step_1(self, **kwargs):
        """Complete step 1 - Vessel arrival & documentation"""
        self.arrival_datetime = kwargs.get('arrival_datetime', datetime.utcnow())
        self.pilot_embarked = kwargs.get('pilot_embarked', False)
        self.customs_clearance = kwargs.get('customs_clearance', False)
        self.immigration_clearance = kwargs.get('immigration_clearance', False)
        self.port_health_clearance = kwargs.get('port_health_clearance', False)
        self.manifest_submitted = kwargs.get('manifest_submitted', False)
        self.documentation_notes = kwargs.get('documentation_notes', '')
        
        # Check if all required items are completed
        required_items = [
            self.pilot_embarked, self.customs_clearance, self.immigration_clearance,
            self.port_health_clearance, self.manifest_submitted
        ]
        
        if all(required_items):
            self.step_1_completed = True
            self.advance_to_next_step()
        
        self.updated_at = datetime.utcnow()
    
    def complete_step_2(self, **kwargs):
        """Complete step 2 - Berth assignment & positioning"""
        self.berth_assigned = kwargs.get('berth_assigned')
        self.berth_assignment_time = kwargs.get('berth_assignment_time', datetime.utcnow())
        self.tugboat_assistance = kwargs.get('tugboat_assistance', False)
        self.mooring_completed = kwargs.get('mooring_completed', False)
        self.gangway_position = kwargs.get('gangway_position')
        self.safety_briefing_completed = kwargs.get('safety_briefing_completed', False)
        self.positioning_notes = kwargs.get('positioning_notes', '')
        
        # Check if all required items are completed
        required_items = [
            self.berth_assigned is not None,
            self.mooring_completed,
            self.safety_briefing_completed
        ]
        
        if all(required_items):
            self.step_2_completed = True
            self.advance_to_next_step()
        
        self.updated_at = datetime.utcnow()
    
    def complete_step_3(self, **kwargs):
        """Complete step 3 - Cargo operations"""
        self.cargo_operation_start = kwargs.get('cargo_operation_start')
        self.cargo_operation_end = kwargs.get('cargo_operation_end')
        self.cargo_type = kwargs.get('cargo_type')
        self.total_cargo_quantity = kwargs.get('total_cargo_quantity')
        self.processed_cargo_quantity = kwargs.get('processed_cargo_quantity', 0)
        self.stevedore_team_id = kwargs.get('stevedore_team_id')
        self.equipment_used = kwargs.get('equipment_used', [])
        self.zone_assignment = kwargs.get('zone_assignment')
        self.cargo_notes = kwargs.get('cargo_notes', '')
        
        # Check if cargo operation is completed
        if (self.processed_cargo_quantity and self.total_cargo_quantity and 
            self.processed_cargo_quantity >= self.total_cargo_quantity):
            self.step_3_completed = True
            self.advance_to_next_step()
        
        self.updated_at = datetime.utcnow()
    
    def complete_step_4(self, **kwargs):
        """Complete step 4 - Departure clearance"""
        self.cargo_completion_confirmed = kwargs.get('cargo_completion_confirmed', False)
        self.final_customs_clearance = kwargs.get('final_customs_clearance', False)
        self.port_dues_paid = kwargs.get('port_dues_paid', False)
        self.departure_clearance_issued = kwargs.get('departure_clearance_issued', False)
        self.pilot_disembarked = kwargs.get('pilot_disembarked', False)
        self.departure_datetime = kwargs.get('departure_datetime')
        self.departure_notes = kwargs.get('departure_notes', '')
        
        # Check if all required items are completed
        required_items = [
            self.cargo_completion_confirmed,
            self.final_customs_clearance,
            self.port_dues_paid,
            self.departure_clearance_issued,
            self.pilot_disembarked
        ]
        
        if all(required_items):
            self.step_4_completed = True
            self.status = 'completed'
            self.advance_to_next_step()
        
        self.updated_at = datetime.utcnow()
    
    def update_cargo_progress(self, processed_quantity):
        """Update cargo processing progress"""
        self.processed_cargo_quantity = processed_quantity
        
        # Auto-complete step 3 if all cargo is processed
        if (self.total_cargo_quantity and 
            processed_quantity >= self.total_cargo_quantity and 
            not self.step_3_completed):
            self.step_3_completed = True
            self.advance_to_next_step()
        
        self.updated_at = datetime.utcnow()
    
    def get_current_step_description(self):
        """Get description of current step"""
        step_descriptions = {
            1: "Vessel Arrival & Documentation",
            2: "Berth Assignment & Positioning", 
            3: "Cargo Operations",
            4: "Departure Clearance"
        }
        return step_descriptions.get(self.current_step, "Unknown Step")
    
    def get_step_requirements(self, step_number):
        """Get requirements for a specific step"""
        requirements = {
            1: ["Pilot embarked", "Customs clearance", "Immigration clearance", 
                "Port health clearance", "Manifest submitted"],
            2: ["Berth assigned", "Mooring completed", "Safety briefing completed"],
            3: ["Cargo operations started", "All cargo processed", "Equipment properly used"],
            4: ["Cargo completion confirmed", "Final customs clearance", 
                "Port dues paid", "Departure clearance issued", "Pilot disembarked"]
        }
        return requirements.get(step_number, [])
    
    def can_proceed_to_step(self, step_number):
        """Check if operation can proceed to a specific step"""
        if step_number <= self.current_step:
            return True
        
        # Check if previous steps are completed
        if step_number == 2:
            return self.step_1_completed
        elif step_number == 3:
            return self.step_1_completed and self.step_2_completed
        elif step_number == 4:
            return self.step_1_completed and self.step_2_completed and self.step_3_completed
        
        return False
    
    def to_dict(self):
        """Convert ship operation to dictionary for API responses"""
        return {
            'id': self.id,
            'operation_id': self.operation_id,
            'vessel_id': self.vessel_id,
            'operation_type': self.operation_type,
            'current_step': self.current_step,
            'current_step_description': self.get_current_step_description(),
            'progress_percentage': self.get_progress_percentage(),
            'step_1_completed': self.step_1_completed,
            'step_2_completed': self.step_2_completed,
            'step_3_completed': self.step_3_completed,
            'step_4_completed': self.step_4_completed,
            
            # Step 1 data
            'arrival_datetime': self.arrival_datetime.isoformat() if self.arrival_datetime else None,
            'pilot_embarked': self.pilot_embarked,
            'customs_clearance': self.customs_clearance,
            'immigration_clearance': self.immigration_clearance,
            'port_health_clearance': self.port_health_clearance,
            'manifest_submitted': self.manifest_submitted,
            'documentation_notes': self.documentation_notes,
            
            # Step 2 data
            'berth_assigned': self.berth_assigned,
            'berth_assignment_time': self.berth_assignment_time.isoformat() if self.berth_assignment_time else None,
            'tugboat_assistance': self.tugboat_assistance,
            'mooring_completed': self.mooring_completed,
            'gangway_position': self.gangway_position,
            'safety_briefing_completed': self.safety_briefing_completed,
            'positioning_notes': self.positioning_notes,
            
            # Step 3 data
            'cargo_operation_start': self.cargo_operation_start.isoformat() if self.cargo_operation_start else None,
            'cargo_operation_end': self.cargo_operation_end.isoformat() if self.cargo_operation_end else None,
            'cargo_type': self.cargo_type,
            'total_cargo_quantity': self.total_cargo_quantity,
            'processed_cargo_quantity': self.processed_cargo_quantity,
            'stevedore_team_id': self.stevedore_team_id,
            'equipment_used': self.equipment_used,
            'zone_assignment': self.zone_assignment,
            'cargo_notes': self.cargo_notes,
            
            # Step 4 data
            'cargo_completion_confirmed': self.cargo_completion_confirmed,
            'final_customs_clearance': self.final_customs_clearance,
            'port_dues_paid': self.port_dues_paid,
            'departure_clearance_issued': self.departure_clearance_issued,
            'pilot_disembarked': self.pilot_disembarked,
            'departure_datetime': self.departure_datetime.isoformat() if self.departure_datetime else None,
            'departure_notes': self.departure_notes,
            
            # General data
            'status': self.status,
            'priority': self.priority,
            'operation_manager_id': self.operation_manager_id,
            'auto_ops_lead_id': self.auto_ops_lead_id,
            'heavy_ops_lead_id': self.heavy_ops_lead_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            
            # Related data
            'vessel_name': self.vessel.name if self.vessel else None,
            'operation_manager_name': self.operation_manager.get_full_name() if self.operation_manager else None,
            'auto_ops_lead_name': self.auto_ops_lead.get_full_name() if self.auto_ops_lead else None,
            'heavy_ops_lead_name': self.heavy_ops_lead.get_full_name() if self.heavy_ops_lead else None,
            'stevedore_team_name': self.stevedore_team.team_name if self.stevedore_team else None
        }
    
    @staticmethod
    def get_active_operations():
        """Get all active ship operations"""
        return ShipOperation.query.filter(
            ShipOperation.status.in_(['initiated', 'in_progress'])
        ).order_by(ShipOperation.created_at.desc()).all()
    
    @staticmethod
    def get_operations_by_vessel(vessel_id):
        """Get ship operations for a specific vessel"""
        return ShipOperation.query.filter_by(vessel_id=vessel_id).order_by(
            ShipOperation.created_at.desc()
        ).all()
    
    @staticmethod
    def get_operations_by_zone(zone):
        """Get ship operations for a specific zone"""
        return ShipOperation.query.filter_by(zone_assignment=zone).order_by(
            ShipOperation.created_at.desc()
        ).all()
    
    @staticmethod
    def get_operations_by_step(step_number):
        """Get operations currently at a specific step"""
        return ShipOperation.query.filter_by(current_step=step_number).order_by(
            ShipOperation.created_at.asc()
        ).all()
    
    @staticmethod
    def get_operations_by_status(status):
        """Get operations by status"""
        return ShipOperation.query.filter_by(status=status).order_by(
            ShipOperation.created_at.desc()
        ).all()
    
    @staticmethod
    def get_overdue_operations():
        """Get operations that are taking too long"""
        # Define operation as overdue if it's been more than 72 hours without completion
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=72)
        
        return ShipOperation.query.filter(
            ShipOperation.status.in_(['initiated', 'in_progress']),
            ShipOperation.created_at < cutoff_time
        ).all()
    
    @staticmethod
    def generate_operation_id(vessel_name, operation_type):
        """Generate unique operation ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        vessel_short = ''.join([c for c in vessel_name.upper() if c.isalpha()])[:6]
        operation_short = operation_type.upper()[:3]
        return f"{vessel_short}-{operation_short}-{timestamp}"