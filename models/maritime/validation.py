"""
Maritime-specific field validation for stevedoring operations
"""

import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

class MaritimeValidator:
    """Maritime field validation utilities"""
    
    # Maritime patterns
    IMO_PATTERN = re.compile(r'^IMO\s?\d{7}$', re.IGNORECASE)
    MMSI_PATTERN = re.compile(r'^\d{9}$')
    CALL_SIGN_PATTERN = re.compile(r'^[A-Z0-9]{4,7}$', re.IGNORECASE)
    
    # Valid options
    VESSEL_TYPES = [
        'container', 'roro', 'auto-carrier', 'general-cargo', 
        'heavy-lift', 'tanker', 'bulk-carrier', 'ferry', 'other'
    ]
    
    SHIPPING_LINES = [
        'K-Line', 'MOL', 'Glovis', 'Grimaldi', 'MSC', 'Maersk',
        'CMA-CGM', 'COSCO', 'Evergreen', 'OOCL', 'Yang-Ming', 'Hapag-Lloyd'
    ]
    
    OPERATION_TYPES = ['loading', 'discharging', 'transshipment', 'maintenance']
    
    STATUS_OPTIONS = ['pending', 'in_progress', 'completed', 'cancelled', 'delayed']
    
    BERTH_OPTIONS = ['berth-1', 'berth-2', 'berth-3', 'berth-4', 'berth-5']
    
    FLAG_STATES = [
        'Liberia', 'Panama', 'Marshall Islands', 'Hong Kong', 'Singapore',
        'Bahamas', 'Malta', 'Cyprus', 'Norway', 'United Kingdom'
    ]
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that all required fields are present and non-empty"""
        errors = []
        
        for field in required_fields:
            if field not in data or not data[field] or str(data[field]).strip() == '':
                errors.append(f"{field} is required")
        
        return errors
    
    @staticmethod
    def validate_vessel_name(vessel_name: str) -> Optional[str]:
        """Validate vessel name"""
        if not vessel_name or not vessel_name.strip():
            return "Vessel name is required"
        
        if len(vessel_name.strip()) < 2:
            return "Vessel name must be at least 2 characters long"
        
        if len(vessel_name.strip()) > 200:
            return "Vessel name must be less than 200 characters"
        
        return None
    
    @staticmethod
    def validate_vessel_type(vessel_type: str) -> Optional[str]:
        """Validate vessel type"""
        if not vessel_type:
            return "Vessel type is required"
        
        if vessel_type not in MaritimeValidator.VESSEL_TYPES:
            return f"Invalid vessel type. Must be one of: {', '.join(MaritimeValidator.VESSEL_TYPES)}"
        
        return None
    
    @staticmethod
    def validate_shipping_line(shipping_line: str) -> Optional[str]:
        """Validate shipping line"""
        if not shipping_line:
            return "Shipping line is required"
        
        if shipping_line not in MaritimeValidator.SHIPPING_LINES and shipping_line != 'other':
            return f"Invalid shipping line. Must be one of: {', '.join(MaritimeValidator.SHIPPING_LINES)} or 'other'"
        
        return None
    
    @staticmethod
    def validate_imo_number(imo_number: str) -> Optional[str]:
        """Validate IMO number format"""
        if not imo_number:
            return None  # IMO is optional
        
        if not MaritimeValidator.IMO_PATTERN.match(imo_number):
            return "IMO number must be in format 'IMO1234567' or 'IMO 1234567'"
        
        return None
    
    @staticmethod
    def validate_mmsi(mmsi: str) -> Optional[str]:
        """Validate MMSI format"""
        if not mmsi:
            return None  # MMSI is optional
        
        if not MaritimeValidator.MMSI_PATTERN.match(mmsi):
            return "MMSI must be exactly 9 digits"
        
        return None
    
    @staticmethod
    def validate_call_sign(call_sign: str) -> Optional[str]:
        """Validate call sign format"""
        if not call_sign:
            return None  # Call sign is optional
        
        if not MaritimeValidator.CALL_SIGN_PATTERN.match(call_sign):
            return "Call sign must be 4-7 alphanumeric characters"
        
        return None
    
    @staticmethod
    def validate_operation_type(operation_type: str) -> Optional[str]:
        """Validate operation type"""
        if not operation_type:
            return "Operation type is required"
        
        if operation_type not in MaritimeValidator.OPERATION_TYPES:
            return f"Invalid operation type. Must be one of: {', '.join(MaritimeValidator.OPERATION_TYPES)}"
        
        return None
    
    @staticmethod
    def validate_status(status: str) -> Optional[str]:
        """Validate operation status"""
        if not status:
            return "Status is required"
        
        if status not in MaritimeValidator.STATUS_OPTIONS:
            return f"Invalid status. Must be one of: {', '.join(MaritimeValidator.STATUS_OPTIONS)}"
        
        return None
    
    @staticmethod
    def validate_operation_date(operation_date: str) -> Optional[str]:
        """Validate operation date"""
        if not operation_date:
            return None  # Operation date is optional
        
        try:
            parsed_date = datetime.strptime(operation_date, '%Y-%m-%d').date()
            today = date.today()
            
            # Allow dates up to 1 year in the past and 1 year in the future
            if (today - parsed_date).days > 365:
                return "Operation date cannot be more than 1 year in the past"
            
            if (parsed_date - today).days > 365:
                return "Operation date cannot be more than 1 year in the future"
            
        except ValueError:
            return "Operation date must be in YYYY-MM-DD format"
        
        return None
    
    @staticmethod
    def validate_eta(eta: str) -> Optional[str]:
        """Validate ETA datetime"""
        if not eta:
            return None  # ETA is optional
        
        try:
            parsed_eta = datetime.fromisoformat(eta.replace('Z', '+00:00'))
            now = datetime.now()
            
            # ETA should be in the future (with 1 hour tolerance for current operations)
            if (now - parsed_eta).total_seconds() > 3600:
                return "ETA cannot be more than 1 hour in the past"
            
            # ETA should not be more than 1 month in the future
            if (parsed_eta - now).days > 30:
                return "ETA cannot be more than 30 days in the future"
            
        except ValueError:
            return "ETA must be in valid datetime format"
        
        return None
    
    @staticmethod
    def validate_berth(berth: str) -> Optional[str]:
        """Validate berth assignment"""
        if not berth:
            return None  # Berth is optional
        
        if berth not in MaritimeValidator.BERTH_OPTIONS:
            return f"Invalid berth. Must be one of: {', '.join(MaritimeValidator.BERTH_OPTIONS)}"
        
        return None
    
    @staticmethod
    def validate_flag_state(flag_state: str) -> Optional[str]:
        """Validate flag state"""
        if not flag_state:
            return None  # Flag state is optional
        
        if flag_state not in MaritimeValidator.FLAG_STATES and flag_state != 'other':
            return f"Invalid flag state. Must be one of: {', '.join(MaritimeValidator.FLAG_STATES)} or 'other'"
        
        return None
    
    @staticmethod
    def validate_integer_field(value: Any, field_name: str, min_value: int = 0, max_value: int = None) -> Optional[str]:
        """Validate integer fields with optional min/max constraints"""
        if value is None or value == '':
            return None  # Allow empty values
        
        try:
            int_value = int(value)
            
            if int_value < min_value:
                return f"{field_name} must be at least {min_value}"
            
            if max_value is not None and int_value > max_value:
                return f"{field_name} must be no more than {max_value}"
            
        except (ValueError, TypeError):
            return f"{field_name} must be a valid number"
        
        return None
    
    @staticmethod
    def validate_progress(progress: Any) -> Optional[str]:
        """Validate progress percentage"""
        return MaritimeValidator.validate_integer_field(progress, "Progress", 0, 100)
    
    @staticmethod
    def validate_time_field(time_value: str, field_name: str) -> Optional[str]:
        """Validate time fields (HH:MM format)"""
        if not time_value:
            return None  # Time fields are optional
        
        time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
        
        if not time_pattern.match(time_value):
            return f"{field_name} must be in HH:MM format (24-hour)"
        
        return None
    
    @staticmethod
    def validate_team_member(name: str, field_name: str) -> Optional[str]:
        """Validate team member name"""
        if not name:
            return None  # Team members are optional
        
        if len(name.strip()) < 2:
            return f"{field_name} must be at least 2 characters long"
        
        if len(name.strip()) > 100:
            return f"{field_name} must be less than 100 characters"
        
        return None
    
    @staticmethod
    def validate_maritime_operation(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Comprehensive validation of maritime operation data"""
        errors = []
        
        # Required fields validation
        required_fields = ['vessel_name', 'vessel_type', 'shipping_line', 'operation_type']
        errors.extend(MaritimeValidator.validate_required_fields(data, required_fields))
        
        # Individual field validations
        validations = [
            MaritimeValidator.validate_vessel_name(data.get('vessel_name', '')),
            MaritimeValidator.validate_vessel_type(data.get('vessel_type', '')),
            MaritimeValidator.validate_shipping_line(data.get('shipping_line', '')),
            MaritimeValidator.validate_operation_type(data.get('operation_type', '')),
            MaritimeValidator.validate_status(data.get('status', 'pending')),
            MaritimeValidator.validate_imo_number(data.get('imo_number', '')),
            MaritimeValidator.validate_mmsi(data.get('mmsi', '')),
            MaritimeValidator.validate_call_sign(data.get('call_sign', '')),
            MaritimeValidator.validate_operation_date(data.get('operation_date', '')),
            MaritimeValidator.validate_eta(data.get('eta', '')),
            MaritimeValidator.validate_berth(data.get('berth', '')),
            MaritimeValidator.validate_flag_state(data.get('flag_state', '')),
            MaritimeValidator.validate_progress(data.get('progress', 0)),
        ]
        
        # Add non-None validation errors
        errors.extend([error for error in validations if error is not None])
        
        # Validate numeric fields
        numeric_fields = [
            'total_vehicles', 'total_automobiles_discharge', 'heavy_equipment_discharge',
            'total_electric_vehicles', 'total_static_cargo', 'brv_target', 'zee_target',
            'sou_target', 'expected_rate', 'total_drivers', 'tico_vans', 'tico_station_wagons'
        ]
        
        for field in numeric_fields:
            error = MaritimeValidator.validate_integer_field(data.get(field, 0), field, 0, 10000)
            if error:
                errors.append(error)
        
        # Validate time fields
        time_fields = [
            'shift_start', 'shift_end', 'target_completion', 'start_time', 'estimated_completion'
        ]
        
        for field in time_fields:
            error = MaritimeValidator.validate_time_field(data.get(field, ''), field)
            if error:
                errors.append(error)
        
        # Validate team member fields
        team_fields = [
            'operation_manager', 'auto_ops_lead', 'auto_ops_assistant',
            'heavy_ops_lead', 'heavy_ops_assistant'
        ]
        
        for field in team_fields:
            error = MaritimeValidator.validate_team_member(data.get(field, ''), field)
            if error:
                errors.append(error)
        
        # Validate break duration
        break_duration_error = MaritimeValidator.validate_integer_field(
            data.get('break_duration', 30), 'break_duration', 0, 480
        )
        if break_duration_error:
            errors.append(break_duration_error)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_validation_rules() -> Dict[str, Dict[str, Any]]:
        """Get client-side validation rules"""
        return {
            'vessel_name': {
                'required': True,
                'minLength': 2,
                'maxLength': 200,
                'pattern': None
            },
            'vessel_type': {
                'required': True,
                'options': MaritimeValidator.VESSEL_TYPES
            },
            'shipping_line': {
                'required': True,
                'options': MaritimeValidator.SHIPPING_LINES + ['other']
            },
            'operation_type': {
                'required': True,
                'options': MaritimeValidator.OPERATION_TYPES
            },
            'imo_number': {
                'required': False,
                'pattern': MaritimeValidator.IMO_PATTERN.pattern
            },
            'mmsi': {
                'required': False,
                'pattern': MaritimeValidator.MMSI_PATTERN.pattern
            },
            'call_sign': {
                'required': False,
                'pattern': MaritimeValidator.CALL_SIGN_PATTERN.pattern
            },
            'progress': {
                'required': False,
                'min': 0,
                'max': 100,
                'type': 'integer'
            }
        }