"""
Maritime Operations API routes
Real-time operations management endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import structlog

def get_app_db():
    import app
    return app.db

from models.maritime.ship_operation import ShipOperation
from models.maritime.stevedore_team import StevedoreTeam
from models.maritime.cargo_discharge import CargoDischarge
from models.models.vessel import Vessel

logger = structlog.get_logger()

operations_api_bp = Blueprint('operations_api', __name__, url_prefix='/api/maritime')

@operations_api_bp.route('/operations/active', methods=['GET'])
@login_required
def get_active_operations():
    """Get all active ship operations"""
    try:
        operations = ShipOperation.get_active_operations()
        return jsonify([op.to_dict() for op in operations])
    except Exception as e:
        logger.error(f"Error fetching active operations: {e}")
        return jsonify({'error': 'Failed to fetch operations'}), 500

@operations_api_bp.route('/operations/<int:operation_id>', methods=['GET'])
@login_required
def get_operation_details(operation_id):
    """Get detailed information about a specific operation"""
    try:
        operation = ShipOperation.query.get_or_404(operation_id)
        return jsonify(operation.to_dict())
    except Exception as e:
        logger.error(f"Error fetching operation {operation_id}: {e}")
        return jsonify({'error': 'Failed to fetch operation details'}), 500

@operations_api_bp.route('/operations/<int:operation_id>/update', methods=['POST'])
@login_required
def update_operation(operation_id):
    """Update operation progress and status"""
    if not current_user.is_manager():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db = get_app_db()
        operation = ShipOperation.query.get_or_404(operation_id)
        data = request.get_json()
        
        # Update operation based on current step
        current_step = data.get('current_step', operation.current_step)
        
        if current_step == 1:
            operation.complete_step_1(**data.get('step_1_data', {}))
        elif current_step == 2:
            operation.complete_step_2(**data.get('step_2_data', {}))
        elif current_step == 3:
            operation.complete_step_3(**data.get('step_3_data', {}))
        elif current_step == 4:
            operation.complete_step_4(**data.get('step_4_data', {}))
        
        # Update general operation data
        if 'priority' in data:
            operation.priority = data['priority']
        if 'status' in data:
            operation.status = data['status']
        
        db.session.commit()
        
        # Broadcast update via WebSocket (if implemented)
        # broadcast_operation_update(operation)
        
        return jsonify({
            'success': True,
            'operation': operation.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating operation {operation_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update operation'}), 500

@operations_api_bp.route('/berths/status', methods=['GET'])
@login_required
def get_berth_status():
    """Get current status of all berths"""
    try:
        # Initialize berth status
        berth_status = {
            '1': {'status': 'available', 'vessel': None, 'operation': None},
            '2': {'status': 'available', 'vessel': None, 'operation': None},
            '3': {'status': 'available', 'vessel': None, 'operation': None}
        }
        
        # Get active operations with berth assignments
        active_operations = ShipOperation.query.filter(
            ShipOperation.status.in_(['initiated', 'in_progress']),
            ShipOperation.berth_assigned.isnot(None)
        ).all()
        
        # Update berth status based on active operations
        for operation in active_operations:
            berth_number = str(operation.berth_assigned)
            if berth_number in berth_status:
                berth_status[berth_number] = {
                    'status': 'occupied',
                    'vessel': {
                        'id': operation.vessel.id,
                        'name': operation.vessel.name,
                        'vessel_type': operation.vessel.vessel_type,
                        'imo_number': operation.vessel.imo_number
                    } if operation.vessel else None,
                    'operation': {
                        'id': operation.id,
                        'operation_id': operation.operation_id,
                        'progress_percentage': operation.get_progress_percentage(),
                        'current_step': operation.current_step,
                        'eta': operation.arrival_datetime.isoformat() if operation.arrival_datetime else None,
                        'priority': operation.priority
                    }
                }
        
        return jsonify(berth_status)
        
    except Exception as e:
        logger.error(f"Error fetching berth status: {e}")
        return jsonify({'error': 'Failed to fetch berth status'}), 500

@operations_api_bp.route('/berths/assign', methods=['POST'])
@login_required
def assign_berth():
    """Assign a vessel to a berth"""
    if not current_user.is_manager():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db = get_app_db()
        data = request.get_json()
        vessel_id = data.get('vessel_id')
        berth_number = data.get('berth_number')
        
        if not vessel_id or not berth_number:
            return jsonify({'error': 'Missing vessel_id or berth_number'}), 400
        
        # Find operation for this vessel
        operation = ShipOperation.query.filter_by(
            vessel_id=vessel_id,
            status='initiated'
        ).first()
        
        if not operation:
            return jsonify({'error': 'No active operation found for vessel'}), 404
        
        # Check if berth is available
        existing_operation = ShipOperation.query.filter_by(
            berth_assigned=berth_number,
            status='in_progress'
        ).first()
        
        if existing_operation:
            return jsonify({'error': f'Berth {berth_number} is already occupied'}), 409
        
        # Assign berth
        operation.berth_assigned = berth_number
        operation.berth_assignment_time = datetime.utcnow()
        operation.status = 'in_progress'
        operation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Vessel assigned to berth {berth_number}',
            'operation': operation.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error assigning berth: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to assign berth'}), 500

@operations_api_bp.route('/teams/performance', methods=['GET'])
@login_required
def get_team_performance():
    """Get performance data for all active teams"""
    try:
        teams = StevedoreTeam.get_active_teams()
        team_data = []
        
        for team in teams:
            team_data.append({
                'id': team.id,
                'team_name': team.team_name,
                'status': team.status,
                'cargo_processed_today': team.get_cargo_processed_today(),
                'efficiency_rating': team.get_efficiency_rating(),
                'active_members_count': team.get_active_members_count(),
                'current_operation': team.get_current_operation(),
                'zone_assignment': team.zone_assignment,
                'shift_pattern': team.shift_pattern
            })
        
        return jsonify(team_data)
        
    except Exception as e:
        logger.error(f"Error fetching team performance: {e}")
        return jsonify({'error': 'Failed to fetch team performance'}), 500

@operations_api_bp.route('/kpis', methods=['GET'])
@login_required
def get_kpis():
    """Get current maritime KPIs"""
    try:
        # Calculate real-time KPIs
        active_operations = ShipOperation.get_active_operations()
        total_operations = len(active_operations)
        
        # Berth utilization
        occupied_berths = len([op for op in active_operations if op.berth_assigned])
        berth_utilization = round((occupied_berths / 3) * 100)
        
        # Cargo throughput (mock calculation)
        today = datetime.utcnow().date()
        completed_today = ShipOperation.query.filter(
            ShipOperation.status == 'completed',
            ShipOperation.updated_at >= datetime.combine(today, datetime.min.time())
        ).count()
        
        # Average turnaround time (mock calculation)
        avg_turnaround = 18  # hours
        
        kpis = {
            'active-operations': total_operations,
            'berth-utilization': berth_utilization,
            'cargo-throughput': 450,  # MT/hr (mock)
            'avg-turnaround': avg_turnaround
        }
        
        return jsonify(kpis)
        
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
        return jsonify({'error': 'Failed to calculate KPIs'}), 500

@operations_api_bp.route('/alerts/active', methods=['GET'])
@login_required
def get_active_alerts():
    """Get current active alerts"""
    try:
        alerts = []
        
        # Check for overdue operations
        overdue_operations = ShipOperation.get_overdue_operations()
        for operation in overdue_operations:
            alerts.append({
                'id': f'overdue_{operation.id}',
                'title': 'Overdue Operation',
                'message': f'Operation {operation.operation_id} is overdue',
                'severity': 'warning',
                'icon': 'clock',
                'created_at': operation.created_at.isoformat(),
                'operation_id': operation.id
            })
        
        # Check for high priority operations without berth
        unassigned_priority = ShipOperation.query.filter(
            ShipOperation.priority.in_(['high', 'urgent']),
            ShipOperation.berth_assigned.is_(None),
            ShipOperation.status == 'initiated'
        ).all()
        
        for operation in unassigned_priority:
            alerts.append({
                'id': f'unassigned_{operation.id}',
                'title': 'High Priority Vessel Waiting',
                'message': f'{operation.vessel.name} requires urgent berth assignment',
                'severity': 'critical' if operation.priority == 'urgent' else 'warning',
                'icon': 'alert-triangle',
                'created_at': operation.created_at.isoformat(),
                'operation_id': operation.id
            })
        
        # Check for team performance issues
        underperforming_teams = StevedoreTeam.query.filter(
            StevedoreTeam.productivity_rating < 6.0,
            StevedoreTeam.status == 'assigned'
        ).all()
        
        for team in underperforming_teams:
            alerts.append({
                'id': f'team_performance_{team.id}',
                'title': 'Team Performance Alert',
                'message': f'{team.team_name} efficiency below threshold',
                'severity': 'info',
                'icon': 'users',
                'created_at': team.updated_at.isoformat() if team.updated_at else team.created_at.isoformat(),
                'team_id': team.id
            })
        
        return jsonify(alerts)
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({'error': 'Failed to fetch alerts'}), 500

@operations_api_bp.route('/alerts/<alert_id>/dismiss', methods=['POST'])
@login_required
def dismiss_alert(alert_id):
    """Dismiss a specific alert"""
    try:
        # In a real implementation, you would update an alerts table
        # For now, just return success
        return jsonify({'success': True, 'message': 'Alert dismissed'})
    except Exception as e:
        logger.error(f"Error dismissing alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to dismiss alert'}), 500

@operations_api_bp.route('/alerts/mark-all-read', methods=['POST'])
@login_required
def mark_all_alerts_read():
    """Mark all alerts as read"""
    try:
        # In a real implementation, you would update alerts table
        return jsonify({'success': True, 'message': 'All alerts marked as read'})
    except Exception as e:
        logger.error(f"Error marking alerts as read: {e}")
        return jsonify({'error': 'Failed to mark alerts as read'}), 500

@operations_api_bp.route('/operations/create', methods=['POST'])
@login_required
def create_operation():
    """Create a new ship operation"""
    if not current_user.is_manager():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db = get_app_db()
        data = request.get_json()
        
        vessel_id = data.get('vessel_id')
        operation_type = data.get('operation_type', 'discharge')
        
        if not vessel_id:
            return jsonify({'error': 'vessel_id is required'}), 400
        
        vessel = Vessel.query.get(vessel_id)
        if not vessel:
            return jsonify({'error': 'Vessel not found'}), 404
        
        # Generate operation ID
        operation_id = ShipOperation.generate_operation_id(vessel.name, operation_type)
        
        # Create new operation
        operation = ShipOperation(
            operation_id=operation_id,
            vessel_id=vessel_id,
            operation_type=operation_type,
            status='initiated',
            priority=data.get('priority', 'medium'),
            operation_manager_id=current_user.id,
            cargo_type=data.get('cargo_type'),
            total_cargo_quantity=data.get('total_cargo_quantity'),
            zone_assignment=data.get('zone_assignment')
        )
        
        db.session.add(operation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Operation created successfully',
            'operation': operation.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating operation: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create operation'}), 500

@operations_api_bp.route('/operations/<int:operation_id>/cargo/update', methods=['POST'])
@login_required
def update_cargo_progress(operation_id):
    """Update cargo processing progress"""
    try:
        db = get_app_db()
        operation = ShipOperation.query.get_or_404(operation_id)
        data = request.get_json()
        
        processed_quantity = data.get('processed_quantity')
        if processed_quantity is None:
            return jsonify({'error': 'processed_quantity is required'}), 400
        
        operation.update_cargo_progress(processed_quantity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'operation': operation.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating cargo progress: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update cargo progress'}), 500

@operations_api_bp.route('/teams/<int:team_id>/assign', methods=['POST'])
@login_required
def assign_team_to_operation(team_id):
    """Assign a stevedore team to an operation"""
    if not current_user.is_manager():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db = get_app_db()
        data = request.get_json()
        operation_id = data.get('operation_id')
        
        if not operation_id:
            return jsonify({'error': 'operation_id is required'}), 400
        
        team = StevedoreTeam.query.get_or_404(team_id)
        operation = ShipOperation.query.get_or_404(operation_id)
        
        if not team.is_available_for_assignment():
            return jsonify({'error': 'Team is not available for assignment'}), 409
        
        # Assign team to operation
        operation.stevedore_team_id = team_id
        team.assign_to_operation(f"{operation.vessel.name} - {operation.operation_type}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Team {team.team_name} assigned to operation',
            'operation': operation.to_dict(),
            'team': team.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error assigning team: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to assign team'}), 500

@operations_api_bp.route('/dashboard/summary', methods=['GET'])
@login_required
def get_dashboard_summary():
    """Get complete dashboard summary data"""
    try:
        # Get all required data in one endpoint for efficiency
        active_operations = ShipOperation.get_active_operations()
        active_teams = StevedoreTeam.get_active_teams()
        
        # Calculate KPIs
        total_operations = len(active_operations)
        occupied_berths = len([op for op in active_operations if op.berth_assigned])
        berth_utilization = round((occupied_berths / 3) * 100)
        
        # Berth status
        berth_status = {}
        for i in range(1, 4):
            berth_status[f'berth_{i}'] = {'status': 'available', 'vessel': None, 'progress': 0}
        
        for operation in active_operations:
            if operation.berth_assigned:
                berth_key = f"berth_{operation.berth_assigned}"
                if berth_key in berth_status:
                    berth_status[berth_key] = {
                        'status': 'occupied',
                        'vessel': operation.vessel,
                        'eta': operation.arrival_datetime,
                        'progress': operation.get_progress_percentage()
                    }
        
        # Vessel queue
        vessel_queue = [
            {
                'id': op.vessel.id,
                'name': op.vessel.name,
                'eta': op.arrival_datetime,
                'cargo_type': op.cargo_type or 'General',
                'operation_id': op.operation_id
            }
            for op in active_operations if not op.berth_assigned
        ]
        
        summary = {
            'kpis': {
                'active_operations': total_operations,
                'berth_utilization': berth_utilization,
                'berths_occupied': occupied_berths,
                'cargo_throughput': 450,  # Mock data
                'avg_turnaround': 18
            },
            'berth_status': berth_status,
            'active_operations': [op.to_dict() for op in active_operations],
            'vessel_queue': vessel_queue,
            'active_teams': [
                {
                    'id': team.id,
                    'team_name': team.team_name,
                    'status': team.status,
                    'cargo_processed_today': team.get_cargo_processed_today(),
                    'efficiency_rating': team.get_efficiency_rating(),
                    'active_members_count': team.get_active_members_count(),
                    'current_operation': team.get_current_operation()
                }
                for team in active_teams
            ],
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}")
        return jsonify({'error': 'Failed to fetch dashboard summary'}), 500