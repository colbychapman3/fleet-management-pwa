"""
CargoDischarge model for tracking automobile/container discharge with zone management
"""

from datetime import datetime
from app import db


class CargoDischarge(db.Model):
    """Cargo discharge model for tracking automobile and container operations with zones"""
    
    __tablename__ = 'cargo_discharges'
    
    id = db.Column(db.Integer, primary_key=True)
    discharge_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    ship_operation_id = db.Column(db.Integer, db.ForeignKey('ship_operations.id'), nullable=False, index=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False, index=True)
    
    # Cargo Information
    cargo_type = db.Column(db.String(50), nullable=False, index=True)  # automobiles, containers, bulk, general_cargo
    total_units = db.Column(db.Integer, nullable=False)
    discharged_units = db.Column(db.Integer, default=0)
    damaged_units = db.Column(db.Integer, default=0)
    
    # Zone Management
    discharge_zone = db.Column(db.String(10), nullable=False, index=True)  # BRV, ZEE, SOU
    storage_zone = db.Column(db.String(10), index=True)  # Final storage zone
    temporary_storage = db.Column(db.Boolean, default=False)
    
    # For Automobiles
    auto_makes = db.Column(db.JSON)  # List of automobile makes/models
    auto_colors = db.Column(db.JSON)  # Color distribution
    auto_fuel_types = db.Column(db.JSON)  # Petrol, diesel, electric, hybrid
    auto_drive_types = db.Column(db.JSON)  # LHD, RHD
    auto_damage_report = db.Column(db.JSON)  # Damage tracking per unit
    
    # For Containers
    container_sizes = db.Column(db.JSON)  # 20ft, 40ft, 45ft distribution
    container_types = db.Column(db.JSON)  # Standard, high cube, refrigerated, open top
    container_numbers = db.Column(db.JSON)  # List of container numbers
    container_seal_numbers = db.Column(db.JSON)  # Seal verification
    container_weights = db.Column(db.JSON)  # Weight per container
    hazardous_cargo = db.Column(db.Boolean, default=False)
    refrigerated_cargo = db.Column(db.Boolean, default=False)
    
    # Operation Details
    berth_number = db.Column(db.String(20), nullable=False)
    discharge_start_time = db.Column(db.DateTime)
    discharge_end_time = db.Column(db.DateTime)
    estimated_completion = db.Column(db.DateTime)
    
    # Personnel and Equipment
    stevedore_team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'))
    equipment_assigned = db.Column(db.JSON)  # List of equipment IDs
    drivers_assigned = db.Column(db.JSON)  # List of driver user IDs
    
    # Quality Control
    inspection_required = db.Column(db.Boolean, default=True)
    inspection_completed = db.Column(db.Boolean, default=False)
    customs_inspection = db.Column(db.Boolean, default=False)
    quality_control_notes = db.Column(db.Text)
    
    # Documentation
    bill_of_lading = db.Column(db.String(100))
    manifest_reference = db.Column(db.String(100))
    customs_declaration = db.Column(db.String(100))
    discharge_report = db.Column(db.JSON)  # Detailed discharge report
    
    # Status and Priority
    status = db.Column(db.String(20), default='pending', index=True)  # pending, in_progress, completed, paused, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    
    # Weather and Environmental
    weather_conditions = db.Column(db.JSON)  # Weather during operations
    tide_conditions = db.Column(db.String(50))
    operation_suspended = db.Column(db.Boolean, default=False)
    suspension_reason = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ship_operation = db.relationship('ShipOperation', backref='cargo_discharges', lazy=True)
    vessel = db.relationship('Vessel', backref='cargo_discharges', lazy=True)
    stevedore_team = db.relationship('StevedoreTeam', backref='cargo_discharges', lazy=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_cargo_discharge_vessel_status', 'vessel_id', 'status'),
        db.Index('idx_cargo_discharge_zone_type', 'discharge_zone', 'cargo_type'),
        db.Index('idx_cargo_discharge_berth', 'berth_number'),
        db.Index('idx_cargo_discharge_datetime', 'discharge_start_time'),
    )
    
    def __repr__(self):
        return f'<CargoDischarge {self.discharge_id}>'
    
    def get_completion_percentage(self):
        """Calculate discharge completion percentage"""
        if self.total_units == 0:
            return 0
        return (self.discharged_units / self.total_units) * 100
    
    def get_damage_percentage(self):
        """Calculate damage percentage"""
        if self.discharged_units == 0:
            return 0
        return (self.damaged_units / self.discharged_units) * 100
    
    def get_remaining_units(self):
        """Get remaining units to discharge"""
        return self.total_units - self.discharged_units
    
    def is_automobile_cargo(self):
        """Check if cargo is automobiles"""
        return self.cargo_type == 'automobiles'
    
    def is_container_cargo(self):
        """Check if cargo is containers"""
        return self.cargo_type == 'containers'
    
    def requires_special_handling(self):
        """Check if cargo requires special handling"""
        if self.is_container_cargo():
            return self.hazardous_cargo or self.refrigerated_cargo
        return False
    
    def update_discharge_progress(self, units_discharged, damaged_units=0):
        """Update discharge progress"""
        self.discharged_units = min(units_discharged, self.total_units)
        self.damaged_units += damaged_units
        
        # Auto-complete if all units discharged
        if self.discharged_units >= self.total_units:
            self.status = 'completed'
            self.discharge_end_time = datetime.utcnow()
        elif self.discharged_units > 0 and self.status == 'pending':
            self.status = 'in_progress'
            if not self.discharge_start_time:
                self.discharge_start_time = datetime.utcnow()
        
        self.updated_at = datetime.utcnow()
    
    def add_automobile_details(self, auto_data):
        """Add automobile-specific details"""
        if not self.is_automobile_cargo():
            return False
        
        self.auto_makes = auto_data.get('makes', [])
        self.auto_colors = auto_data.get('colors', [])
        self.auto_fuel_types = auto_data.get('fuel_types', [])
        self.auto_drive_types = auto_data.get('drive_types', [])
        self.auto_damage_report = auto_data.get('damage_report', [])
        
        self.updated_at = datetime.utcnow()
        return True
    
    def add_container_details(self, container_data):
        """Add container-specific details"""
        if not self.is_container_cargo():
            return False
        
        self.container_sizes = container_data.get('sizes', [])
        self.container_types = container_data.get('types', [])
        self.container_numbers = container_data.get('numbers', [])
        self.container_seal_numbers = container_data.get('seal_numbers', [])
        self.container_weights = container_data.get('weights', [])
        self.hazardous_cargo = container_data.get('hazardous', False)
        self.refrigerated_cargo = container_data.get('refrigerated', False)
        
        self.updated_at = datetime.utcnow()
        return True
    
    def assign_to_zone(self, zone, is_temporary=False):
        """Assign cargo to storage zone"""
        valid_zones = ['BRV', 'ZEE', 'SOU']
        if zone not in valid_zones:
            return False
        
        if is_temporary:
            self.discharge_zone = zone
            self.temporary_storage = True
        else:
            self.storage_zone = zone
            self.temporary_storage = False
        
        self.updated_at = datetime.utcnow()
        return True
    
    def complete_inspection(self, inspection_notes=None):
        """Mark inspection as completed"""
        self.inspection_completed = True
        if inspection_notes:
            self.quality_control_notes = inspection_notes
        self.updated_at = datetime.utcnow()
    
    def suspend_operation(self, reason):
        """Suspend discharge operation"""
        self.operation_suspended = True
        self.suspension_reason = reason
        if self.status == 'in_progress':
            self.status = 'paused'
        self.updated_at = datetime.utcnow()
    
    def resume_operation(self):
        """Resume discharge operation"""
        self.operation_suspended = False
        self.suspension_reason = None
        if self.status == 'paused':
            self.status = 'in_progress'
        self.updated_at = datetime.utcnow()
    
    def get_estimated_time_remaining(self):
        """Estimate time remaining based on current progress"""
        if not self.discharge_start_time or self.discharged_units == 0:
            return None
        
        elapsed_time = datetime.utcnow() - self.discharge_start_time
        rate_per_hour = self.discharged_units / (elapsed_time.total_seconds() / 3600)
        
        if rate_per_hour > 0:
            remaining_units = self.get_remaining_units()
            remaining_hours = remaining_units / rate_per_hour
            return remaining_hours
        
        return None
    
    def get_zone_capacity_info(self):
        """Get information about zone capacity and utilization"""
        # This would typically query other discharges in the same zone
        # For now, returning placeholder structure
        return {
            'zone': self.storage_zone or self.discharge_zone,
            'current_utilization': 0,  # Would be calculated from other operations
            'available_capacity': 100,  # Would be fetched from zone configuration
            'recommended_zone': self.discharge_zone  # Could suggest optimal zone
        }
    
    def to_dict(self):
        """Convert cargo discharge to dictionary for API responses"""
        return {
            'id': self.id,
            'discharge_id': self.discharge_id,
            'ship_operation_id': self.ship_operation_id,
            'vessel_id': self.vessel_id,
            'cargo_type': self.cargo_type,
            'total_units': self.total_units,
            'discharged_units': self.discharged_units,
            'damaged_units': self.damaged_units,
            'completion_percentage': self.get_completion_percentage(),
            'damage_percentage': self.get_damage_percentage(),
            'remaining_units': self.get_remaining_units(),
            
            # Zone information
            'discharge_zone': self.discharge_zone,
            'storage_zone': self.storage_zone,
            'temporary_storage': self.temporary_storage,
            
            # Automobile data
            'auto_makes': self.auto_makes,
            'auto_colors': self.auto_colors,
            'auto_fuel_types': self.auto_fuel_types,
            'auto_drive_types': self.auto_drive_types,
            'auto_damage_report': self.auto_damage_report,
            
            # Container data
            'container_sizes': self.container_sizes,
            'container_types': self.container_types,
            'container_numbers': self.container_numbers,
            'container_seal_numbers': self.container_seal_numbers,
            'container_weights': self.container_weights,
            'hazardous_cargo': self.hazardous_cargo,
            'refrigerated_cargo': self.refrigerated_cargo,
            
            # Operation details
            'berth_number': self.berth_number,
            'discharge_start_time': self.discharge_start_time.isoformat() if self.discharge_start_time else None,
            'discharge_end_time': self.discharge_end_time.isoformat() if self.discharge_end_time else None,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'estimated_time_remaining': self.get_estimated_time_remaining(),
            
            # Personnel and equipment
            'stevedore_team_id': self.stevedore_team_id,
            'equipment_assigned': self.equipment_assigned,
            'drivers_assigned': self.drivers_assigned,
            
            # Quality control
            'inspection_required': self.inspection_required,
            'inspection_completed': self.inspection_completed,
            'customs_inspection': self.customs_inspection,
            'quality_control_notes': self.quality_control_notes,
            
            # Documentation
            'bill_of_lading': self.bill_of_lading,
            'manifest_reference': self.manifest_reference,
            'customs_declaration': self.customs_declaration,
            'discharge_report': self.discharge_report,
            
            # Status and priority
            'status': self.status,
            'priority': self.priority,
            
            # Environmental
            'weather_conditions': self.weather_conditions,
            'tide_conditions': self.tide_conditions,
            'operation_suspended': self.operation_suspended,
            'suspension_reason': self.suspension_reason,
            
            # Timestamps
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            
            # Computed properties
            'is_automobile_cargo': self.is_automobile_cargo(),
            'is_container_cargo': self.is_container_cargo(),
            'requires_special_handling': self.requires_special_handling(),
            'zone_capacity_info': self.get_zone_capacity_info(),
            
            # Related data
            'vessel_name': self.vessel.name if self.vessel else None,
            'operation_id': self.ship_operation.operation_id if self.ship_operation else None,
            'stevedore_team_name': self.stevedore_team.team_name if self.stevedore_team else None
        }
    
    @staticmethod
    def get_active_discharges():
        """Get all active cargo discharges"""
        return CargoDischarge.query.filter(
            CargoDischarge.status.in_(['pending', 'in_progress', 'paused'])
        ).order_by(CargoDischarge.priority.desc(), CargoDischarge.created_at.asc()).all()
    
    @staticmethod
    def get_discharges_by_zone(zone):
        """Get cargo discharges for a specific zone"""
        return CargoDischarge.query.filter(
            db.or_(
                CargoDischarge.discharge_zone == zone,
                CargoDischarge.storage_zone == zone
            )
        ).order_by(CargoDischarge.created_at.desc()).all()
    
    @staticmethod
    def get_discharges_by_cargo_type(cargo_type):
        """Get discharges by cargo type"""
        return CargoDischarge.query.filter_by(cargo_type=cargo_type).order_by(
            CargoDischarge.created_at.desc()
        ).all()
    
    @staticmethod
    def get_discharges_by_vessel(vessel_id):
        """Get cargo discharges for a specific vessel"""
        return CargoDischarge.query.filter_by(vessel_id=vessel_id).order_by(
            CargoDischarge.created_at.desc()
        ).all()
    
    @staticmethod
    def get_discharges_by_berth(berth_number):
        """Get cargo discharges for a specific berth"""
        return CargoDischarge.query.filter_by(berth_number=berth_number).order_by(
            CargoDischarge.created_at.desc()
        ).all()
    
    @staticmethod
    def get_suspended_discharges():
        """Get all suspended discharge operations"""
        return CargoDischarge.query.filter_by(operation_suspended=True).all()
    
    @staticmethod
    def get_pending_inspections():
        """Get discharges pending inspection"""
        return CargoDischarge.query.filter(
            CargoDischarge.inspection_required == True,
            CargoDischarge.inspection_completed == False,
            CargoDischarge.status.in_(['in_progress', 'completed'])
        ).all()
    
    @staticmethod
    def get_zone_statistics(zone):
        """Get statistics for a specific zone"""
        discharges = CargoDischarge.get_discharges_by_zone(zone)
        
        total_discharges = len(discharges)
        active_discharges = len([d for d in discharges if d.status in ['pending', 'in_progress']])
        completed_discharges = len([d for d in discharges if d.status == 'completed'])
        
        total_units = sum([d.total_units for d in discharges])
        discharged_units = sum([d.discharged_units for d in discharges])
        damaged_units = sum([d.damaged_units for d in discharges])
        
        return {
            'zone': zone,
            'total_discharges': total_discharges,
            'active_discharges': active_discharges,
            'completed_discharges': completed_discharges,
            'total_units': total_units,
            'discharged_units': discharged_units,
            'damaged_units': damaged_units,
            'damage_rate': (damaged_units / discharged_units * 100) if discharged_units > 0 else 0,
            'completion_rate': (discharged_units / total_units * 100) if total_units > 0 else 0
        }
    
    @staticmethod
    def get_cargo_type_statistics():
        """Get statistics by cargo type"""
        automobile_discharges = CargoDischarge.get_discharges_by_cargo_type('automobiles')
        container_discharges = CargoDischarge.get_discharges_by_cargo_type('containers')
        
        return {
            'automobiles': {
                'count': len(automobile_discharges),
                'total_units': sum([d.total_units for d in automobile_discharges]),
                'discharged_units': sum([d.discharged_units for d in automobile_discharges])
            },
            'containers': {
                'count': len(container_discharges),
                'total_units': sum([d.total_units for d in container_discharges]),
                'discharged_units': sum([d.discharged_units for d in container_discharges])
            }
        }
    
    @staticmethod
    def generate_discharge_id(vessel_name, cargo_type):
        """Generate unique discharge ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        vessel_short = ''.join([c for c in vessel_name.upper() if c.isalpha()])[:6]
        cargo_short = cargo_type.upper()[:4]
        return f"DIS-{vessel_short}-{cargo_short}-{timestamp}"