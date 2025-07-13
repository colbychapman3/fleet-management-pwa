"""
Maritime Ship Operations API - 4-step wizard implementation
Handles vessel arrival, cargo manifest, team assignment, and berth allocation
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
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
    CargoOperation, StevedoreTeam, TicoVehicle, MaritimeDocument, 
    DischargeProgress, MaritimeOperationsHelper
)
from models.models.sync_log import SyncLog

logger = structlog.get_logger()

ship_operations_bp = Blueprint('ship_operations', __name__)

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

# Ship Operations Wizard API

@ship_operations_bp.route('/', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def create_ship_operation():
    """
    Step 1: Create new ship operation (vessel arrival)
    POST /api/maritime/ship-operations/
    """
    try:
        data = request.get_json()
        
        # Validate required fields for step 1
        required_fields = ['vessel_name', 'arrival_date', 'expected_duration']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if vessel already exists or create new one
        vessel = Vessel.query.filter_by(name=data['vessel_name']).first()
        if not vessel:
            vessel = Vessel(
                name=data['vessel_name'],
                vessel_type=data.get('vessel_type', 'cargo'),
                status='arriving',
                imo_number=data.get('imo_number'),
                call_sign=data.get('call_sign'),
                flag_state=data.get('flag_state'),
                gross_tonnage=data.get('gross_tonnage'),
                created_at=datetime.utcnow()
            )
        else:
            # Update existing vessel status
            vessel.status = 'arriving'
            vessel.updated_at = datetime.utcnow()
        
        # Parse arrival date
        try:
            arrival_date = datetime.fromisoformat(data['arrival_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid arrival_date format. Use ISO format.'}), 400
        
        # Update vessel with operation details
        vessel.arrival_date = arrival_date
        vessel.expected_duration = data.get('expected_duration')
        vessel.total_vehicles = data.get('total_vehicles', 0)
        vessel.expected_rate = data.get('expected_rate', 150)  # vehicles per hour
        vessel.port_of_origin = data.get('port_of_origin')
        vessel.next_port = data.get('next_port')
        vessel.agent_company = data.get('agent_company')
        vessel.operation_notes = data.get('operation_notes', '')
        
        # Set operation metadata
        operation_metadata = {
            'wizard_step': 1,
            'created_by': current_user.id,
            'operation_id': str(uuid.uuid4()),
            'step_1_completed': True,
            'step_2_completed': False,
            'step_3_completed': False,
            'step_4_completed': False
        }
        vessel.operation_metadata = json.dumps(operation_metadata)
        
        db = get_app_db()
        db.session.add(vessel)
        db.session.commit()
        
        # Log operation creation
        SyncLog.log_action(
            user_id=current_user.id,
            action='create',
            table_name='ship_operations',
            record_id=vessel.id,
            data_after=vessel.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('vessels', '*'))
        cache_delete(get_cache_key('ship_operations', '*'))
        
        logger.info(f"Ship operation created: {vessel.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Ship operation created successfully',
            'operation': {
                'vessel_id': vessel.id,
                'operation_id': operation_metadata['operation_id'],
                'wizard_step': 1,
                'next_step': 2,
                'vessel': vessel.to_dict()
            }
        }), 201
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Create ship operation error: {e}")
        return jsonify({'error': 'Failed to create ship operation'}), 500

@ship_operations_bp.route('/<int:vessel_id>', methods=['GET'])
@login_required
@maritime_access_required()
def get_ship_operation(vessel_id):
    """
    Get ship operation details with wizard progress
    GET /api/maritime/ship-operations/{id}
    """
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        
        # Get operation metadata
        operation_metadata = {}
        if vessel.operation_metadata:
            try:
                operation_metadata = json.loads(vessel.operation_metadata)
            except (json.JSONDecodeError, TypeError):
                operation_metadata = {}
        
        # Build comprehensive operation data
        operation_data = {
            'vessel': vessel.to_dict(),
            'wizard_progress': {
                'current_step': operation_metadata.get('wizard_step', 1),
                'step_1_completed': operation_metadata.get('step_1_completed', False),
                'step_2_completed': operation_metadata.get('step_2_completed', False),
                'step_3_completed': operation_metadata.get('step_3_completed', False),
                'step_4_completed': operation_metadata.get('step_4_completed', False),
                'operation_id': operation_metadata.get('operation_id'),
                'created_by': operation_metadata.get('created_by')
            },
            'cargo_operations': [co.to_dict() for co in vessel.cargo_operations] if hasattr(vessel, 'cargo_operations') else [],
            'stevedore_teams': [st.to_dict() for st in vessel.stevedore_teams] if hasattr(vessel, 'stevedore_teams') else [],
            'tico_vehicles': [tv.to_dict() for tv in vessel.tico_vehicles] if hasattr(vessel, 'tico_vehicles') else [],
            'discharge_progress': [dp.to_dict() for dp in vessel.discharge_progress] if hasattr(vessel, 'discharge_progress') else [],
            'maritime_documents': [md.to_dict() for md in vessel.maritime_documents] if hasattr(vessel, 'maritime_documents') else []
        }
        
        # Add zone summary
        operation_data['zone_summary'] = MaritimeOperationsHelper.get_zone_summary(vessel_id)
        
        # Add estimated completion
        estimated_completion = MaritimeOperationsHelper.calculate_estimated_completion(vessel_id)
        operation_data['estimated_completion'] = estimated_completion.isoformat() if estimated_completion else None
        
        return jsonify(operation_data)
        
    except Exception as e:
        logger.error(f"Get ship operation error: {e}")
        return jsonify({'error': 'Failed to retrieve ship operation'}), 500

@ship_operations_bp.route('/<int:vessel_id>/step/<int:step>', methods=['PUT'])
@login_required
@maritime_access_required()
def update_wizard_step(vessel_id, step):
    """
    Update specific wizard step
    PUT /api/maritime/ship-operations/{id}/step/{step}
    """
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        data = request.get_json()
        
        # Get current operation metadata
        operation_metadata = {}
        if vessel.operation_metadata:
            try:
                operation_metadata = json.loads(vessel.operation_metadata)
            except (json.JSONDecodeError, TypeError):
                operation_metadata = {}
        
        db = get_app_db()
        
        if step == 2:
            # Step 2: Cargo Manifest Processing
            return process_step_2_cargo_manifest(vessel, data, operation_metadata, db)
        elif step == 3:
            # Step 3: Team Assignment
            return process_step_3_team_assignment(vessel, data, operation_metadata, db)
        elif step == 4:
            # Step 4: Berth Allocation
            return process_step_4_berth_allocation(vessel, data, operation_metadata, db)
        else:
            return jsonify({'error': f'Invalid step: {step}'}), 400
            
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Update wizard step error: {e}")
        return jsonify({'error': f'Failed to update step {step}'}), 500

def process_step_2_cargo_manifest(vessel, data, operation_metadata, db):
    """Process Step 2: Cargo Manifest and Vehicle Data"""
    required_fields = ['cargo_manifest']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required for step 2'}), 400
    
    cargo_manifest = data['cargo_manifest']
    
    # Clear existing cargo operations for this vessel
    CargoOperation.query.filter_by(vessel_id=vessel.id).delete()
    
    # Process cargo manifest data
    for cargo_item in cargo_manifest:
        cargo_op = CargoOperation(
            vessel_id=vessel.id,
            zone=cargo_item.get('zone', 'General'),
            vehicle_type=cargo_item.get('vehicle_type'),
            quantity=cargo_item.get('quantity', 0),
            discharged=cargo_item.get('discharged', 0),
            location=cargo_item.get('location', '')
        )
        db.session.add(cargo_op)
    
    # Update vessel totals
    vessel.total_vehicles = sum(item.get('quantity', 0) for item in cargo_manifest)
    
    # Update operation metadata
    operation_metadata.update({
        'wizard_step': 2,
        'step_2_completed': True,
        'step_2_data': {
            'manifest_processed': True,
            'total_cargo_items': len(cargo_manifest),
            'processed_at': datetime.utcnow().isoformat()
        }
    })
    vessel.operation_metadata = json.dumps(operation_metadata)
    
    db.session.commit()
    
    logger.info(f"Step 2 completed for vessel {vessel.id}: cargo manifest processed")
    
    return jsonify({
        'message': 'Cargo manifest processed successfully',
        'step': 2,
        'next_step': 3,
        'cargo_operations': [co.to_dict() for co in vessel.cargo_operations]
    })

def process_step_3_team_assignment(vessel, data, operation_metadata, db):
    """Process Step 3: Stevedore Team Assignment"""
    required_fields = ['teams']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required for step 3'}), 400
    
    teams_data = data['teams']
    
    # Clear existing team assignments for this vessel
    StevedoreTeam.query.filter_by(vessel_id=vessel.id).delete()
    
    # Process team assignments
    teams_created = []
    for team_data in teams_data:
        team = StevedoreTeam(
            vessel_id=vessel.id,
            team_type=team_data.get('team_type', 'General'),
            lead_id=team_data.get('lead_id'),
            assistant_id=team_data.get('assistant_id'),
            shift_start=datetime.strptime(team_data['shift_start'], '%H:%M').time() if team_data.get('shift_start') else None,
            shift_end=datetime.strptime(team_data['shift_end'], '%H:%M').time() if team_data.get('shift_end') else None
        )
        
        # Set team members
        if team_data.get('members'):
            team.set_members(team_data['members'])
        
        db.session.add(team)
        teams_created.append(team)
    
    # Process TICO vehicle assignments if provided
    if data.get('tico_vehicles'):
        TicoVehicle.query.filter_by(vessel_id=vessel.id).delete()
        
        for tico_data in data['tico_vehicles']:
            tico_vehicle = TicoVehicle(
                vessel_id=vessel.id,
                vehicle_type=tico_data.get('vehicle_type', 'Van'),
                vehicle_id=tico_data.get('vehicle_id'),
                capacity=tico_data.get('capacity', 7),
                driver_id=tico_data.get('driver_id'),
                status=tico_data.get('status', 'available')
            )
            db.session.add(tico_vehicle)
    
    # Update operation metadata
    operation_metadata.update({
        'wizard_step': 3,
        'step_3_completed': True,
        'step_3_data': {
            'teams_assigned': len(teams_data),
            'tico_vehicles_assigned': len(data.get('tico_vehicles', [])),
            'processed_at': datetime.utcnow().isoformat()
        }
    })
    vessel.operation_metadata = json.dumps(operation_metadata)
    
    db.session.commit()
    
    logger.info(f"Step 3 completed for vessel {vessel.id}: teams assigned")
    
    return jsonify({
        'message': 'Team assignments completed successfully',
        'step': 3,
        'next_step': 4,
        'teams': [team.to_dict() for team in teams_created],
        'tico_vehicles': [tv.to_dict() for tv in vessel.tico_vehicles] if hasattr(vessel, 'tico_vehicles') else []
    })

def process_step_4_berth_allocation(vessel, data, operation_metadata, db):
    """Process Step 4: Berth Allocation and Final Setup"""
    required_fields = ['berth_assignment']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required for step 4'}), 400
    
    berth_data = data['berth_assignment']
    
    # Update vessel with berth information
    vessel.berth_number = berth_data.get('berth_number')
    vessel.berth_location = berth_data.get('berth_location')
    vessel.berth_side = berth_data.get('berth_side', 'port')
    vessel.status = 'berthed'
    
    # Set operation start time
    if berth_data.get('operation_start_time'):
        try:
            vessel.operation_start = datetime.fromisoformat(berth_data['operation_start_time'].replace('Z', '+00:00'))
        except ValueError:
            vessel.operation_start = datetime.utcnow()
    else:
        vessel.operation_start = datetime.utcnow()
    
    # Update operation metadata
    operation_metadata.update({
        'wizard_step': 4,
        'step_4_completed': True,
        'operation_complete': True,
        'step_4_data': {
            'berth_allocated': True,
            'berth_number': vessel.berth_number,
            'operation_start': vessel.operation_start.isoformat(),
            'processed_at': datetime.utcnow().isoformat()
        }
    })
    vessel.operation_metadata = json.dumps(operation_metadata)
    
    # Create initial discharge progress entry
    initial_progress = DischargeProgress(
        vessel_id=vessel.id,
        zone='All',
        timestamp=datetime.utcnow(),
        vehicles_discharged=0,
        hourly_rate=0.0,
        total_progress=0.0,
        created_by=current_user.id
    )
    db.session.add(initial_progress)
    
    db.session.commit()
    
    # Clear relevant caches
    cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
    cache_delete(get_cache_key('vessels', '*'))
    cache_delete(get_cache_key('ship_operations', '*'))
    
    logger.info(f"Step 4 completed for vessel {vessel.id}: operation fully configured")
    
    return jsonify({
        'message': 'Ship operation setup completed successfully',
        'step': 4,
        'operation_complete': True,
        'vessel': vessel.to_dict(),
        'next_actions': [
            'Begin cargo discharge tracking',
            'Monitor team performance',
            'Update discharge progress regularly'
        ]
    })

@ship_operations_bp.route('/', methods=['GET'])
@login_required
@maritime_access_required()
def list_ship_operations():
    """
    Get list of all ship operations with filtering
    GET /api/maritime/ship-operations/?status=active&page=1&per_page=20
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')  # active, completed, all
        vessel_name = request.args.get('vessel_name')
        
        # Build query
        query = Vessel.query
        
        # Apply status filter
        if status == 'active':
            query = query.filter(Vessel.status.in_(['arriving', 'berthed', 'discharging']))
        elif status == 'completed':
            query = query.filter(Vessel.status.in_(['departed', 'completed']))
        
        # Apply vessel name filter
        if vessel_name:
            query = query.filter(Vessel.name.ilike(f'%{vessel_name}%'))
        
        # Only show vessels with operation metadata (ship operations)
        query = query.filter(Vessel.operation_metadata.isnot(None))
        
        # Order by arrival date (most recent first)
        query = query.order_by(Vessel.arrival_date.desc())
        
        # Paginate
        vessels_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Build response with operation summaries
        operations = []
        for vessel in vessels_paginated.items:
            operation_metadata = {}
            if vessel.operation_metadata:
                try:
                    operation_metadata = json.loads(vessel.operation_metadata)
                except (json.JSONDecodeError, TypeError):
                    operation_metadata = {}
            
            operation_summary = {
                'vessel': vessel.to_dict(),
                'wizard_progress': {
                    'current_step': operation_metadata.get('wizard_step', 1),
                    'operation_complete': operation_metadata.get('operation_complete', False),
                    'operation_id': operation_metadata.get('operation_id')
                },
                'summary_stats': {
                    'total_vehicles': vessel.total_vehicles or 0,
                    'estimated_completion': MaritimeOperationsHelper.calculate_estimated_completion(vessel.id).isoformat() if MaritimeOperationsHelper.calculate_estimated_completion(vessel.id) else None
                }
            }
            
            # Add latest progress if available
            latest_progress = DischargeProgress.get_latest_progress_by_vessel(vessel.id)
            if latest_progress:
                operation_summary['latest_progress'] = latest_progress.to_dict()
            
            operations.append(operation_summary)
        
        return jsonify({
            'operations': operations,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': vessels_paginated.total,
                'pages': vessels_paginated.pages,
                'has_next': vessels_paginated.has_next,
                'has_prev': vessels_paginated.has_prev
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"List ship operations error: {e}")
        return jsonify({'error': 'Failed to retrieve ship operations'}), 500

@ship_operations_bp.route('/<int:vessel_id>', methods=['DELETE'])
@login_required
@maritime_access_required(['manager'])
def delete_ship_operation(vessel_id):
    """
    Delete ship operation (managers only)
    DELETE /api/maritime/ship-operations/{id}
    """
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        
        # Store data for logging
        vessel_data = vessel.to_dict()
        
        # Delete related maritime data
        CargoOperation.query.filter_by(vessel_id=vessel_id).delete()
        StevedoreTeam.query.filter_by(vessel_id=vessel_id).delete()
        TicoVehicle.query.filter_by(vessel_id=vessel_id).delete()
        DischargeProgress.query.filter_by(vessel_id=vessel_id).delete()
        MaritimeDocument.query.filter_by(vessel_id=vessel_id).delete()
        
        # Log deletion before removing vessel
        SyncLog.log_action(
            user_id=current_user.id,
            action='delete',
            table_name='ship_operations',
            record_id=vessel_id,
            data_before=vessel_data
        )
        
        db = get_app_db()
        db.session.delete(vessel)
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('vessels', '*'))
        cache_delete(get_cache_key('ship_operations', '*'))
        
        logger.info(f"Ship operation deleted: {vessel_id} by user {current_user.id}")
        
        return jsonify({'message': 'Ship operation deleted successfully'})
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Delete ship operation error: {e}")
        return jsonify({'error': 'Failed to delete ship operation'}), 500