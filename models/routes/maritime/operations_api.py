"""
Maritime Operations API for real-time cargo tracking
"""

from flask import Blueprint, request, jsonify
from app import db
# MaritimeOperation import moved to individual functions to avoid circular import
from models.maritime.validation import MaritimeValidator
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List

operations_api = Blueprint('operations_api', __name__)

@operations_api.route('/api/operations/cargo/progress/<int:operation_id>', methods=['GET'])
def get_cargo_progress(operation_id: int):
    """Get real-time cargo progress for an operation"""
    from models.maritime.maritime_operation import MaritimeOperation
    try:
        operation = MaritimeOperation.query.get_or_404(operation_id)
        
        # Calculate current progress metrics
        progress_data = {
            'operation_id': operation.id,
            'vessel_name': operation.vessel_name,
            'operation_type': operation.operation_type,
            'status': operation.status,
            'overall_progress': operation.progress or 0,
            'cargo_breakdown': operation.get_cargo_breakdown(),
            'zone_progress': _get_zone_progress(operation),
            'equipment_status': _get_equipment_status(operation),
            'discharge_rates': _get_discharge_rates(operation),
            'estimated_completion': _calculate_estimated_completion(operation),
            'last_updated': operation.updated_at.isoformat() if operation.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'data': progress_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@operations_api.route('/api/operations/cargo/update_progress', methods=['POST'])
def update_cargo_progress():
    """Update real-time cargo progress"""
    from models.maritime.maritime_operation import MaritimeOperation
    try:
        data = request.get_json()
        
        if not data or 'operation_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Operation ID is required'
            }), 400
        
        operation = MaritimeOperation.query.get_or_404(data['operation_id'])
        
        # Update progress fields
        if 'progress' in data:
            operation.progress = min(100, max(0, data['progress']))
        
        # Update zone progress
        if 'zone_progress' in data:
            zone_data = data['zone_progress']
            current_hourly = operation.hourly_quantities or []
            
            # Add new hourly data point
            hourly_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'brv_completed': zone_data.get('brv_completed', 0),
                'zee_completed': zone_data.get('zee_completed', 0),
                'sou_completed': zone_data.get('sou_completed', 0),
                'total_completed': zone_data.get('total_completed', 0),
                'rate_per_hour': zone_data.get('current_rate', 0)
            }
            
            current_hourly.append(hourly_entry)
            
            # Keep only last 24 hours of data
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            current_hourly = [
                entry for entry in current_hourly
                if datetime.fromisoformat(entry['timestamp']) > cutoff_time
            ]
            
            operation.hourly_quantities = current_hourly
        
        # Update equipment status
        if 'equipment_status' in data:
            equipment_data = data['equipment_status']
            
            # Update equipment allocation if provided
            if 'tico_vans' in equipment_data:
                operation.tico_vans = equipment_data['tico_vans']
            if 'tico_station_wagons' in equipment_data:
                operation.tico_station_wagons = equipment_data['tico_station_wagons']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated successfully',
            'current_progress': operation.progress
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@operations_api.route('/api/operations/cargo/zones', methods=['GET'])
def get_zone_info():
    """Get zone configurations and current status"""
    from models.maritime.maritime_operation import MaritimeOperation
    try:
        zones = MaritimeValidator.ZONES
        equipment_specs = MaritimeValidator.EQUIPMENT_SPECS
        
        # Get current operations by zone
        active_operations = MaritimeOperation.query.filter_by(status='in_progress').all()
        
        zone_status = {}
        for zone_code, zone_info in zones.items():
            current_load = 0
            active_ops = []
            
            for op in active_operations:
                zone_target = getattr(op, f'{zone_code.lower()}_target', 0) or 0
                current_load += zone_target
                if zone_target > 0:
                    active_ops.append({
                        'operation_id': op.id,
                        'vessel_name': op.vessel_name,
                        'target': zone_target,
                        'progress': op.progress or 0
                    })
            
            zone_status[zone_code] = {
                'name': zone_info['name'],
                'max_capacity': zone_info['max_capacity'],
                'current_load': current_load,
                'available_capacity': zone_info['max_capacity'] - current_load,
                'utilization_percentage': round((current_load / zone_info['max_capacity']) * 100, 1) if zone_info['max_capacity'] > 0 else 0,
                'equipment_types': zone_info['equipment_types'],
                'cargo_types': zone_info['cargo_types'],
                'active_operations': active_ops
            }
        
        return jsonify({
            'success': True,
            'zones': zone_status,
            'equipment_specs': equipment_specs
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@operations_api.route('/api/operations/cargo/recommendations', methods=['POST'])
def get_cargo_recommendations():
    """Get recommendations for cargo allocation and equipment"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Get zone recommendations
        zone_recommendations = MaritimeValidator.get_zone_recommendations(data)
        
        # Get discharge rate calculations
        discharge_calculations = MaritimeValidator.calculate_discharge_rate(data)
        
        # Get equipment recommendations
        equipment_recommendations = _get_equipment_recommendations(data)
        
        return jsonify({
            'success': True,
            'recommendations': {
                'zones': zone_recommendations,
                'discharge_rates': discharge_calculations,
                'equipment': equipment_recommendations
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@operations_api.route('/api/operations/cargo/analytics/<int:operation_id>', methods=['GET'])
def get_cargo_analytics(operation_id: int):
    """Get detailed analytics for cargo operation"""
    from models.maritime.maritime_operation import MaritimeOperation
    try:
        operation = MaritimeOperation.query.get_or_404(operation_id)
        
        # Prepare data for analytics
        operation_data = {
            'total_vehicles': operation.total_vehicles or 0,
            'total_automobiles_discharge': operation.total_automobiles_discharge or 0,
            'heavy_equipment_discharge': operation.heavy_equipment_discharge or 0,
            'total_electric_vehicles': operation.total_electric_vehicles or 0,
            'total_static_cargo': operation.total_static_cargo or 0,
            'brv_target': operation.brv_target or 0,
            'zee_target': operation.zee_target or 0,
            'sou_target': operation.sou_target or 0,
            'expected_rate': operation.expected_rate or 0,
            'total_drivers': operation.total_drivers or 0,
            'tico_vans': operation.tico_vans or 0,
            'tico_station_wagons': operation.tico_station_wagons or 0
        }
        
        # Calculate analytics
        discharge_rates = MaritimeValidator.calculate_discharge_rate(operation_data)
        zone_recommendations = MaritimeValidator.get_zone_recommendations(operation_data)
        
        # Get hourly progress data
        hourly_data = operation.hourly_quantities or []
        
        # Calculate performance metrics
        performance_metrics = _calculate_performance_metrics(operation, hourly_data)
        
        analytics = {
            'operation_info': {
                'id': operation.id,
                'vessel_name': operation.vessel_name,
                'operation_type': operation.operation_type,
                'status': operation.status,
                'progress': operation.progress or 0,
                'start_time': operation.start_time,
                'estimated_completion': operation.estimated_completion
            },
            'cargo_breakdown': operation.get_cargo_breakdown(),
            'zone_analysis': zone_recommendations,
            'discharge_analysis': discharge_rates,
            'performance_metrics': performance_metrics,
            'hourly_progress': hourly_data,
            'equipment_efficiency': _calculate_equipment_efficiency(operation)
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper functions
def _get_zone_progress(operation: MaritimeOperation) -> Dict[str, Any]:
    """Get zone-specific progress information"""
    brv_target = operation.brv_target or 0
    zee_target = operation.zee_target or 0
    sou_target = operation.sou_target or 0
    
    overall_progress = operation.progress or 0
    
    return {
        'brv': {
            'target': brv_target,
            'completed': int(brv_target * overall_progress / 100) if brv_target > 0 else 0,
            'remaining': brv_target - int(brv_target * overall_progress / 100) if brv_target > 0 else 0,
            'progress_percentage': overall_progress
        },
        'zee': {
            'target': zee_target,
            'completed': int(zee_target * overall_progress / 100) if zee_target > 0 else 0,
            'remaining': zee_target - int(zee_target * overall_progress / 100) if zee_target > 0 else 0,
            'progress_percentage': overall_progress
        },
        'sou': {
            'target': sou_target,
            'completed': int(sou_target * overall_progress / 100) if sou_target > 0 else 0,
            'remaining': sou_target - int(sou_target * overall_progress / 100) if sou_target > 0 else 0,
            'progress_percentage': overall_progress
        }
    }

def _get_equipment_status(operation: MaritimeOperation) -> Dict[str, Any]:
    """Get equipment status and utilization"""
    tico_vans = operation.tico_vans or 0
    tico_station_wagons = operation.tico_station_wagons or 0
    
    van_capacity = tico_vans * MaritimeValidator.EQUIPMENT_SPECS['tico_vans']['capacity_per_hour']
    wagon_capacity = tico_station_wagons * MaritimeValidator.EQUIPMENT_SPECS['tico_station_wagons']['capacity_per_hour']
    
    return {
        'tico_vans': {
            'allocated': tico_vans,
            'hourly_capacity': van_capacity,
            'status': 'active' if tico_vans > 0 else 'inactive'
        },
        'tico_station_wagons': {
            'allocated': tico_station_wagons,
            'hourly_capacity': wagon_capacity,
            'status': 'active' if tico_station_wagons > 0 else 'inactive'
        },
        'total_hourly_capacity': van_capacity + wagon_capacity
    }

def _get_discharge_rates(operation: MaritimeOperation) -> Dict[str, Any]:
    """Get discharge rate information"""
    expected_rate = operation.expected_rate or 0
    total_cargo = operation.get_total_cargo()
    
    # Calculate actual rate from recent hourly data
    hourly_data = operation.hourly_quantities or []
    actual_rate = 0
    
    if len(hourly_data) >= 2:
        recent_entries = hourly_data[-2:]
        if len(recent_entries) == 2:
            time_diff = (datetime.fromisoformat(recent_entries[1]['timestamp']) - 
                        datetime.fromisoformat(recent_entries[0]['timestamp'])).total_seconds() / 3600
            if time_diff > 0:
                cargo_diff = recent_entries[1]['total_completed'] - recent_entries[0]['total_completed']
                actual_rate = cargo_diff / time_diff
    
    return {
        'expected_rate': expected_rate,
        'actual_rate': round(actual_rate, 2),
        'rate_efficiency': round((actual_rate / expected_rate) * 100, 1) if expected_rate > 0 else 0,
        'total_cargo': total_cargo,
        'completion_forecast': _calculate_completion_forecast(operation, actual_rate)
    }

def _calculate_estimated_completion(operation: MaritimeOperation) -> Dict[str, Any]:
    """Calculate estimated completion time"""
    total_cargo = operation.get_total_cargo()
    progress = operation.progress or 0
    remaining_cargo = total_cargo * (100 - progress) / 100
    
    # Get current rate from hourly data
    hourly_data = operation.hourly_quantities or []
    current_rate = 0
    
    if len(hourly_data) >= 2:
        recent_entries = hourly_data[-2:]
        if len(recent_entries) == 2:
            time_diff = (datetime.fromisoformat(recent_entries[1]['timestamp']) - 
                        datetime.fromisoformat(recent_entries[0]['timestamp'])).total_seconds() / 3600
            if time_diff > 0:
                cargo_diff = recent_entries[1]['total_completed'] - recent_entries[0]['total_completed']
                current_rate = cargo_diff / time_diff
    
    if current_rate > 0:
        hours_remaining = remaining_cargo / current_rate
        estimated_completion = datetime.utcnow() + timedelta(hours=hours_remaining)
    else:
        estimated_completion = None
        hours_remaining = None
    
    return {
        'remaining_cargo': remaining_cargo,
        'current_rate': round(current_rate, 2),
        'hours_remaining': round(hours_remaining, 2) if hours_remaining else None,
        'estimated_completion': estimated_completion.isoformat() if estimated_completion else None
    }

def _get_equipment_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get equipment allocation recommendations"""
    total_cargo = (data.get('total_vehicles', 0) or 0) + (data.get('total_static_cargo', 0) or 0)
    expected_rate = data.get('expected_rate', 0) or 0
    
    # Calculate recommended equipment based on cargo type and rate
    automobiles = data.get('total_automobiles_discharge', 0) or 0
    heavy_equipment = data.get('heavy_equipment_discharge', 0) or 0
    electric_vehicles = data.get('total_electric_vehicles', 0) or 0
    
    # TICO vans are good for automobiles and general cargo
    recommended_vans = min(50, max(0, int((automobiles * 0.6) / MaritimeValidator.EQUIPMENT_SPECS['tico_vans']['capacity_per_hour'])))
    
    # TICO station wagons are better for heavy equipment and electric vehicles
    recommended_wagons = min(30, max(0, int((heavy_equipment + electric_vehicles) / MaritimeValidator.EQUIPMENT_SPECS['tico_station_wagons']['capacity_per_hour'])))
    
    return {
        'recommended_tico_vans': recommended_vans,
        'recommended_tico_station_wagons': recommended_wagons,
        'reasoning': {
            'tico_vans': f"Recommended for {automobiles} automobiles at {MaritimeValidator.EQUIPMENT_SPECS['tico_vans']['capacity_per_hour']} units/hour capacity",
            'tico_station_wagons': f"Recommended for {heavy_equipment} heavy equipment and {electric_vehicles} electric vehicles at {MaritimeValidator.EQUIPMENT_SPECS['tico_station_wagons']['capacity_per_hour']} units/hour capacity"
        },
        'total_recommended_capacity': (
            recommended_vans * MaritimeValidator.EQUIPMENT_SPECS['tico_vans']['capacity_per_hour'] +
            recommended_wagons * MaritimeValidator.EQUIPMENT_SPECS['tico_station_wagons']['capacity_per_hour']
        )
    }

def _calculate_performance_metrics(operation: MaritimeOperation, hourly_data: List[Dict]) -> Dict[str, Any]:
    """Calculate performance metrics for the operation"""
    if not hourly_data:
        return {
            'average_rate': 0,
            'peak_rate': 0,
            'efficiency_trend': 'stable',
            'total_time_elapsed': 0
        }
    
    # Calculate rates from hourly data
    rates = []
    for i in range(1, len(hourly_data)):
        prev_entry = hourly_data[i-1]
        curr_entry = hourly_data[i]
        
        time_diff = (datetime.fromisoformat(curr_entry['timestamp']) - 
                    datetime.fromisoformat(prev_entry['timestamp'])).total_seconds() / 3600
        
        if time_diff > 0:
            cargo_diff = curr_entry['total_completed'] - prev_entry['total_completed']
            rate = cargo_diff / time_diff
            rates.append(rate)
    
    if not rates:
        return {
            'average_rate': 0,
            'peak_rate': 0,
            'efficiency_trend': 'stable',
            'total_time_elapsed': 0
        }
    
    # Calculate metrics
    average_rate = sum(rates) / len(rates)
    peak_rate = max(rates)
    
    # Determine efficiency trend
    if len(rates) >= 3:
        recent_avg = sum(rates[-3:]) / 3
        earlier_avg = sum(rates[:3]) / 3
        
        if recent_avg > earlier_avg * 1.1:
            efficiency_trend = 'improving'
        elif recent_avg < earlier_avg * 0.9:
            efficiency_trend = 'declining'
        else:
            efficiency_trend = 'stable'
    else:
        efficiency_trend = 'stable'
    
    # Calculate total time elapsed
    if len(hourly_data) >= 2:
        total_time_elapsed = (datetime.fromisoformat(hourly_data[-1]['timestamp']) - 
                            datetime.fromisoformat(hourly_data[0]['timestamp'])).total_seconds() / 3600
    else:
        total_time_elapsed = 0
    
    return {
        'average_rate': round(average_rate, 2),
        'peak_rate': round(peak_rate, 2),
        'efficiency_trend': efficiency_trend,
        'total_time_elapsed': round(total_time_elapsed, 2)
    }

def _calculate_equipment_efficiency(operation: MaritimeOperation) -> Dict[str, Any]:
    """Calculate equipment efficiency metrics"""
    tico_vans = operation.tico_vans or 0
    tico_station_wagons = operation.tico_station_wagons or 0
    
    van_capacity = tico_vans * MaritimeValidator.EQUIPMENT_SPECS['tico_vans']['capacity_per_hour']
    wagon_capacity = tico_station_wagons * MaritimeValidator.EQUIPMENT_SPECS['tico_station_wagons']['capacity_per_hour']
    total_capacity = van_capacity + wagon_capacity
    
    # Get actual performance from hourly data
    hourly_data = operation.hourly_quantities or []
    actual_rate = 0
    
    if len(hourly_data) >= 2:
        recent_entries = hourly_data[-2:]
        if len(recent_entries) == 2:
            time_diff = (datetime.fromisoformat(recent_entries[1]['timestamp']) - 
                        datetime.fromisoformat(recent_entries[0]['timestamp'])).total_seconds() / 3600
            if time_diff > 0:
                cargo_diff = recent_entries[1]['total_completed'] - recent_entries[0]['total_completed']
                actual_rate = cargo_diff / time_diff
    
    efficiency = (actual_rate / total_capacity) * 100 if total_capacity > 0 else 0
    
    return {
        'equipment_capacity': total_capacity,
        'actual_rate': round(actual_rate, 2),
        'efficiency_percentage': round(efficiency, 1),
        'utilization_status': 'high' if efficiency > 80 else 'medium' if efficiency > 60 else 'low',
        'recommendations': _get_efficiency_recommendations(efficiency, operation)
    }

def _get_efficiency_recommendations(efficiency: float, operation: MaritimeOperation) -> List[str]:
    """Get recommendations to improve efficiency"""
    recommendations = []
    
    if efficiency < 60:
        recommendations.append("Consider increasing equipment allocation")
        recommendations.append("Review driver assignments and shift patterns")
        recommendations.append("Check for operational bottlenecks")
    elif efficiency < 80:
        recommendations.append("Monitor equipment utilization closely")
        recommendations.append("Consider minor adjustments to equipment allocation")
    else:
        recommendations.append("Excellent efficiency - maintain current allocation")
    
    # Zone-specific recommendations
    brv_target = operation.brv_target or 0
    zee_target = operation.zee_target or 0
    sou_target = operation.sou_target or 0
    
    if brv_target > zee_target + sou_target:
        recommendations.append("Consider allocating more equipment to BRV zone")
    elif zee_target > brv_target + sou_target:
        recommendations.append("Consider allocating more equipment to ZEE zone")
    elif sou_target > brv_target + zee_target:
        recommendations.append("Consider allocating more equipment to SOU zone")
    
    return recommendations

def _calculate_completion_forecast(operation: MaritimeOperation, actual_rate: float) -> Dict[str, Any]:
    """Calculate completion forecast based on current rate"""
    total_cargo = operation.get_total_cargo()
    progress = operation.progress or 0
    remaining_cargo = total_cargo * (100 - progress) / 100
    
    if actual_rate > 0:
        hours_remaining = remaining_cargo / actual_rate
        estimated_completion = datetime.utcnow() + timedelta(hours=hours_remaining)
        
        # Calculate confidence level based on rate consistency
        hourly_data = operation.hourly_quantities or []
        if len(hourly_data) >= 3:
            recent_rates = []
            for i in range(max(0, len(hourly_data)-3), len(hourly_data)-1):
                time_diff = (datetime.fromisoformat(hourly_data[i+1]['timestamp']) - 
                           datetime.fromisoformat(hourly_data[i]['timestamp'])).total_seconds() / 3600
                if time_diff > 0:
                    cargo_diff = hourly_data[i+1]['total_completed'] - hourly_data[i]['total_completed']
                    recent_rates.append(cargo_diff / time_diff)
            
            if recent_rates:
                rate_variance = sum(abs(r - actual_rate) for r in recent_rates) / len(recent_rates)
                confidence = max(0, min(100, 100 - (rate_variance / actual_rate * 100)))
            else:
                confidence = 50
        else:
            confidence = 50
    else:
        hours_remaining = None
        estimated_completion = None
        confidence = 0
    
    return {
        'hours_remaining': round(hours_remaining, 2) if hours_remaining else None,
        'estimated_completion': estimated_completion.isoformat() if estimated_completion else None,
        'confidence_level': round(confidence, 1),
        'forecast_reliability': 'high' if confidence > 80 else 'medium' if confidence > 60 else 'low'
    }