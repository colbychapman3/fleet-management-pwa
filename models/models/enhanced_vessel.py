"""
Enhanced Vessel model with maritime-specific operations, cargo tracking, and stevedoring features
"""

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import Index, text, DECIMAL
from app import db

class Vessel(db.Model):
    """Enhanced Vessel model for maritime stevedoring operations"""
    
    __tablename__ = 'vessels'
    
    # Basic vessel identification
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    imo_number = db.Column(db.String(20), unique=True, nullable=True, index=True)
    call_sign = db.Column(db.String(20), index=True)
    mmsi_number = db.Column(db.String(15), index=True)  # Maritime Mobile Service Identity
    vessel_type = db.Column(db.String(50), nullable=False)
    flag = db.Column(db.String(50))
    owner = db.Column(db.String(100))
    operator = db.Column(db.String(100))
    agent = db.Column(db.String(100))  # Local shipping agent
    
    # Technical specifications
    length = db.Column(db.Float)  # meters
    beam = db.Column(db.Float)   # meters
    draft = db.Column(db.Float)  # meters
    max_draft = db.Column(db.Float)  # meters
    gross_tonnage = db.Column(db.Integer)
    net_tonnage = db.Column(db.Integer)
    deadweight_tonnage = db.Column(db.Integer)
    
    # Cargo specifications
    cargo_capacity = db.Column(db.Integer)  # Total units (cars, containers, etc.)
    cargo_types_supported = db.Column(db.JSON)  # ['automobiles', 'containers', 'bulk', 'breakbulk']
    has_ramp = db.Column(db.Boolean, default=False)
    ramp_capacity = db.Column(db.Integer)  # Max tonnage on ramp
    deck_count = db.Column(db.Integer, default=1)
    
    # Operational status
    status = db.Column(db.String(30), default='expected', index=True)
    # Status: 'expected', 'arrived', 'berthed', 'operations_active', 'operations_complete', 'departed'
    
    # Port operations
    berth_id = db.Column(db.Integer, db.ForeignKey('berths.id'), nullable=True, index=True)
    current_port = db.Column(db.String(100))
    previous_port = db.Column(db.String(100))
    next_port = db.Column(db.String(100))
    
    # Scheduling
    eta = db.Column(db.DateTime, index=True)  # Estimated Time of Arrival
    ata = db.Column(db.DateTime)  # Actual Time of Arrival
    etb = db.Column(db.DateTime)  # Estimated Time of Berthing
    atb = db.Column(db.DateTime)  # Actual Time of Berthing
    etc = db.Column(db.DateTime)  # Estimated Time of Completion
    atc = db.Column(db.DateTime)  # Actual Time of Completion
    etd = db.Column(db.DateTime)  # Estimated Time of Departure
    atd = db.Column(db.DateTime)  # Actual Time of Departure
    
    # Maritime zones and targets
    brv_target = db.Column(db.Integer)  # BRV zone target units
    zee_target = db.Column(db.Integer)  # ZEE zone target units
    sou_target = db.Column(db.Integer)  # SOU zone target units
    total_discharge_target = db.Column(db.Integer)  # Total units to discharge
    
    # Progress tracking
    brv_completed = db.Column(db.Integer, default=0)
    zee_completed = db.Column(db.Integer, default=0)
    sou_completed = db.Column(db.Integer, default=0)
    total_discharged = db.Column(db.Integer, default=0)
    
    # Operation details
    operation_type = db.Column(db.String(30))  # 'discharge', 'load', 'both'
    priority_level = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    weather_restrictions = db.Column(db.Boolean, default=False)
    tide_restrictions = db.Column(db.Boolean, default=False)
    
    # Documentation
    manifest_received = db.Column(db.Boolean, default=False)
    customs_cleared = db.Column(db.Boolean, default=False)
    port_clearance = db.Column(db.Boolean, default=False)
    dangerous_goods_declared = db.Column(db.Boolean, default=False)
    hazmat_details = db.Column(db.Text)
    
    # Financial
    port_dues = db.Column(DECIMAL(10, 2))
    stevedoring_cost = db.Column(DECIMAL(10, 2))
    equipment_cost = db.Column(DECIMAL(10, 2))
    total_cost = db.Column(DECIMAL(10, 2))
    billing_status = db.Column(db.String(20), default='pending')
    
    # Communication
    master_name = db.Column(db.String(100))
    master_phone = db.Column(db.String(20))
    master_email = db.Column(db.String(120))
    chief_officer_name = db.Column(db.String(100))
    ship_phone = db.Column(db.String(20))
    ship_email = db.Column(db.String(120))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    berth = db.relationship('Berth', backref='vessels', lazy=True)
    operations = db.relationship('ShipOperation', backref='vessel', lazy='dynamic', cascade='all, delete-orphan')
    cargo_batches = db.relationship('CargoBatch', backref='vessel', lazy='dynamic', cascade='all, delete-orphan')
    equipment_assignments = db.relationship('EquipmentAssignment', backref='vessel', lazy='dynamic')
    operation_assignments = db.relationship('OperationAssignment', backref='vessel', lazy='dynamic')
    tasks = db.relationship('Task', backref='vessel', lazy='dynamic')
    time_logs = db.relationship('WorkTimeLog', backref='vessel', lazy='dynamic')
    
    def __repr__(self):
        return f'<Vessel {self.name} ({self.status})>'
    
    # Status and progress methods
    def get_discharge_progress_percentage(self):
        """Calculate overall discharge progress percentage"""
        if not self.total_discharge_target or self.total_discharge_target == 0:
            return 0.0
        return round((self.total_discharged / self.total_discharge_target) * 100, 2)
    
    def get_zone_progress(self, zone):
        """Get progress for specific zone (BRV, ZEE, SOU)"""
        zone_data = {
            'brv': {'target': self.brv_target, 'completed': self.brv_completed},
            'zee': {'target': self.zee_target, 'completed': self.zee_completed},
            'sou': {'target': self.sou_target, 'completed': self.sou_completed}
        }
        
        zone_info = zone_data.get(zone.lower())
        if not zone_info or not zone_info['target']:
            return {'target': 0, 'completed': 0, 'percentage': 0.0, 'remaining': 0}
        
        target = zone_info['target']
        completed = zone_info['completed']
        percentage = round((completed / target) * 100, 2)
        remaining = max(0, target - completed)
        
        return {
            'target': target,
            'completed': completed,
            'percentage': percentage,
            'remaining': remaining
        }
    
    def get_all_zones_progress(self):
        """Get progress for all zones"""
        return {
            'brv': self.get_zone_progress('brv'),
            'zee': self.get_zone_progress('zee'),
            'sou': self.get_zone_progress('sou'),
            'overall': {
                'target': self.total_discharge_target,
                'completed': self.total_discharged,
                'percentage': self.get_discharge_progress_percentage(),
                'remaining': max(0, (self.total_discharge_target or 0) - self.total_discharged)
            }
        }
    
    def update_discharge_progress(self, zone, units_discharged):
        """Update discharge progress for a specific zone"""
        zone = zone.lower()
        if zone == 'brv':
            self.brv_completed = min(self.brv_completed + units_discharged, self.brv_target or 0)
        elif zone == 'zee':
            self.zee_completed = min(self.zee_completed + units_discharged, self.zee_target or 0)
        elif zone == 'sou':
            self.sou_completed = min(self.sou_completed + units_discharged, self.sou_target or 0)
        
        # Update total
        self.total_discharged = (self.brv_completed + self.zee_completed + self.sou_completed)
        db.session.commit()
    
    def is_discharge_complete(self):
        """Check if all discharge operations are complete"""
        return self.total_discharged >= (self.total_discharge_target or 0)
    
    def get_estimated_completion_time(self):
        """Estimate completion time based on current progress"""
        if not self.total_discharge_target or self.total_discharged == 0:
            return None
        
        if self.atb:  # Operations started
            elapsed_time = datetime.utcnow() - self.atb
            progress_rate = self.total_discharged / elapsed_time.total_seconds()
            remaining_units = self.total_discharge_target - self.total_discharged
            
            if progress_rate > 0:
                estimated_seconds = remaining_units / progress_rate
                return datetime.utcnow() + timedelta(seconds=estimated_seconds)
        
        return self.etc
    
    # Operational status methods
    def arrive_at_port(self):
        """Mark vessel as arrived at port"""
        self.status = 'arrived'
        self.ata = datetime.utcnow()
        db.session.commit()
    
    def berth_vessel(self, berth_id):
        """Berth the vessel at specified berth"""
        self.status = 'berthed'
        self.berth_id = berth_id
        self.atb = datetime.utcnow()
        db.session.commit()
    
    def start_operations(self):
        """Start stevedoring operations"""
        if self.status in ['berthed', 'operations_complete']:
            self.status = 'operations_active'
            db.session.commit()
    
    def complete_operations(self):
        """Mark operations as complete"""
        self.status = 'operations_complete'
        self.atc = datetime.utcnow()
        db.session.commit()
    
    def depart_port(self):
        """Mark vessel as departed"""
        self.status = 'departed'
        self.atd = datetime.utcnow()
        self.berth_id = None
        db.session.commit()
    
    # Resource management methods
    def get_assigned_crew_count(self):
        """Get number of crew members currently assigned"""
        return len(self.current_crew)
    
    def get_active_equipment_count(self):
        """Get number of equipment units currently assigned"""
        return self.equipment_assignments.filter_by(status='active').count()
    
    def get_current_operation(self):
        """Get current active ship operation"""
        return self.operations.filter_by(status='active').first()
    
    def assign_stevedore_team(self, team_id, operation_type):
        """Assign a stevedore team to vessel operation"""
        from .operation_assignment import OperationAssignment
        
        assignment = OperationAssignment(
            vessel_id=self.id,
            team_id=team_id,
            operation_type=operation_type,
            assigned_at=datetime.utcnow(),
            status='active'
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment
    
    def get_active_teams(self):
        """Get all teams currently assigned to vessel"""
        return self.operation_assignments.filter_by(status='active').all()
    
    # Safety and compliance methods
    def check_operational_readiness(self):
        """Check if vessel is ready for operations"""
        checks = {
            'berthed': self.status in ['berthed', 'operations_active'],
            'manifest_received': self.manifest_received,
            'customs_cleared': self.customs_cleared,
            'port_clearance': self.port_clearance,
            'crew_assigned': self.get_assigned_crew_count() > 0,
            'equipment_available': self.get_active_equipment_count() > 0
        }
        
        all_ready = all(checks.values())
        return {'ready': all_ready, 'checks': checks}
    
    def get_safety_requirements(self):
        """Get safety requirements based on cargo type and vessel specs"""
        requirements = []
        
        if self.dangerous_goods_declared:
            requirements.append('Dangerous goods certified personnel required')
            requirements.append('Fire safety equipment standby')
        
        if 'automobiles' in (self.cargo_types_supported or []):
            requirements.append('Auto operations certified lead required')
            requirements.append('Vehicle securing equipment required')
        
        if self.draft and self.draft > 10:  # Deep draft vessel
            requirements.append('Tide monitoring required')
            requirements.append('Draft surveys mandatory')
        
        return requirements
    
    # Financial methods
    def calculate_estimated_costs(self):
        """Calculate estimated operation costs"""
        base_port_dues = Decimal('500.00')  # Base rate
        stevedoring_rate = Decimal('25.00')  # Per unit
        equipment_daily_rate = Decimal('200.00')  # Per equipment per day
        
        # Calculate based on targets
        units = self.total_discharge_target or 0
        estimated_days = 1  # Default to 1 day
        
        if self.atb and self.etc:
            estimated_days = max(1, (self.etc - self.atb).days + 1)
        
        estimated_stevedoring = Decimal(str(units)) * stevedoring_rate
        estimated_equipment = Decimal(str(estimated_days)) * equipment_daily_rate * Decimal('3')  # Assume 3 equipment units
        
        total_estimated = base_port_dues + estimated_stevedoring + estimated_equipment
        
        return {
            'port_dues': base_port_dues,
            'stevedoring': estimated_stevedoring,
            'equipment': estimated_equipment,
            'total': total_estimated
        }
    
    def update_actual_costs(self):
        """Update actual costs based on completed operations"""
        costs = self.calculate_estimated_costs()
        
        # Apply completion factor
        completion_factor = self.get_discharge_progress_percentage() / 100
        
        self.stevedoring_cost = costs['stevedoring'] * Decimal(str(completion_factor))
        self.equipment_cost = costs['equipment']
        self.total_cost = (self.port_dues or Decimal('0')) + self.stevedoring_cost + self.equipment_cost
        
        db.session.commit()
    
    # Documentation methods
    def mark_document_received(self, document_type):
        """Mark specific document as received"""
        if document_type == 'manifest':
            self.manifest_received = True
        elif document_type == 'customs':
            self.customs_cleared = True
        elif document_type == 'port_clearance':
            self.port_clearance = True
        
        db.session.commit()
    
    def get_missing_documents(self):
        """Get list of missing required documents"""
        missing = []
        
        if not self.manifest_received:
            missing.append('Cargo Manifest')
        if not self.customs_cleared:
            missing.append('Customs Clearance')
        if not self.port_clearance:
            missing.append('Port Clearance')
        
        return missing
    
    # Analytics and reporting methods
    def get_operation_statistics(self):
        """Get operational statistics for vessel"""
        total_operations = self.operations.count()
        completed_operations = self.operations.filter_by(status='completed').count()
        
        if self.atb and self.atc:
            total_time = self.atc - self.atb
            hours_in_port = total_time.total_seconds() / 3600
        elif self.atb:
            total_time = datetime.utcnow() - self.atb
            hours_in_port = total_time.total_seconds() / 3600
        else:
            hours_in_port = 0
        
        return {
            'total_operations': total_operations,
            'completed_operations': completed_operations,
            'hours_in_port': round(hours_in_port, 2),
            'units_per_hour': round(self.total_discharged / hours_in_port, 2) if hours_in_port > 0 else 0,
            'completion_percentage': self.get_discharge_progress_percentage(),
            'estimated_completion': self.get_estimated_completion_time()
        }
    
    def get_delay_analysis(self):
        """Analyze delays in vessel operations"""
        delays = {}
        
        if self.eta and self.ata:
            arrival_delay = (self.ata - self.eta).total_seconds() / 3600
            delays['arrival'] = round(arrival_delay, 2)
        
        if self.etb and self.atb:
            berthing_delay = (self.atb - self.etb).total_seconds() / 3600
            delays['berthing'] = round(berthing_delay, 2)
        
        if self.etc and self.atc:
            completion_delay = (self.atc - self.etc).total_seconds() / 3600
            delays['completion'] = round(completion_delay, 2)
        elif self.etc and datetime.utcnow() > self.etc:
            completion_delay = (datetime.utcnow() - self.etc).total_seconds() / 3600
            delays['completion_current'] = round(completion_delay, 2)
        
        return delays
    
    # Utility methods
    def to_dict(self, include_relationships=False):
        """Convert vessel to dictionary for API responses"""
        data = {
            'id': self.id,
            'name': self.name,
            'imo_number': self.imo_number,
            'call_sign': self.call_sign,
            'mmsi_number': self.mmsi_number,
            'vessel_type': self.vessel_type,
            'flag': self.flag,
            'owner': self.owner,
            'operator': self.operator,
            'agent': self.agent,
            
            # Technical specs
            'length': self.length,
            'beam': self.beam,
            'draft': self.draft,
            'max_draft': self.max_draft,
            'gross_tonnage': self.gross_tonnage,
            'net_tonnage': self.net_tonnage,
            'deadweight_tonnage': self.deadweight_tonnage,
            
            # Cargo specs
            'cargo_capacity': self.cargo_capacity,
            'cargo_types_supported': self.cargo_types_supported,
            'has_ramp': self.has_ramp,
            'ramp_capacity': self.ramp_capacity,
            'deck_count': self.deck_count,
            
            # Status
            'status': self.status,
            'berth_id': self.berth_id,
            'current_port': self.current_port,
            'previous_port': self.previous_port,
            'next_port': self.next_port,
            
            # Schedule
            'eta': self.eta.isoformat() if self.eta else None,
            'ata': self.ata.isoformat() if self.ata else None,
            'etb': self.etb.isoformat() if self.etb else None,
            'atb': self.atb.isoformat() if self.atb else None,
            'etc': self.etc.isoformat() if self.etc else None,
            'atc': self.atc.isoformat() if self.atc else None,
            'etd': self.etd.isoformat() if self.etd else None,
            'atd': self.atd.isoformat() if self.atd else None,
            
            # Targets and progress
            'brv_target': self.brv_target,
            'zee_target': self.zee_target,
            'sou_target': self.sou_target,
            'total_discharge_target': self.total_discharge_target,
            'brv_completed': self.brv_completed,
            'zee_completed': self.zee_completed,
            'sou_completed': self.sou_completed,
            'total_discharged': self.total_discharged,
            'discharge_progress_percentage': self.get_discharge_progress_percentage(),
            'zones_progress': self.get_all_zones_progress(),
            
            # Operation details
            'operation_type': self.operation_type,
            'priority_level': self.priority_level,
            'weather_restrictions': self.weather_restrictions,
            'tide_restrictions': self.tide_restrictions,
            
            # Documentation
            'manifest_received': self.manifest_received,
            'customs_cleared': self.customs_cleared,
            'port_clearance': self.port_clearance,
            'dangerous_goods_declared': self.dangerous_goods_declared,
            'hazmat_details': self.hazmat_details,
            'missing_documents': self.get_missing_documents(),
            
            # Financial
            'port_dues': float(self.port_dues) if self.port_dues else None,
            'stevedoring_cost': float(self.stevedoring_cost) if self.stevedoring_cost else None,
            'equipment_cost': float(self.equipment_cost) if self.equipment_cost else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'billing_status': self.billing_status,
            
            # Communication
            'master_name': self.master_name,
            'master_phone': self.master_phone,
            'master_email': self.master_email,
            'chief_officer_name': self.chief_officer_name,
            'ship_phone': self.ship_phone,
            'ship_email': self.ship_email,
            
            # Timestamps
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            
            # Calculated fields
            'crew_count': self.get_assigned_crew_count(),
            'active_equipment_count': self.get_active_equipment_count(),
            'operational_readiness': self.check_operational_readiness(),
            'safety_requirements': self.get_safety_requirements(),
            'operation_statistics': self.get_operation_statistics(),
            'delay_analysis': self.get_delay_analysis()
        }
        
        if include_relationships:
            data.update({
                'berth_name': self.berth.name if self.berth else None,
                'current_operation': self.get_current_operation().to_dict() if self.get_current_operation() else None,
                'active_teams': [team.to_dict() for team in self.get_active_teams()]
            })
        
        return data
    
    # Static methods for queries
    @staticmethod
    def get_active_vessels():
        """Get all vessels currently in port (not departed)"""
        return Vessel.query.filter(
            Vessel.status.in_(['expected', 'arrived', 'berthed', 'operations_active', 'operations_complete'])
        ).order_by(Vessel.eta.asc()).all()
    
    @staticmethod
    def get_vessels_by_status(status):
        """Get vessels by status"""
        return Vessel.query.filter_by(status=status).order_by(Vessel.eta.asc()).all()
    
    @staticmethod
    def get_vessels_by_berth(berth_id):
        """Get vessels at specific berth"""
        return Vessel.query.filter_by(berth_id=berth_id).all()
    
    @staticmethod
    def get_arrivals_today():
        """Get vessels arriving today"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        return Vessel.query.filter(
            Vessel.eta >= today,
            Vessel.eta < tomorrow,
            Vessel.status == 'expected'
        ).order_by(Vessel.eta.asc()).all()
    
    @staticmethod
    def get_departures_today():
        """Get vessels departing today"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        return Vessel.query.filter(
            Vessel.etd >= today,
            Vessel.etd < tomorrow,
            Vessel.status.in_(['operations_complete', 'berthed'])
        ).order_by(Vessel.etd.asc()).all()
    
    @staticmethod
    def get_overdue_vessels():
        """Get vessels that are overdue for completion"""
        return Vessel.query.filter(
            Vessel.etc < datetime.utcnow(),
            Vessel.status.in_(['berthed', 'operations_active'])
        ).all()
    
    @staticmethod
    def get_vessels_needing_attention():
        """Get vessels that need immediate attention"""
        return Vessel.query.filter(
            db.or_(
                # Arrived but not berthed
                db.and_(Vessel.status == 'arrived', 
                       Vessel.ata < datetime.utcnow() - timedelta(hours=2)),
                # Operations overdue
                db.and_(Vessel.etc < datetime.utcnow(),
                       Vessel.status.in_(['berthed', 'operations_active'])),
                # Missing critical documents
                db.and_(Vessel.status.in_(['arrived', 'berthed']),
                       db.or_(Vessel.manifest_received == False,
                             Vessel.customs_cleared == False))
            )
        ).all()
    
    @staticmethod
    def search_vessels(query):
        """Search vessels by name, IMO, or call sign"""
        search_term = f"%{query}%"
        return Vessel.query.filter(
            db.or_(
                Vessel.name.ilike(search_term),
                Vessel.imo_number.ilike(search_term),
                Vessel.call_sign.ilike(search_term)
            )
        ).all()
    
    @staticmethod
    def get_vessel_statistics():
        """Get vessel statistics for dashboard"""
        total_vessels = Vessel.query.count()
        active_vessels = len(Vessel.get_active_vessels())
        berthed_vessels = Vessel.query.filter_by(status='berthed').count()
        operations_active = Vessel.query.filter_by(status='operations_active').count()
        overdue_vessels = len(Vessel.get_overdue_vessels())
        
        return {
            'total': total_vessels,
            'active': active_vessels,
            'berthed': berthed_vessels,
            'operations_active': operations_active,
            'overdue': overdue_vessels
        }

# Create indexes for performance
Index('idx_vessel_status_eta', Vessel.status, Vessel.eta)
Index('idx_vessel_berth_status', Vessel.berth_id, Vessel.status)
Index('idx_vessel_operations_schedule', Vessel.atb, Vessel.etc, Vessel.status)
Index('idx_vessel_imo_call_sign', Vessel.imo_number, Vessel.call_sign)
Index('idx_vessel_progress_tracking', Vessel.total_discharge_target, Vessel.total_discharged, Vessel.status)