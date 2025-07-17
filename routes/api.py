"""
API routes for data management and synchronization
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import structlog

# Access app components via current_app or direct import
def get_app_db():
    import app
    return app.db

def get_cache_functions():
    import app
    return app.cache_get, app.cache_set, app.cache_delete, app.get_cache_key
from models.models.user import User
from models.models.vessel import Vessel
from models.models.task import Task
from models.models.sync_log import SyncLog
from models.models.maritime_models import (
    CargoOperation, StevedoreTeam, MaritimeDocument,
    DischargeProgress, MaritimeOperationsHelper
)
from models.models.tico_vehicle import (
    TicoVehicle, TicoVehicleAssignment, TicoVehicleLocation, TicoRouteOptimizer
)
from models.maritime.maritime_operation import MaritimeOperation
from models.models.alert import Alert, AlertGenerator

logger = structlog.get_logger()

api_bp = Blueprint('api', __name__)

# Maritime role validation decorator
def maritime_access_required(required_roles=None):
    """Decorator to check maritime-specific role permissions"""
    if required_roles is None:
        required_roles = ['manager', 'maritime_supervisor', 'stevedore_lead', 'worker']
    
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

# Tasks API
@api_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get tasks with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        vessel_id = request.args.get('vessel_id', type=int)
        assigned_to = request.args.get('assigned_to', type=int)
        priority = request.args.get('priority')
        overdue_only = request.args.get('overdue', 'false').lower() == 'true'
        
        # Get cache functions first
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        
        # Build cache key
        cache_key = get_cache_key(
            'tasks', current_user.id, page, per_page, status, 
            vessel_id, assigned_to, priority, overdue_only
        )
        
        # Try cache first
        cached_result = cache_get(cache_key)
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        # Build query
        query = Task.query
        
        # Apply filters based on user role
        if current_user.is_worker():
            # Workers only see their own tasks or unassigned tasks on their vessel
            if current_user.vessel_id:
                db = get_app_db()
                query = query.filter(
                    db.or_(
                        Task.assigned_to_id == current_user.id,
                        db.and_(
                            Task.vessel_id == current_user.vessel_id,
                            Task.assigned_to_id.is_(None)
                        )
                    )
                )
            else:
                query = query.filter_by(assigned_to_id=current_user.id)
        
        # Apply additional filters
        if status:
            query = query.filter_by(status=status)
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        if assigned_to:
            query = query.filter_by(assigned_to_id=assigned_to)
        if priority:
            query = query.filter_by(priority=priority)
        if overdue_only:
            query = query.filter(
                Task.status.in_(['pending', 'in_progress']),
                Task.due_date < datetime.utcnow()
            )
        
        # Order by due date and priority
        query = query.order_by(Task.due_date.asc(), Task.priority.desc())
        
        # Paginate
        tasks_paginated = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'tasks': [task.to_dict() for task in tasks_paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': tasks_paginated.total,
                'pages': tasks_paginated.pages,
                'has_next': tasks_paginated.has_next,
                'has_prev': tasks_paginated.has_prev
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        cache_set(cache_key, json.dumps(result), timeout=300)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get tasks error: {e}")
        return jsonify({'error': 'Failed to retrieve tasks'}), 500

@api_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'task_type']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create task
        task = Task(
            title=data['title'].strip(),
            description=data.get('description', '').strip(),
            priority=data.get('priority', 'medium'),
            task_type=data['task_type'].strip(),
            created_by_id=current_user.id,
            assigned_to_id=data.get('assigned_to_id'),
            vessel_id=data.get('vessel_id'),
            location=data.get('location', '').strip(),
            equipment=data.get('equipment', '').strip(),
            estimated_hours=data.get('estimated_hours'),
            local_id=data.get('local_id', str(uuid.uuid4()))
        )
        
        # Set due date if provided
        if data.get('due_date'):
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid due_date format'}), 400
        
        db = get_app_db()
        db.session.add(task)
        db.session.commit()
        
        # Log sync action
        SyncLog.log_action(
            user_id=current_user.id,
            action='create',
            table_name='tasks',
            record_id=task.id,
            local_id=task.local_id,
            data_after=task.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tasks', current_user.id, '*'))
        
        logger.info(f"Task created: {task.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Create task error: {e}")
        return jsonify({'error': 'Failed to create task'}), 500

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """Get a specific task"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Check permissions
        if current_user.is_worker():
            if (task.assigned_to_id != current_user.id and 
                task.vessel_id != current_user.vessel_id):
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(task.to_dict())
        
    except Exception as e:
        logger.error(f"Get task error: {e}")
        return jsonify({'error': 'Failed to retrieve task'}), 500

@api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update a task"""
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        # Check permissions
        if current_user.is_worker():
            if (task.assigned_to_id != current_user.id and 
                task.vessel_id != current_user.vessel_id):
                return jsonify({'error': 'Access denied'}), 403
        
        # Store original data for sync log
        original_data = task.to_dict()
        
        # Update allowed fields
        updatable_fields = [
            'title', 'description', 'priority', 'status', 'location', 
            'equipment', 'estimated_hours', 'actual_hours', 
            'completion_notes', 'completion_photos'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(task, field, data[field])
        
        # Only managers can reassign tasks
        if current_user.is_manager() and 'assigned_to_id' in data:
            task.assigned_to_id = data['assigned_to_id']
        
        # Handle due date
        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid due_date format'}), 400
            else:
                task.due_date = None
        
        # Auto-complete if status is completed
        if data.get('status') == 'completed' and task.status != 'completed':
            task.completion_date = datetime.utcnow()
        
        task.updated_at = datetime.utcnow()
        task.is_synced = False  # Mark as needing sync
        
        db = get_app_db()
        db.session.commit()
        
        # Log sync action
        SyncLog.log_action(
            user_id=current_user.id,
            action='update',
            table_name='tasks',
            record_id=task.id,
            data_before=original_data,
            data_after=task.to_dict()
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tasks', '*'))
        
        logger.info(f"Task updated: {task.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Update task error: {e}")
        return jsonify({'error': 'Failed to update task'}), 500

@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task (managers only)"""
    if not current_user.is_manager():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        task = Task.query.get_or_404(task_id)
        task_data = task.to_dict()
        
        # Log sync action before deletion
        SyncLog.log_action(
            user_id=current_user.id,
            action='delete',
            table_name='tasks',
            record_id=task.id,
            data_before=task_data
        )
        
        db = get_app_db()
        db.session.delete(task)
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tasks', '*'))
        
        logger.info(f"Task deleted: {task_id} by user {current_user.id}")
        
        return jsonify({'message': 'Task deleted successfully'})
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Delete task error: {e}")
        return jsonify({'error': 'Failed to delete task'}), 500

# Vessels API
@api_bp.route('/vessels', methods=['GET'])
@login_required
def get_vessels():
    """Get vessels list"""
    try:
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_key = get_cache_key('vessels', 'all')
        cached_result = cache_get(cache_key)
        
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        vessels = Vessel.get_active_vessels()
        result = {
            'vessels': [vessel.to_dict() for vessel in vessels],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 15 minutes
        cache_set(cache_key, json.dumps(result), timeout=900)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get vessels error: {e}")
        return jsonify({'error': 'Failed to retrieve vessels'}), 500

@api_bp.route('/vessels/<int:vessel_id>', methods=['GET'])
@login_required
def get_vessel(vessel_id):
    """Get a specific vessel"""
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        return jsonify(vessel.to_dict())
        
    except Exception as e:
        logger.error(f"Get vessel error: {e}")
        return jsonify({'error': 'Failed to retrieve vessel'}), 500

# Users API (for managers)
@api_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """Get users list (managers only)"""
    if not current_user.is_manager():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_key = get_cache_key('users', 'all')
        cached_result = cache_get(cache_key)
        
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        users = User.query.filter_by(is_active=True).all()
        result = {
            'users': [user.to_dict() for user in users],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 10 minutes
        cache_set(cache_key, json.dumps(result), timeout=600)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({'error': 'Failed to retrieve users'}), 500

# Sync API
@api_bp.route('/sync', methods=['POST'])
@login_required
def sync_data():
    """Synchronize offline changes"""
    try:
        data = request.get_json()
        changes = data.get('changes', [])
        
        results = []
        
        for change in changes:
            try:
                if change['table'] == 'tasks':
                    result = sync_task_change(change)
                elif change['table'] == 'users':
                    result = sync_user_change(change)
                else:
                    result = {'status': 'error', 'message': f"Unknown table: {change['table']}"}
                
                results.append({
                    'change_id': change.get('id'),
                    'result': result
                })
                
            except Exception as e:
                results.append({
                    'change_id': change.get('id'),
                    'result': {'status': 'error', 'message': str(e)}
                })
        
        # Update user's last sync time
        current_user.update_last_sync()
        
        return jsonify({
            'message': 'Sync completed',
            'results': results,
            'sync_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return jsonify({'error': 'Sync failed'}), 500

def sync_task_change(change):
    """Handle task synchronization"""
    try:
        action = change['action']
        data = change['data']
        
        if action == 'create':
            # Check if task already exists by local_id
            existing_task = Task.query.filter_by(local_id=data.get('local_id')).first()
            if existing_task:
                return {'status': 'duplicate', 'server_id': existing_task.id}
            
            task = Task(**{k: v for k, v in data.items() if k in [
                'title', 'description', 'priority', 'status', 'task_type',
                'assigned_to_id', 'vessel_id', 'location', 'equipment',
                'estimated_hours', 'actual_hours', 'completion_notes',
                'completion_photos', 'local_id'
            ]})
            task.created_by_id = current_user.id
            
            if data.get('due_date'):
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            
            db = get_app_db()
            db.session.add(task)
            db.session.commit()
            
            return {'status': 'created', 'server_id': task.id}
            
        elif action == 'update':
            task = Task.query.get(change['server_id'])
            if not task:
                return {'status': 'error', 'message': 'Task not found'}
            
            # Update fields
            for field, value in data.items():
                if hasattr(task, field) and field not in ['id', 'created_at', 'created_by_id']:
                    setattr(task, field, value)
            
            task.updated_at = datetime.utcnow()
            db = get_app_db()
            db.session.commit()
            
            return {'status': 'updated'}
            
        elif action == 'delete':
            task = Task.query.get(change['server_id'])
            if task:
                db = get_app_db()
                db.session.delete(task)
                db.session.commit()
            
            return {'status': 'deleted'}
        
        return {'status': 'error', 'message': f"Unknown action: {action}"}
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

def sync_user_change(change):
    """Handle user synchronization (limited to profile updates)"""
    try:
        if change['action'] == 'update' and change.get('user_id') == current_user.id:
            data = change['data']
            
            # Only allow profile field updates
            allowed_fields = ['first_name', 'last_name', 'phone']
            for field in allowed_fields:
                if field in data:
                    setattr(current_user, field, data[field])
            
            db = get_app_db()
            db.session.commit()
            return {'status': 'updated'}
        
        return {'status': 'error', 'message': 'Unauthorized user change'}
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

# Dashboard statistics
@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_key = get_cache_key('dashboard_stats', current_user.id, current_user.role)
        cached_result = cache_get(cache_key)
        
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        stats = {}
        
        if current_user.is_manager():
            # Manager dashboard stats
            stats = {
                'tasks': Task.get_task_statistics(),
                'users': {
                    'total': User.get_active_users_count(),
                    'managers': len(User.get_managers()),
                    'workers': len(User.get_workers())
                },
                'vessels': {
                    'total': len(Vessel.get_active_vessels())
                },
                'overdue_tasks': len(Task.get_overdue_tasks())
            }
        else:
            # Worker dashboard stats
            user_tasks = Task.get_tasks_for_user(current_user.id)
            stats = {
                'my_tasks': {
                    'total': len(user_tasks),
                    'pending': len([t for t in user_tasks if t.status == 'pending']),
                    'in_progress': len([t for t in user_tasks if t.status == 'in_progress']),
                    'completed': len([t for t in user_tasks if t.status == 'completed']),
                    'overdue': len([t for t in user_tasks if t.is_overdue()])
                },
                'vessel': current_user.vessel.to_dict() if current_user.vessel else None
            }
        
        result = {
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        cache_set(cache_key, json.dumps(result), timeout=300)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({'error': 'Failed to retrieve dashboard statistics'}), 500

# Maritime Alerts API
@api_bp.route('/maritime/alerts/active', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_active_alerts():
    """Get active maritime operation alerts"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        severity = request.args.get('severity')
        alert_type = request.args.get('type')
        
        # Get cache functions
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        
        # Build cache key
        cache_key = get_cache_key('maritime_alerts', current_user.id, limit, severity, alert_type)
        
        # Try cache first
        cached_result = cache_get(cache_key)
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        # Get alerts based on filters
        if severity:
            alerts = Alert.get_alerts_by_severity(severity, limit)
        elif alert_type:
            alerts = Alert.get_alerts_by_type(alert_type, limit)
        else:
            alerts = Alert.get_active_alerts(limit)
        
        # Get alert statistics
        alert_stats = Alert.get_alert_statistics()
        
        result = {
            'alerts': [alert.to_dict() for alert in alerts],
            'statistics': alert_stats,
            'total_count': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 2 minutes
        cache_set(cache_key, json.dumps(result), timeout=120)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get active alerts error: {e}")
        return jsonify({'error': 'Failed to retrieve active alerts'}), 500

@api_bp.route('/maritime/alerts/dismiss', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def dismiss_alert():
    """Dismiss a specific alert"""
    try:
        data = request.get_json()
        alert_id = data.get('alert_id')
        
        if not alert_id:
            return jsonify({'error': 'alert_id is required'}), 400
        
        # Dismiss the alert
        success = Alert.dismiss_alert(alert_id, current_user.id)
        
        if success:
            # Clear relevant caches
            cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
            cache_delete(get_cache_key('maritime_alerts', '*'))
            
            return jsonify({
                'message': 'Alert dismissed successfully',
                'alert_id': alert_id,
                'dismissed_by': current_user.id,
                'dismissed_at': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to dismiss alert or alert not found'}), 404
        
    except Exception as e:
        logger.error(f"Dismiss alert error: {e}")
        return jsonify({'error': 'Failed to dismiss alert'}), 500

@api_bp.route('/maritime/alerts/create', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'message', 'severity', 'alert_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate severity
        valid_severities = ['info', 'warning', 'error', 'critical']
        if data['severity'] not in valid_severities:
            return jsonify({'error': 'Invalid severity level'}), 400
        
        # Create alert
        alert = Alert.create_alert(
            title=data['title'],
            message=data['message'],
            severity=data['severity'],
            icon=data.get('icon', 'alert-circle'),
            operation_id=data.get('operation_id'),
            vessel_id=data.get('vessel_id'),
            user_id=current_user.id,
            alert_type=data['alert_type'],
            alert_code=data.get('alert_code'),
            metadata=data.get('metadata'),
            auto_dismiss_hours=data.get('auto_dismiss_hours')
        )
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('maritime_alerts', '*'))
        
        logger.info(f"Manual alert created: {alert.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Alert created successfully',
            'alert': alert.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Create alert error: {e}")
        return jsonify({'error': 'Failed to create alert'}), 500

@api_bp.route('/maritime/alerts/operation/<int:operation_id>', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_alerts_for_operation(operation_id):
    """Get alerts for a specific maritime operation"""
    try:
        include_dismissed = request.args.get('include_dismissed', 'false').lower() == 'true'
        
        alerts = Alert.get_alerts_for_operation(operation_id, include_dismissed)
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts],
            'operation_id': operation_id,
            'total_count': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get operation alerts error: {e}")
        return jsonify({'error': 'Failed to retrieve operation alerts'}), 500

@api_bp.route('/maritime/alerts/vessel/<int:vessel_id>', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_alerts_for_vessel(vessel_id):
    """Get alerts for a specific vessel"""
    try:
        include_dismissed = request.args.get('include_dismissed', 'false').lower() == 'true'
        
        alerts = Alert.get_alerts_for_vessel(vessel_id, include_dismissed)
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts],
            'vessel_id': vessel_id,
            'total_count': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get vessel alerts error: {e}")
        return jsonify({'error': 'Failed to retrieve vessel alerts'}), 500

@api_bp.route('/maritime/alerts/run-checks', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def run_alert_checks():
    """Manually trigger alert checks"""
    try:
        # Run all alert generation checks
        AlertGenerator.run_all_checks()
        
        # Get updated alert statistics
        alert_stats = Alert.get_alert_statistics()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('maritime_alerts', '*'))
        
        return jsonify({
            'message': 'Alert checks completed successfully',
            'statistics': alert_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Run alert checks error: {e}")
        return jsonify({'error': 'Failed to run alert checks'}), 500

@api_bp.route('/maritime/alerts/cleanup', methods=['POST'])
@login_required
@maritime_access_required(['manager'])
def cleanup_alerts():
    """Clean up old alerts (managers only)"""
    try:
        days_old = request.json.get('days_old', 30) if request.json else 30
        
        cleaned_count = Alert.cleanup_expired_alerts(days_old)
        
        return jsonify({
            'message': f'Cleaned up {cleaned_count} old alerts',
            'cleaned_count': cleaned_count,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cleanup alerts error: {e}")
        return jsonify({'error': 'Failed to cleanup alerts'}), 500

# Team Performance API Routes
@api_bp.route('/maritime/teams/performance', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_team_performance():
    """Get team efficiency metrics for stevedoring operations"""
    try:
        # Get query parameters
        team_id = request.args.get('team_id', type=int)
        operation_id = request.args.get('operation_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        # Get cache functions
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        
        # Build cache key
        cache_key = get_cache_key('team_performance', current_user.id, team_id, operation_id, days)
        
        # Try cache first
        cached_result = cache_get(cache_key)
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        # Calculate date range
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for operations
        operations_query = MaritimeOperation.query.filter(
            MaritimeOperation.created_at >= cutoff_date
        )
        
        # Apply filters
        if operation_id:
            operations_query = operations_query.filter_by(id=operation_id)
        
        operations = operations_query.all()
        
        # Get team performance data
        team_performance = {}
        total_cargo_processed = 0
        total_operations = len(operations)
        
        for operation in operations:
            assigned_teams = operation.get_assigned_teams()
            performance_data = operation.get_team_performance_data()
            throughput_data = operation.get_team_throughput_data()
            
            # If specific team requested, filter for that team
            if team_id and str(team_id) not in assigned_teams:
                continue
            
            total_cargo_processed += operation.cargo_processed_mt or 0
            
            for team_id_str in assigned_teams:
                if team_id_str not in team_performance:
                    team_performance[team_id_str] = {
                        'team_id': int(team_id_str),
                        'operations_count': 0,
                        'total_cargo_processed': 0.0,
                        'total_hours_worked': 0.0,
                        'efficiency_ratings': [],
                        'safety_incidents': 0,
                        'completion_rate': 0.0,
                        'average_throughput': 0.0
                    }
                
                team_data = team_performance[team_id_str]
                team_data['operations_count'] += 1
                team_data['total_cargo_processed'] += operation.cargo_processed_mt or 0
                team_data['safety_incidents'] += operation.safety_incidents or 0
                
                # Add performance metrics if available
                if performance_data.get(team_id_str):
                    perf_data = performance_data[team_id_str]
                    if 'efficiency' in perf_data:
                        team_data['efficiency_ratings'].append(perf_data['efficiency'])
                    if 'hours_worked' in perf_data:
                        team_data['total_hours_worked'] += perf_data['hours_worked']
                
                # Add throughput data if available
                if throughput_data.get(team_id_str):
                    throughput = throughput_data[team_id_str]
                    if 'mt_per_hour' in throughput:
                        team_data['average_throughput'] = throughput['mt_per_hour']
        
        # Calculate aggregated metrics
        for team_id_str, data in team_performance.items():
            # Calculate average efficiency
            if data['efficiency_ratings']:
                data['average_efficiency'] = sum(data['efficiency_ratings']) / len(data['efficiency_ratings'])
            else:
                data['average_efficiency'] = 0.0
            
            # Calculate throughput rate
            if data['total_hours_worked'] > 0:
                data['throughput_rate'] = data['total_cargo_processed'] / data['total_hours_worked']
            else:
                data['throughput_rate'] = 0.0
            
            # Calculate completion rate (assuming operation completion = team completion)
            completed_ops = sum(1 for op in operations if op.status == 'completed' and team_id_str in op.get_assigned_teams())
            data['completion_rate'] = (completed_ops / data['operations_count']) * 100 if data['operations_count'] > 0 else 0.0
            
            # Calculate safety incident rate (incidents per 100 operations)
            data['safety_incident_rate'] = (data['safety_incidents'] / data['operations_count']) * 100 if data['operations_count'] > 0 else 0.0
            
            # Get team information
            team = StevedoreTeam.query.get(int(team_id_str))
            if team:
                data['team_name'] = team.team_type
                data['team_size'] = team.get_team_size()
                data['lead_name'] = team.lead.get_full_name() if team.lead else None
        
        # Calculate overall metrics
        overall_metrics = {
            'total_operations': total_operations,
            'total_cargo_processed': total_cargo_processed,
            'active_teams': len(team_performance),
            'average_efficiency': sum(data['average_efficiency'] for data in team_performance.values()) / len(team_performance) if team_performance else 0.0,
            'total_safety_incidents': sum(data['safety_incidents'] for data in team_performance.values()),
            'average_throughput': sum(data['throughput_rate'] for data in team_performance.values()) / len(team_performance) if team_performance else 0.0
        }
        
        result = {
            'team_performance': list(team_performance.values()),
            'overall_metrics': overall_metrics,
            'period_days': days,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 10 minutes
        cache_set(cache_key, json.dumps(result), timeout=600)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get team performance error: {e}")
        return jsonify({'error': 'Failed to retrieve team performance data'}), 500

@api_bp.route('/maritime/teams/active', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_active_teams():
    """Get currently active stevedoring teams"""
    try:
        # Get cache functions
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        
        # Build cache key
        cache_key = get_cache_key('active_teams', current_user.id)
        
        # Try cache first
        cached_result = cache_get(cache_key)
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        # Get active operations
        active_operations = MaritimeOperation.query.filter(
            MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
        ).all()
        
        # Get teams assigned to active operations
        active_team_ids = set()
        for operation in active_operations:
            assigned_teams = operation.get_assigned_teams()
            active_team_ids.update(assigned_teams)
        
        # Get team details
        active_teams = []
        for team_id in active_team_ids:
            try:
                team = StevedoreTeam.query.get(int(team_id))
                if team:
                    # Find current operation
                    current_operation = None
                    for operation in active_operations:
                        if str(team_id) in operation.get_assigned_teams():
                            current_operation = operation
                            break
                    
                    # Get team performance data
                    team_performance = {}
                    if current_operation:
                        perf_data = current_operation.get_team_performance_data()
                        team_performance = perf_data.get(str(team_id), {})
                    
                    team_data = {
                        'id': team.id,
                        'team_name': team.team_type,
                        'team_size': team.get_team_size(),
                        'lead_name': team.lead.get_full_name() if team.lead else None,
                        'assistant_name': team.assistant.get_full_name() if team.assistant else None,
                        'shift_start': team.shift_start.strftime('%H:%M') if team.shift_start else None,
                        'shift_end': team.shift_end.strftime('%H:%M') if team.shift_end else None,
                        'current_operation': {
                            'id': current_operation.id,
                            'vessel_name': current_operation.vessel_name,
                            'operation_type': current_operation.operation_type,
                            'status': current_operation.status,
                            'progress': current_operation.progress
                        } if current_operation else None,
                        'performance': {
                            'efficiency': team_performance.get('efficiency', 0.0),
                            'cargo_processed': team_performance.get('cargo_processed', 0.0),
                            'hours_worked': team_performance.get('hours_worked', 0.0),
                            'throughput_rate': team_performance.get('cargo_processed', 0.0) / team_performance.get('hours_worked', 1.0)
                        },
                        'status': 'active',
                        'created_at': team.created_at.isoformat()
                    }
                    active_teams.append(team_data)
            except (ValueError, TypeError):
                continue
        
        # Sort by team name
        active_teams.sort(key=lambda x: x['team_name'])
        
        result = {
            'active_teams': active_teams,
            'total_active_teams': len(active_teams),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        cache_set(cache_key, json.dumps(result), timeout=300)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get active teams error: {e}")
        return jsonify({'error': 'Failed to retrieve active teams'}), 500

@api_bp.route('/maritime/teams/assignments', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_team_assignments():
    """Get team-to-operation assignments"""
    try:
        # Get query parameters
        team_id = request.args.get('team_id', type=int)
        operation_id = request.args.get('operation_id', type=int)
        status = request.args.get('status', 'active')
        
        # Build query
        query = MaritimeOperation.query
        
        # Apply status filter
        if status == 'active':
            query = query.filter(MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4']))
        elif status == 'completed':
            query = query.filter_by(status='completed')
        elif status == 'all':
            pass  # No filter
        
        # Apply operation filter
        if operation_id:
            query = query.filter_by(id=operation_id)
        
        operations = query.order_by(MaritimeOperation.created_at.desc()).all()
        
        # Build assignments data
        assignments = []
        for operation in operations:
            assigned_teams = operation.get_assigned_teams()
            
            # If specific team requested, filter for that team
            if team_id and str(team_id) not in assigned_teams:
                continue
            
            # Get team details
            team_details = []
            for team_id_str in assigned_teams:
                try:
                    team = StevedoreTeam.query.get(int(team_id_str))
                    if team:
                        # Get team performance for this operation
                        performance_data = operation.get_team_performance_data()
                        team_performance = performance_data.get(team_id_str, {})
                        
                        team_details.append({
                            'team_id': team.id,
                            'team_name': team.team_type,
                            'team_size': team.get_team_size(),
                            'lead_name': team.lead.get_full_name() if team.lead else None,
                            'performance': {
                                'efficiency': team_performance.get('efficiency', 0.0),
                                'cargo_processed': team_performance.get('cargo_processed', 0.0),
                                'hours_worked': team_performance.get('hours_worked', 0.0)
                            }
                        })
                except (ValueError, TypeError):
                    continue
            
            assignment = {
                'operation_id': operation.id,
                'vessel_name': operation.vessel_name,
                'operation_type': operation.operation_type,
                'status': operation.status,
                'progress': operation.progress,
                'berth': operation.berth,
                'assigned_teams': team_details,
                'team_count': len(team_details),
                'cargo_processed': operation.cargo_processed_mt or 0.0,
                'operation_efficiency': operation.operation_efficiency or 0.0,
                'safety_incidents': operation.safety_incidents or 0,
                'created_at': operation.created_at.isoformat(),
                'updated_at': operation.updated_at.isoformat() if operation.updated_at else None
            }
            assignments.append(assignment)
        
        result = {
            'assignments': assignments,
            'total_assignments': len(assignments),
            'status_filter': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get team assignments error: {e}")
        return jsonify({'error': 'Failed to retrieve team assignments'}), 500

@api_bp.route('/maritime/teams/assign', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def assign_teams_to_operation():
    """Assign teams to a maritime operation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        operation_id = data.get('operation_id')
        team_ids = data.get('team_ids', [])
        
        if not operation_id:
            return jsonify({'error': 'operation_id is required'}), 400
        
        if not team_ids or not isinstance(team_ids, list):
            return jsonify({'error': 'team_ids must be a non-empty list'}), 400
        
        # Get operation
        operation = MaritimeOperation.query.get(operation_id)
        if not operation:
            return jsonify({'error': 'Operation not found'}), 404
        
        # Validate teams exist
        teams = []
        for team_id in team_ids:
            team = StevedoreTeam.query.get(team_id)
            if not team:
                return jsonify({'error': f'Team {team_id} not found'}), 404
            teams.append(team)
        
        # Check for team conflicts (teams already assigned to other active operations)
        conflicts = []
        active_operations = MaritimeOperation.query.filter(
            MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4']),
            MaritimeOperation.id != operation_id
        ).all()
        
        for other_op in active_operations:
            other_assigned_teams = other_op.get_assigned_teams()
            for team_id in team_ids:
                if str(team_id) in other_assigned_teams:
                    conflicts.append({
                        'team_id': team_id,
                        'operation_id': other_op.id,
                        'vessel_name': other_op.vessel_name
                    })
        
        # Return conflicts if any (unless force flag is set)
        if conflicts and not data.get('force', False):
            return jsonify({
                'error': 'Team assignment conflicts detected',
                'conflicts': conflicts,
                'message': 'Some teams are already assigned to other active operations. Use force=true to reassign.'
            }), 409
        
        # If forcing, remove teams from conflicting operations
        if data.get('force', False):
            for conflict in conflicts:
                conflicting_op = MaritimeOperation.query.get(conflict['operation_id'])
                if conflicting_op:
                    conflicting_teams = conflicting_op.get_assigned_teams()
                    conflicting_teams = [t for t in conflicting_teams if int(t) != conflict['team_id']]
                    conflicting_op.set_assigned_teams(conflicting_teams)
        
        # Assign teams to operation
        operation.set_assigned_teams([str(team_id) for team_id in team_ids])
        
        # Initialize team performance data
        performance_data = operation.get_team_performance_data()
        throughput_data = operation.get_team_throughput_data()
        
        for team_id in team_ids:
            team_id_str = str(team_id)
            if team_id_str not in performance_data:
                performance_data[team_id_str] = {
                    'efficiency': 0.0,
                    'cargo_processed': 0.0,
                    'hours_worked': 0.0,
                    'assigned_at': datetime.utcnow().isoformat()
                }
            
            if team_id_str not in throughput_data:
                throughput_data[team_id_str] = {
                    'mt_per_hour': 0.0,
                    'peak_throughput': 0.0,
                    'target_throughput': 150.0  # Default target
                }
        
        operation.set_team_performance_data(performance_data)
        operation.set_team_throughput_data(throughput_data)
        
        # Update operation
        operation.updated_at = datetime.utcnow()
        
        db = get_app_db()
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('active_teams', '*'))
        cache_delete(get_cache_key('team_performance', '*'))
        
        # Get updated team details
        assigned_teams_data = []
        for team in teams:
            assigned_teams_data.append({
                'team_id': team.id,
                'team_name': team.team_type,
                'team_size': team.get_team_size(),
                'lead_name': team.lead.get_full_name() if team.lead else None
            })
        
        logger.info(f"Teams assigned to operation {operation_id}: {team_ids} by user {current_user.id}")
        
        return jsonify({
            'message': 'Teams assigned successfully',
            'operation_id': operation_id,
            'assigned_teams': assigned_teams_data,
            'conflicts_resolved': len(conflicts) if data.get('force', False) else 0,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Assign teams error: {e}")
        return jsonify({'error': 'Failed to assign teams to operation'}), 500

@api_bp.route('/maritime/teams/performance/update', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def update_team_performance():
    """Update team performance metrics for an operation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        operation_id = data.get('operation_id')
        team_id = data.get('team_id')
        performance_data = data.get('performance_data', {})
        
        if not operation_id or not team_id:
            return jsonify({'error': 'operation_id and team_id are required'}), 400
        
        # Get operation
        operation = MaritimeOperation.query.get(operation_id)
        if not operation:
            return jsonify({'error': 'Operation not found'}), 404
        
        # Verify team is assigned to operation
        assigned_teams = operation.get_assigned_teams()
        if str(team_id) not in assigned_teams:
            return jsonify({'error': 'Team not assigned to this operation'}), 400
        
        # Update performance data
        current_performance = operation.get_team_performance_data()
        team_id_str = str(team_id)
        
        if team_id_str not in current_performance:
            current_performance[team_id_str] = {}
        
        # Update allowed performance fields
        allowed_fields = ['efficiency', 'cargo_processed', 'hours_worked', 'safety_incidents']
        for field in allowed_fields:
            if field in performance_data:
                current_performance[team_id_str][field] = performance_data[field]
        
        # Update timestamp
        current_performance[team_id_str]['updated_at'] = datetime.utcnow().isoformat()
        
        # Set updated performance data
        operation.set_team_performance_data(current_performance)
        
        # Update throughput data if provided
        if 'throughput_data' in data:
            throughput_data = operation.get_team_throughput_data()
            if team_id_str not in throughput_data:
                throughput_data[team_id_str] = {}
            
            throughput_fields = ['mt_per_hour', 'peak_throughput', 'target_throughput']
            for field in throughput_fields:
                if field in data['throughput_data']:
                    throughput_data[team_id_str][field] = data['throughput_data'][field]
            
            operation.set_team_throughput_data(throughput_data)
        
        # Recalculate operation-level metrics
        operation.operation_efficiency = operation.calculate_overall_efficiency()
        operation.updated_at = datetime.utcnow()
        
        db = get_app_db()
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('team_performance', '*'))
        cache_delete(get_cache_key('active_teams', '*'))
        
        logger.info(f"Team performance updated for operation {operation_id}, team {team_id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Team performance updated successfully',
            'operation_id': operation_id,
            'team_id': team_id,
            'updated_performance': current_performance[team_id_str],
            'operation_efficiency': operation.operation_efficiency,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Update team performance error: {e}")
        return jsonify({'error': 'Failed to update team performance'}), 500

# TICO Vehicle Management API
@api_bp.route('/maritime/vehicles/tico', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_tico_vehicles():
    """Get TICO vehicle status and information"""
    try:
        # Get query parameters
        vessel_id = request.args.get('vessel_id', type=int)
        zone = request.args.get('zone')
        status = request.args.get('status')
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        # Get cache functions
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        
        # Build cache key
        cache_key = get_cache_key('tico_vehicles', vessel_id, zone, status, available_only)
        
        # Try cache first
        cached_result = cache_get(cache_key)
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        # Build query
        query = TicoVehicle.query
        
        # Apply filters
        if vessel_id:
            query = query.filter_by(vessel_id=vessel_id)
        
        if zone:
            query = query.filter_by(zone_assignment=zone)
        
        if status:
            query = query.filter_by(status=status)
        
        if available_only:
            query = query.filter_by(status='available')
        
        # Order by license plate
        vehicles = query.order_by(TicoVehicle.license_plate).all()
        
        # Get utilization summary
        utilization_summary = TicoVehicle.get_utilization_summary(vessel_id)
        
        # Get zone summary
        zone_summary = {}
        for vehicle in vehicles:
            zone = vehicle.zone_assignment or 'Unassigned'
            if zone not in zone_summary:
                zone_summary[zone] = {
                    'total_vehicles': 0,
                    'available_vehicles': 0,
                    'total_capacity': 0,
                    'available_capacity': 0
                }
            
            zone_summary[zone]['total_vehicles'] += 1
            zone_summary[zone]['total_capacity'] += vehicle.capacity
            zone_summary[zone]['available_capacity'] += vehicle.get_available_capacity()
            
            if vehicle.is_available():
                zone_summary[zone]['available_vehicles'] += 1
        
        result = {
            'vehicles': [vehicle.to_dict() for vehicle in vehicles],
            'utilization_summary': utilization_summary,
            'zone_summary': zone_summary,
            'total_vehicles': len(vehicles),
            'available_vehicles': len([v for v in vehicles if v.is_available()]),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache for 3 minutes
        cache_set(cache_key, json.dumps(result), timeout=180)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get TICO vehicles error: {e}")
        return jsonify({'error': 'Failed to retrieve TICO vehicles'}), 500

@api_bp.route('/maritime/vehicles/assign', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def assign_vehicle_to_zone():
    """Assign vehicles to zones"""
    try:
        data = request.get_json()
        
        # Validate required fields
        vehicle_id = data.get('vehicle_id')
        zone = data.get('zone')
        driver_id = data.get('driver_id')
        passenger_count = data.get('passenger_count', 1)
        
        if not vehicle_id or not zone:
            return jsonify({'error': 'vehicle_id and zone are required'}), 400
        
        # Get vehicle
        vehicle = TicoVehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Check if vehicle can accommodate passengers
        if not vehicle.can_accommodate(passenger_count):
            return jsonify({
                'error': 'Vehicle cannot accommodate requested passengers',
                'available_capacity': vehicle.get_available_capacity(),
                'requested_capacity': passenger_count
            }), 400
        
        # Assign vehicle to zone
        success, message = vehicle.assign_to_zone(zone, driver_id)
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Update passenger count
        vehicle.current_load += passenger_count
        
        db = get_app_db()
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tico_vehicles', '*'))
        
        logger.info(f"Vehicle {vehicle_id} assigned to zone {zone} by user {current_user.id}")
        
        return jsonify({
            'message': 'Vehicle assigned successfully',
            'vehicle_id': vehicle_id,
            'zone': zone,
            'driver_id': driver_id,
            'passenger_count': passenger_count,
            'vehicle_status': vehicle.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Assign vehicle error: {e}")
        return jsonify({'error': 'Failed to assign vehicle'}), 500

@api_bp.route('/maritime/vehicles/update-location', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead', 'worker'])
def update_vehicle_location():
    """Update vehicle location"""
    try:
        data = request.get_json()
        
        # Validate required fields
        vehicle_id = data.get('vehicle_id')
        location = data.get('location')
        coordinates = data.get('coordinates')
        
        if not vehicle_id or not location:
            return jsonify({'error': 'vehicle_id and location are required'}), 400
        
        # Get vehicle
        vehicle = TicoVehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Check permissions - workers can only update vehicles they're assigned to
        if current_user.is_worker() and vehicle.driver_id != current_user.id:
            return jsonify({'error': 'Access denied - not assigned to this vehicle'}), 403
        
        # Update location
        vehicle.update_location(location, coordinates)
        
        db = get_app_db()
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tico_vehicles', '*'))
        
        logger.info(f"Vehicle {vehicle_id} location updated to {location} by user {current_user.id}")
        
        return jsonify({
            'message': 'Vehicle location updated successfully',
            'vehicle_id': vehicle_id,
            'location': location,
            'coordinates': coordinates,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Update vehicle location error: {e}")
        return jsonify({'error': 'Failed to update vehicle location'}), 500

@api_bp.route('/maritime/vehicles/utilization', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_vehicle_utilization():
    """Get vehicle utilization metrics"""
    try:
        # Get query parameters
        vessel_id = request.args.get('vessel_id', type=int)
        hours = request.args.get('hours', 24, type=int)
        vehicle_id = request.args.get('vehicle_id', type=int)
        
        # Get cache functions
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        
        # Build cache key
        cache_key = get_cache_key('vehicle_utilization', vessel_id, hours, vehicle_id)
        
        # Try cache first
        cached_result = cache_get(cache_key)
        if cached_result:
            import json
            return jsonify(json.loads(cached_result))
        
        if vehicle_id:
            # Get utilization for specific vehicle
            vehicle = TicoVehicle.query.get(vehicle_id)
            if not vehicle:
                return jsonify({'error': 'Vehicle not found'}), 404
            
            utilization = vehicle.get_utilization(hours)
            
            # Get recent assignments
            from_time = datetime.utcnow() - timedelta(hours=hours)
            assignments = TicoVehicleAssignment.query.filter(
                TicoVehicleAssignment.vehicle_id == vehicle_id,
                TicoVehicleAssignment.assigned_at >= from_time
            ).order_by(TicoVehicleAssignment.assigned_at.desc()).all()
            
            # Get location history
            locations = TicoVehicleLocation.query.filter(
                TicoVehicleLocation.vehicle_id == vehicle_id,
                TicoVehicleLocation.timestamp >= from_time
            ).order_by(TicoVehicleLocation.timestamp.desc()).all()
            
            result = {
                'vehicle': vehicle.to_dict(),
                'utilization_percentage': utilization,
                'assignments': [assignment.to_dict() for assignment in assignments],
                'location_history': [location.to_dict() for location in locations],
                'period_hours': hours,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            # Get utilization summary for all vehicles
            utilization_summary = TicoVehicle.get_utilization_summary(vessel_id, hours)
            
            # Get vehicles
            query = TicoVehicle.query
            if vessel_id:
                query = query.filter_by(vessel_id=vessel_id)
            
            vehicles = query.all()
            
            # Get detailed utilization for each vehicle
            vehicle_utilizations = []
            for vehicle in vehicles:
                util = vehicle.get_utilization(hours)
                vehicle_utilizations.append({
                    'vehicle_id': vehicle.id,
                    'license_plate': vehicle.license_plate,
                    'zone_assignment': vehicle.zone_assignment,
                    'utilization_percentage': util,
                    'status': vehicle.status,
                    'driver_name': vehicle.driver.get_full_name() if vehicle.driver else None
                })
            
            result = {
                'utilization_summary': utilization_summary,
                'vehicle_utilizations': vehicle_utilizations,
                'period_hours': hours,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Cache for 5 minutes
        cache_set(cache_key, json.dumps(result), timeout=300)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get vehicle utilization error: {e}")
        return jsonify({'error': 'Failed to retrieve vehicle utilization'}), 500

@api_bp.route('/maritime/vehicles/optimize', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def optimize_vehicle_assignments():
    """Get optimized vehicle assignment recommendations"""
    try:
        data = request.get_json()
        
        # Validate required fields
        vessel_id = data.get('vessel_id')
        zone_demands = data.get('zone_demands', {})
        
        if not vessel_id:
            return jsonify({'error': 'vessel_id is required'}), 400
        
        if not zone_demands or not isinstance(zone_demands, dict):
            return jsonify({'error': 'zone_demands must be a dictionary of zone: capacity_needed'}), 400
        
        # Get optimization recommendations
        optimization_result = TicoRouteOptimizer.calculate_optimal_assignments(vessel_id, zone_demands)
        
        # Get workload balance recommendations
        balance_result = TicoRouteOptimizer.balance_vehicle_workload(vessel_id)
        
        # Get automated dispatch recommendations
        dispatch_result = TicoRouteOptimizer.get_automated_dispatch_recommendations(vessel_id, zone_demands)
        
        result = {
            'optimization': optimization_result,
            'workload_balance': balance_result,
            'dispatch_recommendations': dispatch_result,
            'vessel_id': vessel_id,
            'zone_demands': zone_demands,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Vehicle optimization calculated for vessel {vessel_id} by user {current_user.id}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Optimize vehicle assignments error: {e}")
        return jsonify({'error': 'Failed to optimize vehicle assignments'}), 500

@api_bp.route('/maritime/vehicles/complete-assignment', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead', 'worker'])
def complete_vehicle_assignment():
    """Complete a vehicle assignment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        assignment_id = data.get('assignment_id')
        notes = data.get('notes', '')
        
        if not assignment_id:
            return jsonify({'error': 'assignment_id is required'}), 400
        
        # Get assignment
        assignment = TicoVehicleAssignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Check permissions - workers can only complete assignments they're assigned to
        if current_user.is_worker() and assignment.driver_id != current_user.id:
            return jsonify({'error': 'Access denied - not assigned to this vehicle'}), 403
        
        # Complete assignment
        assignment.notes = notes
        assignment.complete_assignment()
        
        db = get_app_db()
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tico_vehicles', '*'))
        cache_delete(get_cache_key('vehicle_utilization', '*'))
        
        logger.info(f"Vehicle assignment {assignment_id} completed by user {current_user.id}")
        
        return jsonify({
            'message': 'Vehicle assignment completed successfully',
            'assignment_id': assignment_id,
            'assignment': assignment.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Complete vehicle assignment error: {e}")
        return jsonify({'error': 'Failed to complete vehicle assignment'}), 500

@api_bp.route('/maritime/vehicles/assignments', methods=['GET'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor', 'stevedore_lead'])
def get_vehicle_assignments():
    """Get vehicle assignments with optional filters"""
    try:
        # Get query parameters
        vessel_id = request.args.get('vessel_id', type=int)
        zone = request.args.get('zone')
        status = request.args.get('status', 'active')  # active, completed, all
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = TicoVehicleAssignment.query
        
        # Join with vehicle to filter by vessel
        if vessel_id:
            query = query.join(TicoVehicle).filter(TicoVehicle.vessel_id == vessel_id)
        
        # Apply filters
        if zone:
            query = query.filter_by(zone=zone)
        
        if status == 'active':
            query = query.filter(TicoVehicleAssignment.completed_at.is_(None))
        elif status == 'completed':
            query = query.filter(TicoVehicleAssignment.completed_at.isnot(None))
        # 'all' means no filter
        
        # Order by assigned_at desc and limit
        assignments = query.order_by(TicoVehicleAssignment.assigned_at.desc()).limit(limit).all()
        
        # Get assignment statistics
        stats = {
            'total_assignments': query.count(),
            'active_assignments': query.filter(TicoVehicleAssignment.completed_at.is_(None)).count(),
            'completed_assignments': query.filter(TicoVehicleAssignment.completed_at.isnot(None)).count(),
            'average_duration': 0
        }
        
        # Calculate average duration for completed assignments
        completed_assignments = [a for a in assignments if a.completed_at]
        if completed_assignments:
            total_duration = sum(a.get_duration() for a in completed_assignments)
            stats['average_duration'] = total_duration / len(completed_assignments)
        
        result = {
            'assignments': [assignment.to_dict() for assignment in assignments],
            'statistics': stats,
            'filters': {
                'vessel_id': vessel_id,
                'zone': zone,
                'status': status,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Get vehicle assignments error: {e}")
        return jsonify({'error': 'Failed to retrieve vehicle assignments'}), 500

@api_bp.route('/maritime/vehicles/create', methods=['POST'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def create_tico_vehicle():
    """Create a new TICO vehicle"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vessel_id', 'vehicle_type', 'license_plate', 'capacity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate vehicle type
        if data['vehicle_type'] not in ['van', 'station_wagon']:
            return jsonify({'error': 'vehicle_type must be "van" or "station_wagon"'}), 400
        
        # Check if license plate already exists
        existing_vehicle = TicoVehicle.query.filter_by(license_plate=data['license_plate']).first()
        if existing_vehicle:
            return jsonify({'error': 'Vehicle with this license plate already exists'}), 400
        
        # Create vehicle
        vehicle = TicoVehicle(
            vessel_id=data['vessel_id'],
            vehicle_type=data['vehicle_type'],
            license_plate=data['license_plate'],
            capacity=data['capacity'],
            zone_assignment=data.get('zone_assignment'),
            driver_id=data.get('driver_id'),
            current_location=data.get('current_location')
        )
        
        db = get_app_db()
        db.session.add(vehicle)
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tico_vehicles', '*'))
        
        logger.info(f"TICO vehicle created: {vehicle.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'TICO vehicle created successfully',
            'vehicle': vehicle.to_dict()
        }), 201
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Create TICO vehicle error: {e}")
        return jsonify({'error': 'Failed to create TICO vehicle'}), 500

@api_bp.route('/maritime/vehicles/<int:vehicle_id>', methods=['PUT'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def update_tico_vehicle(vehicle_id):
    """Update TICO vehicle information"""
    try:
        data = request.get_json()
        
        # Get vehicle
        vehicle = TicoVehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Update allowed fields
        updatable_fields = [
            'vehicle_type', 'license_plate', 'capacity', 'status',
            'zone_assignment', 'driver_id', 'current_location',
            'next_maintenance'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'license_plate' and data[field] != vehicle.license_plate:
                    # Check if new license plate already exists
                    existing = TicoVehicle.query.filter_by(license_plate=data[field]).first()
                    if existing:
                        return jsonify({'error': 'Vehicle with this license plate already exists'}), 400
                
                if field == 'next_maintenance' and data[field]:
                    try:
                        vehicle.next_maintenance = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({'error': 'Invalid next_maintenance date format'}), 400
                else:
                    setattr(vehicle, field, data[field])
        
        vehicle.updated_at = datetime.utcnow()
        
        db = get_app_db()
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('tico_vehicles', '*'))
        
        logger.info(f"TICO vehicle updated: {vehicle_id} by user {current_user.id}")
        
        return jsonify({
            'message': 'TICO vehicle updated successfully',
            'vehicle': vehicle.to_dict()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Update TICO vehicle error: {e}")
        return jsonify({'error': 'Failed to update TICO vehicle'}), 500