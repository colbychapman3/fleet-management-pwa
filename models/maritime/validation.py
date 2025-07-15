"""
Maritime operation validation system for stevedoring operations
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional


class MaritimeValidator:
    """Comprehensive validation for maritime operations"""
    
    # Zone configurations
    ZONES = {
        'BRV': {
            'name': 'Berth Receiving Vessel',
            'max_capacity': 500,
            'equipment_types': ['tico_vans', 'tico_station_wagons'],
            'cargo_types': ['automobiles', 'heavy_equipment', 'static_cargo']
        },
        'ZEE': {
            'name': 'Zone Export/Empty',
            'max_capacity': 300,
            'equipment_types': ['tico_vans', 'tico_station_wagons'],
            'cargo_types': ['automobiles', 'electric_vehicles', 'static_cargo']
        },
        'SOU': {
            'name': 'South Terminal',
            'max_capacity': 400,
            'equipment_types': ['tico_station_wagons'],
            'cargo_types': ['automobiles', 'heavy_equipment']
        }
    }
    
    # Equipment specifications
    EQUIPMENT_SPECS = {
        'tico_vans': {
            'capacity_per_hour': 25,
            'max_weight': 3500,  # kg
            'suitable_cargo': ['automobiles', 'static_cargo']
        },
        'tico_station_wagons': {
            'capacity_per_hour': 15,
            'max_weight': 2500,  # kg
            'suitable_cargo': ['automobiles', 'electric_vehicles', 'heavy_equipment']
        }
    }
    
    @staticmethod
    def validate_maritime_operation(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation for maritime operations
        
        Args:
            data: Dictionary containing operation data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Basic required fields
        required_fields = ['vessel_name', 'operation_type', 'port']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        # Vessel name validation
        if data.get('vessel_name'):
            if not MaritimeValidator._validate_vessel_name(data['vessel_name']):
                errors.append("Vessel name must be between 2 and 200 characters")
        
        # Operation type validation
        valid_operation_types = ['loading', 'discharging', 'maintenance', 'inspection', 'refueling']
        if data.get('operation_type') and data['operation_type'] not in valid_operation_types:
            errors.append(f"Operation type must be one of: {', '.join(valid_operation_types)}")
        
        # IMO number validation
        if data.get('imo_number'):
            if not MaritimeValidator._validate_imo_number(data['imo_number']):
                errors.append("IMO number must be in format IMO1234567")
        
        # MMSI validation
        if data.get('mmsi'):
            if not MaritimeValidator._validate_mmsi(data['mmsi']):
                errors.append("MMSI must be exactly 9 digits")
        
        # Progress validation
        if data.get('progress') is not None:
            if not (0 <= data['progress'] <= 100):
                errors.append("Progress must be between 0 and 100")
        
        # Zone target validation
        zone_errors = MaritimeValidator._validate_zone_targets(data)
        errors.extend(zone_errors)
        
        # Equipment validation
        equipment_errors = MaritimeValidator._validate_equipment_allocation(data)
        errors.extend(equipment_errors)
        
        # Cargo validation
        cargo_errors = MaritimeValidator._validate_cargo_data(data)
        errors.extend(cargo_errors)
        
        # Discharge rate validation
        rate_errors = MaritimeValidator._validate_discharge_rates(data)
        errors.extend(rate_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_vessel_name(name: str) -> bool:
        """Validate vessel name format"""
        return isinstance(name, str) and 2 <= len(name.strip()) <= 200
    
    @staticmethod
    def _validate_imo_number(imo: str) -> bool:
        """Validate IMO number format"""
        if not imo:
            return True  # Optional field
        
        # Remove spaces and convert to uppercase
        imo = imo.replace(' ', '').upper()
        
        # Check format: IMO followed by 7 digits
        pattern = r'^IMO\d{7}$'
        if not re.match(pattern, imo):
            return False
        
        # Extract the 7-digit number
        number_part = imo[3:]
        
        # Calculate check digit (simple validation)
        check_digit = int(number_part[-1])
        digits = [int(d) for d in number_part[:-1]]
        
        # IMO check digit calculation
        multipliers = [7, 6, 5, 4, 3, 2]
        total = sum(d * m for d, m in zip(digits, multipliers))
        calculated_check = total % 10
        
        return calculated_check == check_digit
    
    @staticmethod
    def _validate_mmsi(mmsi: str) -> bool:
        """Validate MMSI format"""
        if not mmsi:
            return True  # Optional field
        
        # Remove spaces and non-digits
        mmsi = re.sub(r'\D', '', mmsi)
        
        # Must be exactly 9 digits
        return len(mmsi) == 9 and mmsi.isdigit()
    
    @staticmethod
    def _validate_zone_targets(data: Dict[str, Any]) -> List[str]:
        """Validate zone-based operation targets"""
        errors = []
        
        brv_target = data.get('brv_target', 0) or 0
        zee_target = data.get('zee_target', 0) or 0
        sou_target = data.get('sou_target', 0) or 0
        
        # Check zone capacity limits
        if brv_target > MaritimeValidator.ZONES['BRV']['max_capacity']:
            errors.append(f"BRV target ({brv_target}) exceeds maximum capacity ({MaritimeValidator.ZONES['BRV']['max_capacity']})")
        
        if zee_target > MaritimeValidator.ZONES['ZEE']['max_capacity']:
            errors.append(f"ZEE target ({zee_target}) exceeds maximum capacity ({MaritimeValidator.ZONES['ZEE']['max_capacity']})")
        
        if sou_target > MaritimeValidator.ZONES['SOU']['max_capacity']:
            errors.append(f"SOU target ({sou_target}) exceeds maximum capacity ({MaritimeValidator.ZONES['SOU']['max_capacity']})")
        
        # Check total target vs. total cargo
        total_target = brv_target + zee_target + sou_target
        total_cargo = (data.get('total_vehicles', 0) or 0) + (data.get('total_static_cargo', 0) or 0)
        
        if total_target > total_cargo:
            errors.append(f"Total zone targets ({total_target}) exceed total cargo ({total_cargo})")
        
        return errors
    
    @staticmethod
    def _validate_equipment_allocation(data: Dict[str, Any]) -> List[str]:
        """Validate equipment allocation"""
        errors = []
        
        tico_vans = data.get('tico_vans', 0) or 0
        tico_station_wagons = data.get('tico_station_wagons', 0) or 0
        
        # Check reasonable equipment numbers
        if tico_vans < 0 or tico_vans > 50:
            errors.append("TICO vans must be between 0 and 50")
        
        if tico_station_wagons < 0 or tico_station_wagons > 30:
            errors.append("TICO station wagons must be between 0 and 30")
        
        # Check equipment capacity vs. cargo
        total_equipment_capacity = (
            tico_vans * MaritimeValidator.EQUIPMENT_SPECS['tico_vans']['capacity_per_hour'] +
            tico_station_wagons * MaritimeValidator.EQUIPMENT_SPECS['tico_station_wagons']['capacity_per_hour']
        )
        
        expected_rate = data.get('expected_rate', 0) or 0
        if expected_rate > 0 and total_equipment_capacity < expected_rate:
            errors.append(f"Equipment capacity ({total_equipment_capacity}/hour) insufficient for expected rate ({expected_rate}/hour)")
        
        return errors
    
    @staticmethod
    def _validate_cargo_data(data: Dict[str, Any]) -> List[str]:
        """Validate cargo data consistency"""
        errors = []
        
        total_vehicles = data.get('total_vehicles', 0) or 0
        automobiles = data.get('total_automobiles_discharge', 0) or 0
        heavy_equipment = data.get('heavy_equipment_discharge', 0) or 0
        electric_vehicles = data.get('total_electric_vehicles', 0) or 0
        static_cargo = data.get('total_static_cargo', 0) or 0
        
        # Check vehicle breakdown consistency
        vehicle_sum = automobiles + heavy_equipment + electric_vehicles
        if vehicle_sum > total_vehicles:
            errors.append(f"Vehicle breakdown sum ({vehicle_sum}) exceeds total vehicles ({total_vehicles})")
        
        # Check negative values
        cargo_fields = {
            'total_vehicles': total_vehicles,
            'total_automobiles_discharge': automobiles,
            'heavy_equipment_discharge': heavy_equipment,
            'total_electric_vehicles': electric_vehicles,
            'total_static_cargo': static_cargo
        }
        
        for field, value in cargo_fields.items():
            if value < 0:
                errors.append(f"{field.replace('_', ' ').title()} cannot be negative")
        
        return errors
    
    @staticmethod
    def _validate_discharge_rates(data: Dict[str, Any]) -> List[str]:
        """Validate discharge rate calculations"""
        errors = []
        
        expected_rate = data.get('expected_rate', 0) or 0
        total_drivers = data.get('total_drivers', 0) or 0
        total_cargo = (data.get('total_vehicles', 0) or 0) + (data.get('total_static_cargo', 0) or 0)
        
        # Check driver-to-cargo ratio
        if total_drivers > 0 and total_cargo > 0:
            cargo_per_driver = total_cargo / total_drivers
            if cargo_per_driver > 20:  # Reasonable limit
                errors.append(f"Cargo per driver ({cargo_per_driver:.1f}) seems high (>20)")
        
        # Check expected rate feasibility
        if expected_rate > 0 and total_cargo > 0:
            # Assuming 8-hour shift
            shift_duration = 8
            required_rate = total_cargo / shift_duration
            
            if expected_rate < required_rate * 0.8:  # 80% efficiency minimum
                errors.append(f"Expected rate ({expected_rate}/hour) may be too low for cargo volume (requires ~{required_rate:.1f}/hour)")
        
        return errors
    
    @staticmethod
    def calculate_discharge_rate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal discharge rate based on cargo and equipment"""
        
        # Get cargo data
        total_vehicles = data.get('total_vehicles', 0) or 0
        total_static_cargo = data.get('total_static_cargo', 0) or 0
        total_cargo = total_vehicles + total_static_cargo
        
        # Get equipment data
        tico_vans = data.get('tico_vans', 0) or 0
        tico_station_wagons = data.get('tico_station_wagons', 0) or 0
        
        # Calculate equipment capacity
        van_capacity = tico_vans * MaritimeValidator.EQUIPMENT_SPECS['tico_vans']['capacity_per_hour']
        wagon_capacity = tico_station_wagons * MaritimeValidator.EQUIPMENT_SPECS['tico_station_wagons']['capacity_per_hour']
        total_equipment_capacity = van_capacity + wagon_capacity
        
        # Calculate zone distribution
        brv_target = data.get('brv_target', 0) or 0
        zee_target = data.get('zee_target', 0) or 0
        sou_target = data.get('sou_target', 0) or 0
        
        # Calculate optimal rates
        shift_duration = 8  # hours
        total_drivers = data.get('total_drivers', 0) or 0
        
        # Base rate calculation
        if total_cargo > 0:
            base_rate = total_cargo / shift_duration
            
            # Adjust for equipment availability
            if total_equipment_capacity > 0:
                equipment_adjusted_rate = min(base_rate, total_equipment_capacity)
            else:
                equipment_adjusted_rate = base_rate
            
            # Adjust for driver availability
            if total_drivers > 0:
                driver_capacity = total_drivers * 3  # 3 units per driver per hour
                driver_adjusted_rate = min(equipment_adjusted_rate, driver_capacity)
            else:
                driver_adjusted_rate = equipment_adjusted_rate
            
            optimal_rate = driver_adjusted_rate
        else:
            optimal_rate = 0
        
        return {
            'optimal_rate_per_hour': round(optimal_rate, 1),
            'total_cargo': total_cargo,
            'equipment_capacity': total_equipment_capacity,
            'estimated_completion_hours': round(total_cargo / optimal_rate, 1) if optimal_rate > 0 else 0,
            'zone_distribution': {
                'brv': brv_target,
                'zee': zee_target,
                'sou': sou_target
            },
            'efficiency_factors': {
                'equipment_utilization': min(1.0, optimal_rate / total_equipment_capacity) if total_equipment_capacity > 0 else 0,
                'driver_utilization': min(1.0, optimal_rate / (total_drivers * 3)) if total_drivers > 0 else 0
            }
        }
    
    @staticmethod
    def get_zone_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations for zone-based operations"""
        
        total_vehicles = data.get('total_vehicles', 0) or 0
        automobiles = data.get('total_automobiles_discharge', 0) or 0
        heavy_equipment = data.get('heavy_equipment_discharge', 0) or 0
        electric_vehicles = data.get('total_electric_vehicles', 0) or 0
        static_cargo = data.get('total_static_cargo', 0) or 0
        
        recommendations = {
            'BRV': {
                'recommended_allocation': 0,
                'cargo_types': [],
                'equipment_suggestion': []
            },
            'ZEE': {
                'recommended_allocation': 0,
                'cargo_types': [],
                'equipment_suggestion': []
            },
            'SOU': {
                'recommended_allocation': 0,
                'cargo_types': [],
                'equipment_suggestion': []
            }
        }
        
        # BRV recommendations (best for automobiles and static cargo)
        brv_allocation = min(automobiles + static_cargo, MaritimeValidator.ZONES['BRV']['max_capacity'])
        recommendations['BRV']['recommended_allocation'] = brv_allocation
        recommendations['BRV']['cargo_types'] = ['automobiles', 'static_cargo']
        recommendations['BRV']['equipment_suggestion'] = ['tico_vans', 'tico_station_wagons']
        
        # ZEE recommendations (best for electric vehicles)
        zee_allocation = min(electric_vehicles, MaritimeValidator.ZONES['ZEE']['max_capacity'])
        recommendations['ZEE']['recommended_allocation'] = zee_allocation
        recommendations['ZEE']['cargo_types'] = ['electric_vehicles']
        recommendations['ZEE']['equipment_suggestion'] = ['tico_station_wagons']
        
        # SOU recommendations (best for heavy equipment)
        sou_allocation = min(heavy_equipment, MaritimeValidator.ZONES['SOU']['max_capacity'])
        recommendations['SOU']['recommended_allocation'] = sou_allocation
        recommendations['SOU']['cargo_types'] = ['heavy_equipment']
        recommendations['SOU']['equipment_suggestion'] = ['tico_station_wagons']
        
        return recommendations