"""
Dashboard routes for web interface
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import structlog

from app import db
from models.user import User
from models.vessel import Vessel
from models.task import Task
from models.sync_log import SyncLog

logger = structlog.get_logger()

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def main():
    """Main dashboard page"""
    try:
        if current_user.is_manager():
            return redirect(url_for('dashboard.manager'))
        else:
            return redirect(url_for('dashboard.worker'))
    except Exception as e:
        logger.error(f"Dashboard main error: {e}")
        flash('An error occurred loading the dashboard', 'error')
        return render_template('dashboard/error.html'), 500

@dashboard_bp.route('/manager')
@login_required
def manager():
    """Manager dashboard"""
    if not current_user.is_manager():
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.worker'))
    
    try:
        # Get statistics
        task_stats = Task.get_task_statistics()
        overdue_tasks = Task.get_overdue_tasks()
        recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(10).all()
        vessels = Vessel.get_active_vessels()
        users = User.query.filter_by(is_active=True).all()
        
        # Get sync status
        pending_syncs = SyncLog.get_pending_syncs()
        failed_syncs = SyncLog.get_failed_syncs()
        
        return render_template('dashboard/manager.html',
            task_stats=task_stats,
            overdue_tasks=overdue_tasks,
            recent_tasks=recent_tasks,
            vessels=vessels,
            users=users,
            pending_syncs_count=len(pending_syncs),
            failed_syncs_count=len(failed_syncs)
        )
        
    except Exception as e:
        logger.error(f"Manager dashboard error: {e}")
        flash('An error occurred loading the manager dashboard', 'error')
        return render_template('dashboard/error.html'), 500

@dashboard_bp.route('/worker')
@login_required
def worker():
    """Worker dashboard"""
    try:
        # Get user's tasks
        my_tasks = Task.get_tasks_for_user(current_user.id)
        pending_tasks = [t for t in my_tasks if t.status == 'pending']
        in_progress_tasks = [t for t in my_tasks if t.status == 'in_progress']
        completed_tasks = [t for t in my_tasks if t.status == 'completed']
        overdue_tasks = [t for t in my_tasks if t.is_overdue()]
        
        # Get vessel information
        vessel = current_user.vessel
        vessel_tasks = []
        if vessel:
            vessel_tasks = Task.get_tasks_for_vessel(vessel.id, status='pending')
        
        # Get sync status
        user_sync_stats = SyncLog.get_sync_statistics(current_user.id)
        
        return render_template('dashboard/worker.html',
            my_tasks=my_tasks,
            pending_tasks=pending_tasks,
            in_progress_tasks=in_progress_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            vessel=vessel,
            vessel_tasks=vessel_tasks,
            sync_stats=user_sync_stats
        )
        
    except Exception as e:
        logger.error(f"Worker dashboard error: {e}")
        flash('An error occurred loading the worker dashboard', 'error')
        return render_template('dashboard/error.html'), 500

@dashboard_bp.route('/tasks')
@login_required
def tasks():
    """Tasks management page"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status')
        vessel_filter = request.args.get('vessel_id', type=int)
        assigned_filter = request.args.get('assigned_to', type=int)
        priority_filter = request.args.get('priority')
        
        # Build query
        query = Task.query
        
        # Apply role-based filtering
        if current_user.is_worker():
            if current_user.vessel_id:
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
        
        # Apply filters
        if status_filter:
            query = query.filter_by(status=status_filter)
        if vessel_filter:
            query = query.filter_by(vessel_id=vessel_filter)
        if assigned_filter:
            query = query.filter_by(assigned_to_id=assigned_filter)
        if priority_filter:
            query = query.filter_by(priority=priority_filter)
        
        # Order and paginate
        page = request.args.get('page', 1, type=int)
        tasks_paginated = query.order_by(
            Task.due_date.asc(), Task.priority.desc()
        ).paginate(
            page=page, per_page=20, error_out=False
        )
        
        # Get filter options
        vessels = Vessel.get_active_vessels() if current_user.is_manager() else []
        users = User.query.filter_by(is_active=True).all() if current_user.is_manager() else []
        
        return render_template('dashboard/tasks.html',
            tasks=tasks_paginated.items,
            pagination=tasks_paginated,
            vessels=vessels,
            users=users,
            current_filters={
                'status': status_filter,
                'vessel_id': vessel_filter,
                'assigned_to': assigned_filter,
                'priority': priority_filter
            }
        )
        
    except Exception as e:
        logger.error(f"Tasks page error: {e}")
        flash('An error occurred loading tasks', 'error')
        return render_template('dashboard/error.html'), 500

@dashboard_bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    """Create task page"""
    if request.method == 'GET':
        vessels = Vessel.get_active_vessels()
        users = User.query.filter_by(is_active=True).all()
        return render_template('dashboard/task_create.html', vessels=vessels, users=users)
    
    # Handle POST - redirect to API
    return redirect(url_for('api.create_task'))

@dashboard_bp.route('/tasks/<int:task_id>')
@login_required
def task_detail(task_id):
    """Task detail page"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Check permissions
        if current_user.is_worker():
            if (task.assigned_to_id != current_user.id and 
                task.vessel_id != current_user.vessel_id):
                flash('Access denied', 'error')
                return redirect(url_for('dashboard.tasks'))
        
        return render_template('dashboard/task_detail.html', task=task)
        
    except Exception as e:
        logger.error(f"Task detail error: {e}")
        flash('An error occurred loading task details', 'error')
        return redirect(url_for('dashboard.tasks'))

@dashboard_bp.route('/vessels')
@login_required
def vessels():
    """Vessels management page (managers only)"""
    if not current_user.is_manager():
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        vessels = Vessel.query.order_by(Vessel.name).all()
        return render_template('dashboard/vessels.html', vessels=vessels)
        
    except Exception as e:
        logger.error(f"Vessels page error: {e}")
        flash('An error occurred loading vessels', 'error')
        return render_template('dashboard/error.html'), 500

@dashboard_bp.route('/vessels/<int:vessel_id>')
@login_required
def vessel_detail(vessel_id):
    """Vessel detail page"""
    try:
        vessel = Vessel.query.get_or_404(vessel_id)
        vessel_tasks = Task.get_tasks_for_vessel(vessel_id)
        crew_members = User.get_by_vessel(vessel_id)
        
        return render_template('dashboard/vessel_detail.html', 
            vessel=vessel, 
            tasks=vessel_tasks,
            crew_members=crew_members
        )
        
    except Exception as e:
        logger.error(f"Vessel detail error: {e}")
        flash('An error occurred loading vessel details', 'error')
        return redirect(url_for('dashboard.vessels'))

@dashboard_bp.route('/users')
@login_required
def users():
    """Users management page (managers only)"""
    if not current_user.is_manager():
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        users = User.query.filter_by(is_active=True).order_by(User.role, User.username).all()
        vessels = Vessel.get_active_vessels()
        return render_template('dashboard/users.html', users=users, vessels=vessels)
        
    except Exception as e:
        logger.error(f"Users page error: {e}")
        flash('An error occurred loading users', 'error')
        return render_template('dashboard/error.html'), 500

@dashboard_bp.route('/sync')
@login_required
def sync_status():
    """Sync status page"""
    try:
        if current_user.is_manager():
            # Show all sync logs for managers
            pending_syncs = SyncLog.get_pending_syncs()
            failed_syncs = SyncLog.get_failed_syncs()
            sync_stats = SyncLog.get_sync_statistics()
        else:
            # Show only user's sync logs for workers
            pending_syncs = SyncLog.get_pending_syncs(current_user.id)
            failed_syncs = SyncLog.get_failed_syncs(current_user.id)
            sync_stats = SyncLog.get_sync_statistics(current_user.id)
        
        return render_template('dashboard/sync.html',
            pending_syncs=pending_syncs,
            failed_syncs=failed_syncs,
            sync_stats=sync_stats
        )
        
    except Exception as e:
        logger.error(f"Sync status page error: {e}")
        flash('An error occurred loading sync status', 'error')
        return render_template('dashboard/error.html'), 500

@dashboard_bp.route('/reports')
@login_required
def reports():
    """Reports page (managers only)"""
    if not current_user.is_manager():
        flash('Access denied', 'error')
        return redirect(url_for('dashboard.main'))
    
    try:
        # Get date range from query params
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Task completion stats
        completed_tasks = Task.query.filter(
            Task.status == 'completed',
            Task.completion_date >= start_date
        ).all()
        
        # Overdue tasks
        overdue_tasks = Task.get_overdue_tasks()
        
        # User productivity
        user_stats = []
        for user in User.query.filter_by(is_active=True, role='worker').all():
            user_completed = [t for t in completed_tasks if t.assigned_to_id == user.id]
            user_stats.append({
                'user': user,
                'completed_tasks': len(user_completed),
                'total_hours': sum(t.actual_hours or 0 for t in user_completed)
            })
        
        # Vessel stats
        vessel_stats = []
        for vessel in Vessel.get_active_vessels():
            vessel_completed = [t for t in completed_tasks if t.vessel_id == vessel.id]
            vessel_stats.append({
                'vessel': vessel,
                'completed_tasks': len(vessel_completed),
                'active_tasks': vessel.get_active_tasks_count()
            })
        
        return render_template('dashboard/reports.html',
            days=days,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            user_stats=user_stats,
            vessel_stats=vessel_stats
        )
        
    except Exception as e:
        logger.error(f"Reports page error: {e}")
        flash('An error occurred loading reports', 'error')
        return render_template('dashboard/error.html'), 500