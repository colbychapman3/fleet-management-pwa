"""
Maritime Team Management API - Stevedore team operations
Handles team assignments, shift management, and personnel allocation
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, time
import structlog
import json

# Access app components via current_app or direct import
def get_app_db():
    import app
    return app.db

def get_cache_functions():
    import app
    return app.cache_get, app.cache_set, app.cache_delete, app.get_cache_key

from models.models.user import User
from models.models.vessel import Vessel
from models.models.maritime_models import (
    MaritimeOperationsHelper
)
from models.maritime.stevedore_team import StevedoreTeam
from models.models.tico_vehicle import TicoVehicle
from models.models.sync_log import SyncLog

logger = structlog.get_logger()

team_management_bp = Blueprint('team_management', __name__)

# Maritime role validation decorator
def maritime_access_required(required_roles=None):
    """Decorator to check maritime-specific role permissions"""
    if required_roles is None:
        required_roles = ['manager', 'maritime_supervisor', 'stevedore_lead']
    
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

@team_management_bp.route('/', methods=['GET'])
@login_required
@maritime_access_required()
def get_teams():
    """
    Get all stevedore teams with filtering
    GET /api/maritime/teams/?vessel_id=1&team_type=Auto+Ops&active_only=true
    """
    try:
        # Get query parameters
        vessel_id = request.args.get('vessel_id', type=int)
        team_type = request.args.get('team_type')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build cache key for caching
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_key = get_cache_key('teams', vessel_id, team_type, active_only, page, per_page)
        
        # Try cache first
        cached_result = cache_get(cache_key)
        if cached_result:
            return jsonify(json.loads(cached_result))
        
        # Build query
        query = StevedoreTeam.query
        
        # Apply filters
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        if team_type:
            query = query.filter_by(team_type=team_type)
        
        # If active_only, filter by vessels that are currently active
        if active_only:
            query = query.join(Vessel).filter(
                Vessel.status.in_(['arriving', 'berthed', 'discharging'])
            )
        
        # Order by creation date
        query = query.order_by(StevedoreTeam.created_at.desc())
        
        # Paginate
        teams_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Build response with team details and member information
        teams_data = []
        for team in teams_paginated.items:
            team_dict = team.to_dict()
            
            # Add member details
            member_ids = team.get_members()
            team_dict['member_details'] = []
            
            if member_ids:
                members = User.query.filter(User.id.in_(member_ids)).all()
                team_dict['member_details'] = [
                    {
                        'id': member.id,
                        'name': member.get_full_name(),
                        'role': getattr(member, 'maritime_role', member.role),
                        'experience_level': getattr(member, 'experience_level', 'intermediate')
                    }
                    for member in members
                ]
            
            # Add vessel information
            if team.vessel:
                team_dict['vessel_info'] = {
                    'name': team.vessel.name,
                    'status': team.vessel.status,
                    'berth_number': team.vessel.berth_number
                }
            
            # Add current shift status
            current_time = datetime.now().time()
            team_dict['shift_status'] = calculate_shift_status(team.shift_start, team.shift_end, current_time)
            
            teams_data.append(team_dict)
        
        result = {
            'teams': teams_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': teams_paginated.total,
                'pages': teams_paginated.pages,
                'has_next': teams_paginated.has_next,
                'has_prev': teams_paginated.has_prev
            },
            'filters': {
                'vessel_id': vessel_id,
                'team_type': team_type,
                'active_only': active_only
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        cache_set(cache_key, json.dumps(result), timeout=300)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get teams error: {e}")
        return jsonify({'error': 'Failed to retrieve teams'}), 500

@team_management_bp.route('/', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def create_team():
    """
    Create new stevedore team
    POST /api/maritime/teams/
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vessel_id', 'team_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate vessel exists
        vessel = Vessel.query.get(data['vessel_id'])
        if not vessel:
            return jsonify({'error': 'Vessel not found'}), 404
        
        # Validate team members exist
        member_ids = data.get('members', [])
        if member_ids:
            existing_members = User.query.filter(User.id.in_(member_ids)).all()
            if len(existing_members) != len(member_ids):
                return jsonify({'error': 'One or more team members not found'}), 400
        
        # Validate lead and assistant exist
        lead_id = data.get('lead_id')
        assistant_id = data.get('assistant_id')
        
        if lead_id and not User.query.get(lead_id):
            return jsonify({'error': 'Team lead not found'}), 404
        if assistant_id and not User.query.get(assistant_id):
            return jsonify({'error': 'Team assistant not found'}), 404
        
        # Parse shift times
        shift_start = None
        shift_end = None
        
        if data.get('shift_start'):
            try:
                shift_start = datetime.strptime(data['shift_start'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Invalid shift_start format. Use HH:MM'}), 400
        
        if data.get('shift_end'):
            try:
                shift_end = datetime.strptime(data['shift_end'], '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Invalid shift_end format. Use HH:MM'}), 400
        
        # Create team
        team = StevedoreTeam(
            vessel_id=data['vessel_id'],
            team_type=data['team_type'],
            lead_id=lead_id,
            assistant_id=assistant_id,
            shift_start=shift_start,
            shift_end=shift_end,
            created_at=datetime.utcnow()
        )
        
        # Set team members
        if member_ids:
            team.set_members(member_ids)
        
        db = get_app_db()
        db.session.add(team)
        db.session.commit()
        
        # Log team creation
        SyncLog.log_action(
            user_id=current_user.id,
            action='create',
            table_name='stevedore_teams',
            record_id=team.id,
            data_after=team.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('teams', '*'))
        
        logger.info(f"Stevedore team created: {team.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Team created successfully',
            'team': team.to_dict()
        }), 201
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Create team error: {e}")
        return jsonify({'error': 'Failed to create team'}), 500

@team_management_bp.route('/<int:team_id>', methods=['GET'])
@login_required
@maritime_access_required()
def get_team(team_id):
    """
    Get specific stevedore team details
    GET /api/maritime/teams/{id}
    """
    try:
        team = StevedoreTeam.query.get_or_404(team_id)
        
        # Build comprehensive team data
        team_data = team.to_dict()
        
        # Add detailed member information
        member_ids = team.get_members()
        team_data['member_details'] = []
        
        if member_ids:
            members = User.query.filter(User.id.in_(member_ids)).all()
            team_data['member_details'] = [
                {
                    'id': member.id,
                    'username': member.username,
                    'name': member.get_full_name(),
                    'email': member.email,
                    'role': getattr(member, 'maritime_role', member.role),
                    'experience_level': getattr(member, 'experience_level', 'intermediate'),
                    'last_login': member.last_login.isoformat() if member.last_login else None,
                    'is_active': member.is_active
                }
                for member in members
            ]
        
        # Add lead and assistant details
        if team.lead:
            team_data['lead_details'] = {
                'id': team.lead.id,
                'name': team.lead.get_full_name(),
                'email': team.lead.email,
                'experience_level': getattr(team.lead, 'experience_level', 'senior')
            }
        
        if team.assistant:
            team_data['assistant_details'] = {
                'id': team.assistant.id,
                'name': team.assistant.get_full_name(),
                'email': team.assistant.email,
                'experience_level': getattr(team.assistant, 'experience_level', 'intermediate')
            }
        
        # Add vessel details
        if team.vessel:
            team_data['vessel_details'] = team.vessel.to_dict()
        
        # Add current shift status
        current_time = datetime.now().time()
        team_data['shift_status'] = calculate_shift_status(team.shift_start, team.shift_end, current_time)
        
        # Add team performance metrics (if available)
        team_data['performance_metrics'] = calculate_team_performance(team_id)
        
        return jsonify(team_data)
        
    except Exception as e:
        logger.error(f"Get team error: {e}")
        return jsonify({'error': 'Failed to retrieve team'}), 500

@team_management_bp.route('/<int:team_id>', methods=['PUT'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def update_team(team_id):
    """
    Update stevedore team
    PUT /api/maritime/teams/{id}
    """
    try:
        team = StevedoreTeam.query.get_or_404(team_id)
        data = request.get_json()
        
        # Store original data for logging
        original_data = team.to_dict()
        
        # Update basic fields
        updatable_fields = ['team_type', 'lead_id', 'assistant_id']
        for field in updatable_fields:
            if field in data:
                setattr(team, field, data[field])
        
        # Update shift times
        if 'shift_start' in data:
            if data['shift_start']:
                try:
                    team.shift_start = datetime.strptime(data['shift_start'], '%H:%M').time()
                except ValueError:
                    return jsonify({'error': 'Invalid shift_start format. Use HH:MM'}), 400
            else:
                team.shift_start = None
        
        if 'shift_end' in data:
            if data['shift_end']:
                try:
                    team.shift_end = datetime.strptime(data['shift_end'], '%H:%M').time()
                except ValueError:
                    return jsonify({'error': 'Invalid shift_end format. Use HH:MM'}), 400
            else:
                team.shift_end = None
        
        # Update team members
        if 'members' in data:
            member_ids = data['members']
            if member_ids:
                # Validate members exist
                existing_members = User.query.filter(User.id.in_(member_ids)).all()
                if len(existing_members) != len(member_ids):
                    return jsonify({'error': 'One or more team members not found'}), 400
            
            team.set_members(member_ids)
        
        # Validate lead and assistant
        if data.get('lead_id') and not User.query.get(data['lead_id']):
            return jsonify({'error': 'Team lead not found'}), 404
        if data.get('assistant_id') and not User.query.get(data['assistant_id']):
            return jsonify({'error': 'Team assistant not found'}), 404
        
        db = get_app_db()
        db.session.commit()
        
        # Log team update
        SyncLog.log_action(
            user_id=current_user.id,
            action='update',
            table_name='stevedore_teams',
            record_id=team.id,
            data_before=original_data,
            data_after=team.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('teams', '*'))
        
        logger.info(f"Stevedore team updated: {team.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Team updated successfully',
            'team': team.to_dict()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Update team error: {e}")
        return jsonify({'error': 'Failed to update team'}), 500

@team_management_bp.route('/<int:team_id>', methods=['DELETE'])
@login_required
@maritime_access_required(['manager'])
def delete_team(team_id):
    """
    Delete stevedore team (managers only)
    DELETE /api/maritime/teams/{id}
    """
    try:
        team = StevedoreTeam.query.get_or_404(team_id)
        team_data = team.to_dict()
        
        # Log deletion before removing
        SyncLog.log_action(
            user_id=current_user.id,
            action='delete',
            table_name='stevedore_teams',
            record_id=team_id,
            data_before=team_data
        )
        
        db = get_app_db()
        db.session.delete(team)
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('teams', '*'))
        
        logger.info(f"Stevedore team deleted: {team_id} by user {current_user.id}")
        
        return jsonify({'message': 'Team deleted successfully'})
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Delete team error: {e}")
        return jsonify({'error': 'Failed to delete team'}), 500

@team_management_bp.route('/vessel/<int:vessel_id>', methods=['GET'])
@login_required
@maritime_access_required()
def get_teams_by_vessel(vessel_id):
    """
    Get all teams assigned to a specific vessel
    GET /api/maritime/teams/vessel/{vessel_id}
    """
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        teams = StevedoreTeam.query.filter_by(vessel_id=vessel_id).all()
        
        # Build comprehensive vessel team data
        teams_data = []
        for team in teams:
            team_dict = team.to_dict()
            
            # Add member details
            member_ids = team.get_members()
            if member_ids:
                members = User.query.filter(User.id.in_(member_ids)).all()
                team_dict['member_details'] = [
                    {
                        'id': member.id,
                        'name': member.get_full_name(),
                        'role': getattr(member, 'maritime_role', member.role)
                    }
                    for member in members
                ]
            
            # Add shift status
            current_time = datetime.now().time()
            team_dict['shift_status'] = calculate_shift_status(team.shift_start, team.shift_end, current_time)
            
            teams_data.append(team_dict)
        
        # Calculate vessel team statistics
        team_stats = {
            'total_teams': len(teams),
            'total_personnel': sum(team.get_team_size() for team in teams),
            'teams_by_type': {},
            'active_shifts': 0
        }
        
        current_time = datetime.now().time()
        for team in teams:
            # Count by team type
            team_type = team.team_type or 'General'
            team_stats['teams_by_type'][team_type] = team_stats['teams_by_type'].get(team_type, 0) + 1
            
            # Count active shifts
            if is_team_on_shift(team.shift_start, team.shift_end, current_time):
                team_stats['active_shifts'] += 1
        
        return jsonify({
            'vessel_id': vessel_id,
            'vessel_name': vessel.name,
            'teams': teams_data,
            'team_statistics': team_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get teams by vessel error: {e}")
        return jsonify({'error': 'Failed to retrieve vessel teams'}), 500

@team_management_bp.route('/tico-vehicles', methods=['GET'])
@login_required
@maritime_access_required()
def get_tico_vehicles():
    """
    Get TICO vehicles for driver transport
    GET /api/maritime/teams/tico-vehicles?vessel_id=1&status=available
    """
    try:
        # Get query parameters
        vessel_id = request.args.get('vessel_id', type=int)
        status = request.args.get('status')
        
        # Build query
        query = TicoVehicle.query
        
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        if status:
            query = query.filter_by(status=status)
        
        # Order by availability and capacity
        query = query.order_by(TicoVehicle.status.asc(), TicoVehicle.capacity.desc())
        
        vehicles = query.all()
        vehicles_data = [vehicle.to_dict() for vehicle in vehicles]
        
        # Add optimization suggestions if driver count provided
        drivers_needed = request.args.get('drivers_needed', type=int)
        optimization_result = None
        
        if drivers_needed and vessel_id:
            optimization_result = MaritimeOperationsHelper.optimize_tico_assignments(vessel_id, drivers_needed)
        
        return jsonify({
            'tico_vehicles': vehicles_data,
            'optimization': optimization_result,
            'total_vehicles': len(vehicles),
            'available_vehicles': len([v for v in vehicles if v.is_available()]),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get TICO vehicles error: {e}")
        return jsonify({'error': 'Failed to retrieve TICO vehicles'}), 500

@team_management_bp.route('/tico-vehicles', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def create_tico_vehicle():
    """
    Create new TICO vehicle assignment
    POST /api/maritime/teams/tico-vehicles
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vessel_id', 'vehicle_type', 'vehicle_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate vessel exists
        vessel = Vessel.query.get(data['vessel_id'])
        if not vessel:
            return jsonify({'error': 'Vessel not found'}), 404
        
        # Validate driver if provided
        driver_id = data.get('driver_id')
        if driver_id and not User.query.get(driver_id):
            return jsonify({'error': 'Driver not found'}), 404
        
        # Create TICO vehicle
        tico_vehicle = TicoVehicle(
            vessel_id=data['vessel_id'],
            vehicle_type=data['vehicle_type'],
            vehicle_id=data['vehicle_id'],
            capacity=data.get('capacity', MaritimeOperationsHelper.TICO_VEHICLE_CAPACITY.get(data['vehicle_type'], 7)),
            driver_id=driver_id,
            status=data.get('status', 'available'),
            created_at=datetime.utcnow()
        )
        
        db = get_app_db()
        db.session.add(tico_vehicle)
        db.session.commit()
        
        # Log creation
        SyncLog.log_action(
            user_id=current_user.id,
            action='create',
            table_name='tico_vehicles',
            record_id=tico_vehicle.id,
            data_after=tico_vehicle.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tico_vehicles', '*'))
        
        logger.info(f"TICO vehicle created: {tico_vehicle.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'TICO vehicle created successfully',
            'tico_vehicle': tico_vehicle.to_dict()
        }), 201
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Create TICO vehicle error: {e}")
        return jsonify({'error': 'Failed to create TICO vehicle'}), 500

@team_management_bp.route('/analytics', methods=['GET'])
@login_required
@maritime_access_required()
def get_team_analytics():
    """
    Get team performance analytics
    GET /api/maritime/teams/analytics?vessel_id=1&hours=24
    """
    try:
        vessel_id = request.args.get('vessel_id', type=int)
        hours = request.args.get('hours', 24, type=int)
        
        # Build base query
        query = StevedoreTeam.query
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        
        teams = query.all()
        
        # Calculate analytics
        analytics = {
            'team_summary': {
                'total_teams': len(teams),
                'teams_by_type': {},
                'total_personnel': 0,
                'active_shifts': 0
            },
            'personnel_distribution': {},
            'shift_coverage': calculate_shift_coverage(teams),
            'vessel_assignments': {}
        }
        
        current_time = datetime.now().time()
        
        for team in teams:
            # Team type distribution
            team_type = team.team_type or 'General'
            analytics['team_summary']['teams_by_type'][team_type] = \
                analytics['team_summary']['teams_by_type'].get(team_type, 0) + 1
            
            # Personnel count
            analytics['team_summary']['total_personnel'] += team.get_team_size()
            
            # Active shifts
            if is_team_on_shift(team.shift_start, team.shift_end, current_time):
                analytics['team_summary']['active_shifts'] += 1
            
            # Vessel assignments
            if team.vessel:
                vessel_name = team.vessel.name
                if vessel_name not in analytics['vessel_assignments']:
                    analytics['vessel_assignments'][vessel_name] = {
                        'total_teams': 0,
                        'total_personnel': 0,
                        'team_types': []
                    }
                
                analytics['vessel_assignments'][vessel_name]['total_teams'] += 1
                analytics['vessel_assignments'][vessel_name]['total_personnel'] += team.get_team_size()
                if team_type not in analytics['vessel_assignments'][vessel_name]['team_types']:
                    analytics['vessel_assignments'][vessel_name]['team_types'].append(team_type)
        
        # Calculate personnel distribution by role
        all_member_ids = []
        for team in teams:
            if team.lead_id:
                all_member_ids.append(team.lead_id)
            if team.assistant_id:
                all_member_ids.append(team.assistant_id)
            all_member_ids.extend(team.get_members())
        
        if all_member_ids:
            personnel = User.query.filter(User.id.in_(all_member_ids)).all()
            for person in personnel:
                role = getattr(person, 'maritime_role', person.role)
                analytics['personnel_distribution'][role] = \
                    analytics['personnel_distribution'].get(role, 0) + 1
        
        return jsonify({
            'analytics': analytics,
            'query_params': {
                'vessel_id': vessel_id,
                'hours': hours
            },
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get team analytics error: {e}")
        return jsonify({'error': 'Failed to generate team analytics'}), 500

# Helper functions

def calculate_shift_status(shift_start, shift_end, current_time):
    """Calculate current shift status"""
    if not shift_start or not shift_end:
        return {
            'status': 'no_schedule',
            'description': 'No shift schedule defined'
        }
    
    if is_team_on_shift(shift_start, shift_end, current_time):
        return {
            'status': 'on_shift',
            'description': f'Currently on shift until {shift_end.strftime("%H:%M")}'
        }
    else:
        return {
            'status': 'off_shift',
            'description': f'Off shift - next shift starts at {shift_start.strftime("%H:%M")}'
        }

def is_team_on_shift(shift_start, shift_end, current_time):
    """Check if team is currently on shift"""
    if not shift_start or not shift_end:
        return False
    
    # Handle overnight shifts
    if shift_end < shift_start:
        return current_time >= shift_start or current_time <= shift_end
    else:
        return shift_start <= current_time <= shift_end

def calculate_team_performance(team_id):
    """Calculate team performance metrics (placeholder)"""
    # This would integrate with task completion data, discharge progress, etc.
    return {
        'tasks_completed': 0,
        'average_completion_time': 0,
        'efficiency_rating': 0,
        'note': 'Performance metrics integration pending'
    }

def calculate_shift_coverage(teams):
    """Calculate 24-hour shift coverage"""
    coverage = {}
    
    # Initialize hourly coverage
    for hour in range(24):
        coverage[f"{hour:02d}:00"] = {
            'teams_on_shift': 0,
            'personnel_count': 0,
            'team_types': []
        }
    
    for team in teams:
        if not team.shift_start or not team.shift_end:
            continue
        
        start_hour = team.shift_start.hour
        end_hour = team.shift_end.hour
        
        # Handle overnight shifts
        if end_hour < start_hour:
            # Shift spans midnight
            hours = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
        else:
            hours = list(range(start_hour, end_hour + 1))
        
        for hour in hours:
            hour_key = f"{hour:02d}:00"
            coverage[hour_key]['teams_on_shift'] += 1
            coverage[hour_key]['personnel_count'] += team.get_team_size()
            
            team_type = team.team_type or 'General'
            if team_type not in coverage[hour_key]['team_types']:
                coverage[hour_key]['team_types'].append(team_type)
    
    return coverage