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

logger = structlog.get_logger()

api_bp = Blueprint('api', __name__)

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