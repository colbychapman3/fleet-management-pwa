from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, DateTimeField, SelectField, DateField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Regexp, ValidationError
from datetime import datetime

class MaritimeOperationStep1Form(FlaskForm):
    """Form for Step 1: Operation Details"""
    vessel_id = SelectField('Vessel', coerce=int, validators=[DataRequired()])
    operation_type = SelectField('Operation Type', 
                                choices=[
                                    ('loading', 'Loading'),
                                    ('discharging', 'Discharging'),
                                    ('maintenance', 'Maintenance'),
                                    ('inspection', 'Inspection'),
                                    ('refueling', 'Refueling')
                                ],
                                validators=[DataRequired()])

class MaritimeOperationStep2Form(FlaskForm):
    """Form for Step 2: Cargo Information"""
    cargo_type = StringField('Cargo Type', validators=[DataRequired(), Length(max=100)])
    cargo_weight = FloatField('Cargo Weight (tons)', 
                             validators=[DataRequired(), NumberRange(min=0.1, max=100000)])
    cargo_description = TextAreaField('Cargo Description', 
                                     validators=[Optional(), Length(max=500)])
    cargo_origin = StringField('Origin Port', validators=[DataRequired(), Length(max=100)])
    cargo_destination = StringField('Destination Port', validators=[DataRequired(), Length(max=100)])

class MaritimeOperationStep3Form(FlaskForm):
    """Form for Step 3: Stowage Plan"""
    stowage_location = StringField('Stowage Location', 
                                  validators=[DataRequired(), Length(max=100)])
    stowage_notes = TextAreaField('Stowage Notes', 
                                 validators=[Optional(), Length(max=1000)])
    safety_requirements = TextAreaField('Safety Requirements', 
                                       validators=[Optional(), Length(max=1000)])
    loading_sequence = IntegerField('Loading Sequence', 
                                   validators=[Optional(), NumberRange(min=1, max=100)])

class MaritimeOperationStep4Form(FlaskForm):
    """Form for Step 4: Confirmation Details"""
    estimated_completion = DateTimeField('Estimated Completion', 
                                        validators=[DataRequired()],
                                        format='%Y-%m-%dT%H:%M')
    special_instructions = TextAreaField('Special Instructions', 
                                        validators=[Optional(), Length(max=1000)])
    priority_level = SelectField('Priority Level',
                                choices=[
                                    ('low', 'Low'),
                                    ('normal', 'Normal'),
                                    ('high', 'High'),
                                    ('urgent', 'Urgent')
                                ],
                                default='normal',
                                validators=[DataRequired()])
    assigned_crew = StringField('Assigned Crew', validators=[Optional(), Length(max=200)])

class MaritimeOperationEditForm(FlaskForm):
    """Form for editing existing maritime operations"""
    vessel_id = SelectField('Vessel', coerce=int, validators=[DataRequired()])
    operation_type = SelectField('Operation Type', 
                                choices=[
                                    ('loading', 'Loading'),
                                    ('discharging', 'Discharging'),
                                    ('maintenance', 'Maintenance'),
                                    ('inspection', 'Inspection'),
                                    ('refueling', 'Refueling')
                                ],
                                validators=[DataRequired()])
    status = SelectField('Status',
                        choices=[
                            ('pending', 'Pending'),
                            ('in_progress', 'In Progress'),
                            ('completed', 'Completed'),
                            ('cancelled', 'Cancelled')
                        ],
                        validators=[DataRequired()])
    
    # Cargo Information
    cargo_type = StringField('Cargo Type', validators=[Optional(), Length(max=100)])
    cargo_weight = FloatField('Cargo Weight (tons)', 
                             validators=[Optional(), NumberRange(min=0.1, max=100000)])
    cargo_description = TextAreaField('Cargo Description', 
                                     validators=[Optional(), Length(max=500)])
    cargo_origin = StringField('Origin Port', validators=[Optional(), Length(max=100)])
    cargo_destination = StringField('Destination Port', validators=[Optional(), Length(max=100)])
    
    # Stowage Plan
    stowage_location = StringField('Stowage Location', 
                                  validators=[Optional(), Length(max=100)])
    stowage_notes = TextAreaField('Stowage Notes', 
                                 validators=[Optional(), Length(max=1000)])
    safety_requirements = TextAreaField('Safety Requirements', 
                                       validators=[Optional(), Length(max=1000)])
    loading_sequence = IntegerField('Loading Sequence', 
                                   validators=[Optional(), NumberRange(min=1, max=100)])
    
    # Confirmation Details
    estimated_completion = DateTimeField('Estimated Completion', 
                                        validators=[Optional()],
                                        format='%Y-%m-%dT%H:%M')
    special_instructions = TextAreaField('Special Instructions', 
                                        validators=[Optional(), Length(max=1000)])
    priority_level = SelectField('Priority Level',
                                choices=[
                                    ('low', 'Low'),
                                    ('normal', 'Normal'),
                                    ('high', 'High'),
                                    ('urgent', 'Urgent')
                                ],
                                default='normal',
                                validators=[DataRequired()])
    assigned_crew = StringField('Assigned Crew', validators=[Optional(), Length(max=200)])

# Enhanced comprehensive form for Jules' advanced features
class MaritimeOperationWizardForm(FlaskForm):
    """Comprehensive form for the enhanced maritime operation wizard"""
    
    # Vessel Details
    vessel_name = StringField('Vessel Name', validators=[DataRequired(), Length(max=200)])
    vessel_type = StringField('Vessel Type', validators=[DataRequired(), Length(max=100)])
    shipping_line = StringField('Shipping Line', validators=[DataRequired(), Length(max=100)])
    port = StringField('Port', validators=[DataRequired(), Length(max=100)])
    berth = StringField('Berth', validators=[Optional(), Length(max=50)])
    
    # Operation Details
    operation_type = SelectField('Operation Type',
                                choices=[
                                    ('loading', 'Loading'),
                                    ('discharging', 'Discharging'),
                                    ('maintenance', 'Maintenance'),
                                    ('inspection', 'Inspection'),
                                    ('refueling', 'Refueling')
                                ],
                                validators=[DataRequired()])
    operation_date = DateField('Operation Date', validators=[DataRequired()])
    company = StringField('Company', validators=[Optional(), Length(max=100)])
    
    # Team Assignments
    operation_manager = StringField('Operation Manager', validators=[Optional(), Length(max=100)])
    auto_ops_lead = StringField('Auto Ops Lead', validators=[Optional(), Length(max=100)])
    auto_ops_assistant = StringField('Auto Ops Assistant', validators=[Optional(), Length(max=100)])
    heavy_ops_lead = StringField('Heavy Ops Lead', validators=[Optional(), Length(max=100)])
    heavy_ops_assistant = StringField('Heavy Ops Assistant', validators=[Optional(), Length(max=100)])
    
    # Cargo and Vehicle Breakdown
    total_vehicles = IntegerField('Total Vehicles', validators=[Optional(), NumberRange(min=0)])
    total_automobiles_discharge = IntegerField('Total Automobiles Discharge', validators=[Optional(), NumberRange(min=0)])
    heavy_equipment_discharge = IntegerField('Heavy Equipment Discharge', validators=[Optional(), NumberRange(min=0)])
    total_electric_vehicles = IntegerField('Total Electric Vehicles', validators=[Optional(), NumberRange(min=0)])
    total_static_cargo = IntegerField('Total Static Cargo', validators=[Optional(), NumberRange(min=0)])
    
    # Terminal Targets
    brv_target = IntegerField('BRV Target', validators=[Optional(), NumberRange(min=0)])
    zee_target = IntegerField('ZEE Target', validators=[Optional(), NumberRange(min=0)])
    sou_target = IntegerField('SOU Target', validators=[Optional(), NumberRange(min=0)])
    expected_rate = IntegerField('Expected Rate', validators=[Optional(), NumberRange(min=0)])
    total_drivers = IntegerField('Total Drivers', validators=[Optional(), NumberRange(min=0)])
    
    # Shift and Timing
    shift_start = StringField('Shift Start', validators=[Optional(), Length(max=20)])
    shift_end = StringField('Shift End', validators=[Optional(), Length(max=20)])
    break_duration = IntegerField('Break Duration (minutes)', validators=[Optional(), NumberRange(min=0, max=480)])
    target_completion = StringField('Target Completion', validators=[Optional(), Length(max=20)])
    start_time = StringField('Start Time', validators=[Optional(), Length(max=20)])
    estimated_completion = StringField('Estimated Completion', validators=[Optional(), Length(max=20)])
    
    # Equipment Allocation
    tico_vans = IntegerField('TICO Vans', validators=[Optional(), NumberRange(min=0)])
    tico_station_wagons = IntegerField('TICO Station Wagons', validators=[Optional(), NumberRange(min=0)])
    
    # Progress Tracking
    progress = IntegerField('Progress %', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Advanced Maritime Fields
    imo_number = StringField('IMO Number', validators=[Optional(), Length(max=20), Regexp(r'^IMO\d{7}$', message='IMO number must be in format IMO1234567')])
    mmsi = StringField('MMSI', validators=[Optional(), Length(max=15), Regexp(r'^\d{9}$', message='MMSI must be 9 digits')])
    call_sign = StringField('Call Sign', validators=[Optional(), Length(max=20)])
    flag_state = StringField('Flag State', validators=[Optional(), Length(max=50)])
    
    # ETA field
    eta = DateTimeField('ETA', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    
    def validate_imo_number(self, field):
        """Custom validation for IMO number"""
        if field.data and not field.data.startswith('IMO'):
            field.data = f'IMO{field.data}'
    
    def validate_mmsi(self, field):
        """Custom validation for MMSI"""
        if field.data and len(field.data) != 9:
            raise ValidationError('MMSI must be exactly 9 digits')

class MaritimeOperationAPIForm(FlaskForm):
    """Form for API-based maritime operations (simplified validation)"""
    
    # Required fields
    vessel_name = StringField('Vessel Name', validators=[DataRequired()])
    operation_type = StringField('Operation Type', validators=[DataRequired()])
    
    # Optional fields with minimal validation for API flexibility
    vessel_type = StringField('Vessel Type', validators=[Optional()])
    shipping_line = StringField('Shipping Line', validators=[Optional()])
    port = StringField('Port', validators=[Optional()])
    berth = StringField('Berth', validators=[Optional()])
    operation_date = DateField('Operation Date', validators=[Optional()])
    
    # Team fields
    operation_manager = StringField('Operation Manager', validators=[Optional()])
    auto_ops_lead = StringField('Auto Ops Lead', validators=[Optional()])
    auto_ops_assistant = StringField('Auto Ops Assistant', validators=[Optional()])
    heavy_ops_lead = StringField('Heavy Ops Lead', validators=[Optional()])
    heavy_ops_assistant = StringField('Heavy Ops Assistant', validators=[Optional()])
    
    # Cargo fields
    total_vehicles = IntegerField('Total Vehicles', validators=[Optional()])
    total_automobiles_discharge = IntegerField('Total Automobiles Discharge', validators=[Optional()])
    heavy_equipment_discharge = IntegerField('Heavy Equipment Discharge', validators=[Optional()])
    total_electric_vehicles = IntegerField('Total Electric Vehicles', validators=[Optional()])
    total_static_cargo = IntegerField('Total Static Cargo', validators=[Optional()])
    
    # Target fields
    brv_target = IntegerField('BRV Target', validators=[Optional()])
    zee_target = IntegerField('ZEE Target', validators=[Optional()])
    sou_target = IntegerField('SOU Target', validators=[Optional()])
    expected_rate = IntegerField('Expected Rate', validators=[Optional()])
    total_drivers = IntegerField('Total Drivers', validators=[Optional()])
    
    # Timing fields
    shift_start = StringField('Shift Start', validators=[Optional()])
    shift_end = StringField('Shift End', validators=[Optional()])
    break_duration = IntegerField('Break Duration', validators=[Optional()])
    target_completion = StringField('Target Completion', validators=[Optional()])
    start_time = StringField('Start Time', validators=[Optional()])
    estimated_completion = StringField('Estimated Completion', validators=[Optional()])
    
    # Equipment fields
    tico_vans = IntegerField('TICO Vans', validators=[Optional()])
    tico_station_wagons = IntegerField('TICO Station Wagons', validators=[Optional()])
    
    # Progress
    progress = IntegerField('Progress', validators=[Optional()])
    
    # Maritime fields
    imo_number = StringField('IMO Number', validators=[Optional()])
    mmsi = StringField('MMSI', validators=[Optional()])
    call_sign = StringField('Call Sign', validators=[Optional()])
    flag_state = StringField('Flag State', validators=[Optional()])
    
    # ETA
    eta = DateTimeField('ETA', validators=[Optional()])

