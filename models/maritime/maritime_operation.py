from app import db
from datetime import datetime
import json
from sqlalchemy.ext.hybrid import hybrid_property

class MaritimeOperation(db.Model):
    """Enhanced Maritime Operation model for stevedoring operations"""
    __tablename__ = 'maritime_operations'

    # Core identification
    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False)
    
    # Basic operation details (backward compatible)
    operation_type = db.Column(db.String(100), nullable=False)  # 'loading', 'discharging'
    status = db.Column(db.String(50), default='pending')  # 'pending', 'in_progress', 'completed'
    
    # Enhanced vessel and operation details (from Manus' Ship model)
    vessel_name = db.Column(db.String(200))
    vessel_type = db.Column(db.String(100))
    shipping_line = db.Column(db.String(100))
    port = db.Column(db.String(100))
    operation_date = db.Column(db.Date)
    company = db.Column(db.String(100))
    berth = db.Column(db.String(50))
    
    # Team assignments
    operation_manager = db.Column(db.String(100))
    auto_ops_lead = db.Column(db.String(100))
    auto_ops_assistant = db.Column(db.String(100))
    heavy_ops_lead = db.Column(db.String(100))
    heavy_ops_assistant = db.Column(db.String(100))
    
    # Cargo and vehicle breakdown
    total_vehicles = db.Column(db.Integer, default=0)
    total_automobiles_discharge = db.Column(db.Integer, default=0)
    heavy_equipment_discharge = db.Column(db.Integer, default=0)
    total_electric_vehicles = db.Column(db.Integer, default=0)
    total_static_cargo = db.Column(db.Integer, default=0)
    
    # Terminal targets and planning
    brv_target = db.Column(db.Integer, default=0)
    zee_target = db.Column(db.Integer, default=0)
    sou_target = db.Column(db.Integer, default=0)
    expected_rate = db.Column(db.Integer, default=0)
    total_drivers = db.Column(db.Integer, default=0)
    
    # Shift and timing
    shift_start = db.Column(db.String(20))
    shift_end = db.Column(db.String(20))
    break_duration = db.Column(db.Integer, default=30)  # minutes
    target_completion = db.Column(db.String(20))
    start_time = db.Column(db.String(20))
    estimated_completion = db.Column(db.String(20))
    
    # Equipment allocation
    tico_vans = db.Column(db.Integer, default=0)
    tico_station_wagons = db.Column(db.Integer, default=0)
    
    # Progress tracking
    progress = db.Column(db.Integer, default=0)  # percentage
    
    # JSON fields for complex data (from Manus' design)
    deck_data = db.Column(db.Text)  # JSON string for deck-specific cargo data
    turnaround_data = db.Column(db.Text)  # JSON string for turnaround metrics
    inventory_data = db.Column(db.Text)  # JSON string for inventory tracking
    hourly_quantity_data = db.Column(db.Text)  # JSON string for hourly progress
    
    # Advanced maritime fields
    imo_number = db.Column(db.String(20))
    mmsi = db.Column(db.String(15))
    call_sign = db.Column(db.String(20))
    flag_state = db.Column(db.String(50))
    
    # Enhanced maritime operation fields (from forms)
    cargo_type = db.Column(db.String(100))
    cargo_weight = db.Column(db.Float)
    cargo_description = db.Column(db.Text)
    cargo_origin = db.Column(db.String(100))
    cargo_destination = db.Column(db.String(100))
    stowage_location = db.Column(db.String(100))
    stowage_notes = db.Column(db.Text)
    safety_requirements = db.Column(db.Text)
    loading_sequence = db.Column(db.Integer)
    special_instructions = db.Column(db.Text)
    priority_level = db.Column(db.String(20), default='normal')
    assigned_crew = db.Column(db.String(200))
    eta = db.Column(db.DateTime)
    
    # Timestamps (backward compatible)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vessel = db.relationship('Vessel', backref='maritime_operations')
    
    def __repr__(self):
        return f'<MaritimeOperation {self.id}: {self.vessel_name}>'
    
    # JSON field helpers (from Manus' design)
    @hybrid_property
    def deck_info(self):
        """Get deck data as Python object"""
        if self.deck_data:
            try:
                return json.loads(self.deck_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    @deck_info.setter
    def deck_info(self, value):
        """Set deck data from Python object"""
        if value is not None:
            self.deck_data = json.dumps(value)
        else:
            self.deck_data = None
    
    @hybrid_property
    def turnaround_info(self):
        """Get turnaround data as Python object"""
        if self.turnaround_data:
            try:
                return json.loads(self.turnaround_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    @turnaround_info.setter
    def turnaround_info(self, value):
        """Set turnaround data from Python object"""
        if value is not None:
            self.turnaround_data = json.dumps(value)
        else:
            self.turnaround_data = None
    
    @hybrid_property
    def inventory_info(self):
        """Get inventory data as Python object"""
        if self.inventory_data:
            try:
                return json.loads(self.inventory_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    @inventory_info.setter
    def inventory_info(self, value):
        """Set inventory data from Python object"""
        if value is not None:
            self.inventory_data = json.dumps(value)
        else:
            self.inventory_data = None
    
    @hybrid_property
    def hourly_quantities(self):
        """Get hourly quantity data as Python object"""
        if self.hourly_quantity_data:
            try:
                return json.loads(self.hourly_quantity_data)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    @hourly_quantities.setter
    def hourly_quantities(self, value):
        """Set hourly quantity data from Python object"""
        if value is not None:
            self.hourly_quantity_data = json.dumps(value)
        else:
            self.hourly_quantity_data = None
    
    def get_total_cargo(self):
        """Calculate total cargo count"""
        return (self.total_vehicles or 0) + (self.total_static_cargo or 0)
    
    def get_completion_percentage(self):
        """Get operation completion percentage"""
        return self.progress or 0
    
    def get_team_summary(self):
        """Get team assignment summary"""
        return {
            'operation_manager': self.operation_manager,
            'auto_ops': {
                'lead': self.auto_ops_lead,
                'assistant': self.auto_ops_assistant
            },
            'heavy_ops': {
                'lead': self.heavy_ops_lead,
                'assistant': self.heavy_ops_assistant
            }
        }
    
    def get_cargo_breakdown(self):
        """Get cargo breakdown summary"""
        return {
            'vehicles': {
                'total': self.total_vehicles or 0,
                'automobiles': self.total_automobiles_discharge or 0,
                'heavy_equipment': self.heavy_equipment_discharge or 0,
                'electric': self.total_electric_vehicles or 0
            },
            'static_cargo': self.total_static_cargo or 0,
            'equipment': {
                'tico_vans': self.tico_vans or 0,
                'tico_station_wagons': self.tico_station_wagons or 0
            }
        }
    
    def get_targets_summary(self):
        """Get terminal targets summary"""
        return {
            'brv': self.brv_target or 0,
            'zee': self.zee_target or 0,
            'sou': self.sou_target or 0,
            'expected_rate': self.expected_rate or 0,
            'total_drivers': self.total_drivers or 0
        }
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'vessel_id': self.vessel_id,
            'vessel_name': self.vessel_name,
            'vessel_type': self.vessel_type,
            'shipping_line': self.shipping_line,
            'port': self.port,
            'operation_type': self.operation_type,
            'operation_date': self.operation_date.isoformat() if self.operation_date else None,
            'status': self.status,
            'berth': self.berth,
            'progress': self.progress,
            'team': self.get_team_summary(),
            'cargo': self.get_cargo_breakdown(),
            'targets': self.get_targets_summary(),
            # Enhanced fields
            'cargo_type': self.cargo_type,
            'cargo_weight': self.cargo_weight,
            'cargo_description': self.cargo_description,
            'cargo_origin': self.cargo_origin,
            'cargo_destination': self.cargo_destination,
            'stowage_location': self.stowage_location,
            'stowage_notes': self.stowage_notes,
            'safety_requirements': self.safety_requirements,
            'loading_sequence': self.loading_sequence,
            'special_instructions': self.special_instructions,
            'priority_level': self.priority_level,
            'assigned_crew': self.assigned_crew,
            'eta': self.eta.isoformat() if self.eta else None,
            'estimated_completion': self.estimated_completion,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create_from_wizard_data(form_data):
        """Create maritime operation from wizard form data"""
        operation = MaritimeOperation()
        
        # Map form fields to model fields
        field_mapping = {
            'vesselName': 'vessel_name',
            'vesselType': 'vessel_type',
            'shippingLine': 'shipping_line',
            'port': 'port',
            'operationType': 'operation_type',
            'berth': 'berth',
            'operationManager': 'operation_manager',
            'autoOpsLead': 'auto_ops_lead',
            'autoOpsAssistant': 'auto_ops_assistant',
            'heavyOpsLead': 'heavy_ops_lead',
            'heavyOpsAssistant': 'heavy_ops_assistant',
            'imoNumber': 'imo_number',
            'mmsi': 'mmsi',
            'callSign': 'call_sign',
            'flagState': 'flag_state'
        }
        
        for form_field, model_field in field_mapping.items():
            if form_field in form_data:
                setattr(operation, model_field, form_data[form_field])
        
        return operation
