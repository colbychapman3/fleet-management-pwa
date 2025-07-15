from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, DateTimeField, SelectField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
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

