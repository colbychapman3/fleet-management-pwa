"""
Maritime Berth Management API - Berth allocation and management
Handles berth assignments, scheduling, and port resource management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import structlog
import json

# Access app components via current_app or direct import
def get_app_db():
    import app
    return app.db

def get_cache_functions():
    import app
    return app.cache_get, app.cache_set, app.cache_delete, app.get_cache_key

from models.models.vessel import Vessel
from models.models.maritime_models import MaritimeOperationsHelper
from models.models.sync_log import SyncLog

logger = structlog.get_logger()

berth_management_bp = Blueprint('berth_management', __name__)

# Define berth configuration (this could be moved to database in future)
BERTH_CONFIG = {
    'berths': {
        'B1': {
            'name': 'Berth 1',
            'zone': 'BRV',
            'max_length': 200,
            'max_beam': 32,
            'depth': 12,
            'facilities': ['crane', 'power', 'water'],
            'capacity': 1000
        },
        'B2': {
            'name': 'Berth 2',
            'zone': 'ZEE',
            'max_length': 180,
            'max_beam': 28,
            'depth': 10,
            'facilities': ['crane', 'power'],
            'capacity': 800
        },
        'B3': {
            'name': 'Berth 3',
            'zone': 'SOU',
            'max_length': 220,
            'max_beam': 35,
            'depth': 14,
            'facilities': ['crane', 'power', 'water', 'fuel'],
            'capacity': 1200
        },
        'B4': {
            'name': 'Berth 4',
            'zone': 'BRV',
            'max_length': 190,
            'max_beam': 30,
            'depth': 11,
            'facilities': ['power', 'water'],
            'capacity': 900
        }
    },
    'zones': {
        'BRV': {
            'name': 'Bravo Zone',
            'description': 'Primary cargo operations zone',
            'berths': ['B1', 'B4']
        },
        'ZEE': {
            'name': 'Zulu Zone', 
            'description': 'Secondary operations zone',
            'berths': ['B2']
        },
        'SOU': {
            'name': 'South Zone',
            'description': 'Heavy cargo operations zone',
            'berths': ['B3']
        }
    }
}

# Maritime role validation decorator
def maritime_access_required(required_roles=None):
    """Decorator to check maritime-specific role permissions"""
    if required_roles is None:
        required_roles = ['manager', 'maritime_supervisor', 'port_controller']
    
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Allow managers full access
            if current_user.is_manager():
                return f(*args, **kwargs)
            
            # Check specific maritime roles
            user_role = getattr(current_user, 'maritime_role', current_user.role)
            if user_role not in required_roles:
                return jsonify({'error': 'Insufficient maritime permissions'}), 403
            
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@berth_management_bp.route('/', methods=['GET'])
@login_required
@maritime_access_required()
def get_berths():
    """
    Get all berths with current status and assignments
    GET /api/maritime/berths/
    """
    try:
        # Get current vessel assignments
        assigned_vessels = Vessel.query.filter(
            Vessel.berth_number.isnot(None),
            Vessel.status.in_(['berthed', 'discharging'])
        ).all()
        
        # Build berth status map
        berth_assignments = {}
        for vessel in assigned_vessels:
            berth_assignments[vessel.berth_number] = {
                'vessel_id': vessel.id,
                'vessel_name': vessel.name,
                'vessel_type': vessel.vessel_type,
                'arrival_date': vessel.arrival_date.isoformat() if vessel.arrival_date else None,
                'status': vessel.status,
                'total_vehicles': vessel.total_vehicles,
                'berth_side': vessel.berth_side,
                'operation_start': vessel.operation_start.isoformat() if vessel.operation_start else None,
                'estimated_completion': None
            }
            
            # Calculate estimated completion
            estimated_completion = MaritimeOperationsHelper.calculate_estimated_completion(vessel.id)
            if estimated_completion:
                berth_assignments[vessel.berth_number]['estimated_completion'] = estimated_completion.isoformat()
        
        # Build comprehensive berth data
        berths_data = []
        for berth_id, berth_info in BERTH_CONFIG['berths'].items():
            berth_data = {
                'berth_id': berth_id,
                'berth_info': berth_info,
                'status': 'available',
                'assignment': None,
                'utilization': {
                    'current_capacity_used': 0,
                    'capacity_percentage': 0
                }
            }
            
            # Add assignment if exists
            if berth_id in berth_assignments:
                berth_data['status'] = 'occupied'
                berth_data['assignment'] = berth_assignments[berth_id]
                
                # Calculate utilization
                vessel_capacity = berth_assignments[berth_id]['total_vehicles'] or 0
                max_capacity = berth_info['capacity']
                berth_data['utilization']['current_capacity_used'] = vessel_capacity
                berth_data['utilization']['capacity_percentage'] = (vessel_capacity / max_capacity) * 100 if max_capacity > 0 else 0
            
            berths_data.append(berth_data)
        
        # Calculate overall port statistics
        port_stats = {
            'total_berths': len(BERTH_CONFIG['berths']),
            'occupied_berths': len(berth_assignments),
            'available_berths': len(BERTH_CONFIG['berths']) - len(berth_assignments),
            'utilization_percentage': (len(berth_assignments) / len(BERTH_CONFIG['berths'])) * 100,
            'total_vessels_berthed': len(assigned_vessels)
        }
        
        return jsonify({
            'berths': berths_data,
            'port_statistics': port_stats,
            'zones': BERTH_CONFIG['zones'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get berths error: {e}")
        return jsonify({'error': 'Failed to retrieve berth information'}), 500

@berth_management_bp.route('/<berth_id>', methods=['GET'])
@login_required
@maritime_access_required()
def get_berth(berth_id):
    """
    Get specific berth details
    GET /api/maritime/berths/{berth_id}
    """
    try:
        # Validate berth exists
        if berth_id not in BERTH_CONFIG['berths']:
            return jsonify({'error': 'Berth not found'}), 404
        
        berth_info = BERTH_CONFIG['berths'][berth_id]
        
        # Get current assignment
        current_vessel = Vessel.query.filter_by(
            berth_number=berth_id
        ).filter(
            Vessel.status.in_(['berthed', 'discharging'])
        ).first()
        
        berth_data = {
            'berth_id': berth_id,
            'berth_info': berth_info,
            'status': 'occupied' if current_vessel else 'available',
            'current_assignment': None,
            'assignment_history': [],
            'upcoming_reservations': []
        }
        
        # Add current assignment details
        if current_vessel:
            berth_data['current_assignment'] = {
                'vessel_id': current_vessel.id,
                'vessel_name': current_vessel.name,
                'vessel_details': current_vessel.to_dict(),
                'berthed_since': current_vessel.operation_start.isoformat() if current_vessel.operation_start else None,
                'estimated_completion': None,
                'zone_summary': MaritimeOperationsHelper.get_zone_summary(current_vessel.id)
            }
            
            # Calculate estimated completion
            estimated_completion = MaritimeOperationsHelper.calculate_estimated_completion(current_vessel.id)
            if estimated_completion:
                berth_data['current_assignment']['estimated_completion'] = estimated_completion.isoformat()
        
        # Get assignment history (last 10 vessels)
        historical_vessels = Vessel.query.filter_by(
            berth_number=berth_id
        ).filter(
            Vessel.status.in_(['departed', 'completed'])
        ).order_by(
            Vessel.updated_at.desc()
        ).limit(10).all()
        
        berth_data['assignment_history'] = [
            {
                'vessel_id': vessel.id,
                'vessel_name': vessel.name,
                'arrival_date': vessel.arrival_date.isoformat() if vessel.arrival_date else None,
                'departure_date': vessel.updated_at.isoformat() if vessel.updated_at else None,
                'total_vehicles': vessel.total_vehicles,
                'status': vessel.status
            }
            for vessel in historical_vessels
        ]
        
        # Get upcoming reservations (vessels with future arrival dates)
        upcoming_vessels = Vessel.query.filter_by(
            berth_number=berth_id
        ).filter(
            Vessel.status == 'arriving',
            Vessel.arrival_date > datetime.utcnow()
        ).order_by(
            Vessel.arrival_date.asc()
        ).limit(5).all()
        
        berth_data['upcoming_reservations'] = [
            {
                'vessel_id': vessel.id,
                'vessel_name': vessel.name,
                'arrival_date': vessel.arrival_date.isoformat() if vessel.arrival_date else None,
                'estimated_duration': vessel.expected_duration,
                'total_vehicles': vessel.total_vehicles
            }
            for vessel in upcoming_vessels
        ]
        
        return jsonify(berth_data)
        
    except Exception as e:
        logger.error(f"Get berth error: {e}")
        return jsonify({'error': 'Failed to retrieve berth details'}), 500

@berth_management_bp.route('/<berth_id>/assign', methods=['PUT'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'port_controller'])
def assign_berth(berth_id):
    """
    Assign vessel to berth
    PUT /api/maritime/berths/{berth_id}/assign
    """
    try:
        # Validate berth exists
        if berth_id not in BERTH_CONFIG['berths']:
            return jsonify({'error': 'Berth not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vessel_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        vessel_id = data['vessel_id']
        vessel = Vessel.query.get(vessel_id)
        if not vessel:
            return jsonify({'error': 'Vessel not found'}), 404
        
        # Check if berth is available
        current_occupant = Vessel.query.filter_by(
            berth_number=berth_id
        ).filter(
            Vessel.status.in_(['berthed', 'discharging'])
        ).first()
        
        if current_occupant and current_occupant.id != vessel_id:
            return jsonify({
                'error': f'Berth {berth_id} is currently occupied by vessel {current_occupant.name}'
            }), 409
        
        # Validate vessel fits berth specifications
        berth_info = BERTH_CONFIG['berths'][berth_id]
        vessel_length = vessel.length or 0
        vessel_beam = vessel.beam or 0
        vessel_draft = vessel.draft or 0
        
        if vessel_length > berth_info['max_length']:
            return jsonify({
                'error': f'Vessel length ({vessel_length}m) exceeds berth maximum ({berth_info["max_length"]}m)'
            }), 400
        
        if vessel_beam > berth_info['max_beam']:
            return jsonify({
                'error': f'Vessel beam ({vessel_beam}m) exceeds berth maximum ({berth_info["max_beam"]}m)'
            }), 400
        
        if vessel_draft > berth_info['depth']:
            return jsonify({
                'error': f'Vessel draft ({vessel_draft}m) exceeds berth depth ({berth_info["depth"]}m)'
            }), 400
        
        # Store original data for logging
        original_data = vessel.to_dict()
        
        # Assign berth to vessel
        vessel.berth_number = berth_id
        vessel.berth_location = berth_info['name']
        vessel.berth_side = data.get('berth_side', 'port')
        vessel.status = 'berthed'
        
        # Set operation start time
        if data.get('operation_start_time'):
            try:
                vessel.operation_start = datetime.fromisoformat(data['operation_start_time'].replace('Z', '+00:00'))
            except ValueError:
                vessel.operation_start = datetime.utcnow()
        else:
            vessel.operation_start = datetime.utcnow()
        
        # Update vessel zone based on berth
        for zone_id, zone_info in BERTH_CONFIG['zones'].items():
            if berth_id in zone_info['berths']:
                vessel.current_zone = zone_id
                break
        
        vessel.updated_at = datetime.utcnow()
        
        db = get_app_db()
        db.session.commit()
        
        # Log berth assignment
        SyncLog.log_action(
            user_id=current_user.id,
            action='update',
            table_name='berth_assignments',
            record_id=vessel.id,
            data_before=original_data,
            data_after=vessel.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('berths', '*'))
        cache_delete(get_cache_key('vessels', '*'))
        
        logger.info(f"Berth {berth_id} assigned to vessel {vessel.id} by user {current_user.id}")
        
        return jsonify({
            'message': f'Vessel {vessel.name} successfully assigned to {berth_info["name"]}',
            'assignment': {
                'berth_id': berth_id,
                'berth_name': berth_info['name'],
                'vessel_id': vessel.id,
                'vessel_name': vessel.name,
                'operation_start': vessel.operation_start.isoformat(),
                'berth_side': vessel.berth_side,
                'zone': vessel.current_zone
            }
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Assign berth error: {e}")
        return jsonify({'error': 'Failed to assign berth'}), 500

@berth_management_bp.route('/<berth_id>/release', methods=['PUT'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'port_controller'])
def release_berth(berth_id):
    """
    Release vessel from berth
    PUT /api/maritime/berths/{berth_id}/release
    """
    try:
        # Validate berth exists
        if berth_id not in BERTH_CONFIG['berths']:
            return jsonify({'error': 'Berth not found'}), 404
        
        # Find current occupant
        vessel = Vessel.query.filter_by(
            berth_number=berth_id
        ).filter(
            Vessel.status.in_(['berthed', 'discharging'])
        ).first()
        
        if not vessel:
            return jsonify({'error': f'Berth {berth_id} is not currently occupied'}), 400
        
        data = request.get_json() or {}
        
        # Store original data for logging
        original_data = vessel.to_dict()
        
        # Release berth
        vessel.berth_number = None
        vessel.berth_location = None
        vessel.berth_side = None
        vessel.status = data.get('new_status', 'departed')
        vessel.current_zone = None
        
        # Set departure time
        vessel.departure_time = datetime.utcnow()
        vessel.updated_at = datetime.utcnow()
        
        # Add completion notes if provided
        if data.get('completion_notes'):
            vessel.operation_notes = (vessel.operation_notes or '') + f"\nDeparture: {data['completion_notes']}"
        
        db = get_app_db()
        db.session.commit()
        
        # Log berth release
        SyncLog.log_action(
            user_id=current_user.id,
            action='update',
            table_name='berth_assignments',
            record_id=vessel.id,
            data_before=original_data,
            data_after=vessel.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('berths', '*'))
        cache_delete(get_cache_key('vessels', '*'))
        
        logger.info(f"Berth {berth_id} released from vessel {vessel.id} by user {current_user.id}")
        
        return jsonify({
            'message': f'Berth {berth_id} successfully released',
            'release_details': {
                'berth_id': berth_id,
                'vessel_id': vessel.id,
                'vessel_name': vessel.name,
                'departure_time': vessel.departure_time.isoformat(),
                'new_status': vessel.status
            }
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Release berth error: {e}")
        return jsonify({'error': 'Failed to release berth'}), 500

# Helper functions

def both_confirmed(assignment1, assignment2):
    """Check if both assignments are confirmed (not estimated)"""
    return not assignment1.get('estimated', False) and not assignment2.get('estimated', False)

def calculate_berth_utilization(berth_id, vessels, period_days):
    """Calculate utilization percentage for a specific berth"""
    berth_vessels = [v for v in vessels if v.berth_number == berth_id]
    
    total_occupied_hours = 0
    for vessel in berth_vessels:
        if vessel.arrival_date:
            departure = vessel.departure_time or datetime.utcnow()
            occupied_hours = (departure - vessel.arrival_date).total_seconds() / 3600
            total_occupied_hours += occupied_hours
    
    total_available_hours = period_days * 24
    return (total_occupied_hours / total_available_hours) * 100 if total_available_hours > 0 else 0

def run_berth_optimization(pending_vessels):
    """Run berth allocation optimization algorithm"""
    # Simple optimization algorithm - can be enhanced with more sophisticated logic
    optimization_result = {
        'optimal_assignments': [],
        'conflicts': [],
        'efficiency_score': 0
    }
    
    # Get currently available berths
    occupied_berths = set(
        vessel.berth_number for vessel in Vessel.query.filter(
            Vessel.berth_number.isnot(None),
            Vessel.status.in_(['berthed', 'discharging'])
        ).all()
    )
    
    available_berths = [
        berth_id for berth_id in BERTH_CONFIG['berths'].keys()
        if berth_id not in occupied_berths
    ]
    
    # Score and assign vessels to berths
    for vessel_data in pending_vessels:
        best_berth = None
        best_score = -1
        
        for berth_id in available_berths:
            berth_info = BERTH_CONFIG['berths'][berth_id]
            
            # Calculate compatibility score
            score = calculate_compatibility_score(vessel_data, berth_info)
            
            if score > best_score:
                best_score = score
                best_berth = berth_id
        
        if best_berth:
            optimization_result['optimal_assignments'].append({
                'vessel_id': vessel_data['vessel_id'],
                'vessel_name': vessel_data['vessel_name'],
                'recommended_berth': best_berth,
                'compatibility_score': best_score,
                'reasons': get_assignment_reasons(vessel_data, BERTH_CONFIG['berths'][best_berth])
            })
            available_berths.remove(best_berth)
        else:
            optimization_result['conflicts'].append({
                'vessel_id': vessel_data['vessel_id'],
                'vessel_name': vessel_data['vessel_name'],
                'issue': 'No suitable berth available',
                'suggestions': ['Wait for berth to become available', 'Consider alternative arrangements']
            })
    
    # Calculate efficiency score
    optimization_result['efficiency_score'] = calculate_optimization_efficiency(optimization_result)
    
    return optimization_result

def calculate_compatibility_score(vessel_data, berth_info):
    """Calculate compatibility score between vessel and berth"""
    score = 100
    
    # Physical constraints
    if vessel_data['length'] > berth_info['max_length']:
        return 0  # Hard constraint
    if vessel_data['beam'] > berth_info['max_beam']:
        return 0  # Hard constraint
    if vessel_data['draft'] > berth_info['depth']:
        return 0  # Hard constraint
    
    # Capacity utilization (prefer efficient use)
    capacity_utilization = vessel_data['total_vehicles'] / berth_info['capacity']
    if capacity_utilization > 1:
        score -= 30  # Over capacity penalty
    elif capacity_utilization < 0.3:
        score -= 10  # Under-utilization penalty
    else:
        score += (capacity_utilization - 0.3) * 20  # Bonus for good utilization
    
    # Size efficiency (prefer good fit)
    length_efficiency = vessel_data['length'] / berth_info['max_length']
    score += length_efficiency * 10
    
    return max(0, score)

def get_assignment_reasons(vessel_data, berth_info):
    """Get reasons for berth assignment recommendation"""
    reasons = []
    
    # Physical compatibility
    reasons.append(f"Vessel fits berth dimensions ({vessel_data['length']}m < {berth_info['max_length']}m)")
    
    # Capacity utilization
    utilization = vessel_data['total_vehicles'] / berth_info['capacity'] * 100
    reasons.append(f"Good capacity utilization ({utilization:.1f}%)")
    
    # Available facilities
    if berth_info['facilities']:
        reasons.append(f"Available facilities: {', '.join(berth_info['facilities'])}")
    
    return reasons

def calculate_optimization_efficiency(optimization_result):
    """Calculate overall efficiency score for the optimization"""
    if not optimization_result['optimal_assignments']:
        return 0
    
    total_score = sum(
        assignment['compatibility_score'] 
        for assignment in optimization_result['optimal_assignments']
    )
    
    avg_score = total_score / len(optimization_result['optimal_assignments'])
    
    # Penalize conflicts
    conflict_penalty = len(optimization_result['conflicts']) * 10
    
    return max(0, avg_score - conflict_penalty)

def generate_berth_recommendations(optimization_result):
    """Generate actionable recommendations from optimization results"""
    recommendations = []
    
    # Successful assignments
    for assignment in optimization_result['optimal_assignments']:
        recommendations.append({
            'type': 'assignment',
            'priority': 'high',
            'action': f"Assign {assignment['vessel_name']} to {assignment['recommended_berth']}",
            'rationale': assignment['reasons'][0] if assignment['reasons'] else 'Optimal compatibility'
        })
    
    # Conflict resolutions
    for conflict in optimization_result['conflicts']:
        recommendations.append({
            'type': 'conflict',
            'priority': 'urgent',
            'action': f"Resolve assignment for {conflict['vessel_name']}",
            'rationale': conflict['issue'],
            'suggestions': conflict['suggestions']
        })
    
    # General optimization suggestions
    if optimization_result['efficiency_score'] < 70:
        recommendations.append({
            'type': 'optimization',
            'priority': 'medium',
            'action': 'Review berth allocation strategy',
            'rationale': f"Current efficiency score is {optimization_result['efficiency_score']:.1f}%"
        })
    
    return recommendations
