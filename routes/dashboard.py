"""
Dashboard routes for web interface
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import structlog
from sqlalchemy import func

def get_app_db():
    import app
    return app.db
from models.models.enhanced_user import User
from models.models.enhanced_vessel import Vessel
from models.models.enhanced_task import Task
from models.models.sync_log import SyncLog
try:
    from models.models.alert import Alert, AlertGenerator
except ImportError:
    Alert = None
    AlertGenerator = None

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

        # Get maritime operations
        # Get maritime operations (late import to avoid circular import)
        from models.maritime.maritime_operation import MaritimeOperation
        maritime_operations = MaritimeOperation.query.order_by(MaritimeOperation.created_at.desc()).all()
        
        # Calculate stevedoring-specific metrics
        today = datetime.utcnow().date()
        completed_tasks_today = Task.query.filter(
            Task.status == 'completed',
            Task.completion_date >= today
        ).count()
        
        # Mock berth utilization data
        berth_utilization = {
            'berth_1': {'status': 'occupied', 'vessel': vessels[0] if vessels else None, 'eta': '14:30', 'progress': 65},
            'berth_2': {'status': 'available', 'vessel': None, 'eta': None, 'progress': 0},
            'berth_3': {'status': 'occupied', 'vessel': vessels[1] if len(vessels) > 1 else None, 'eta': '16:00', 'progress': 30}
        }
        
        # Run alert generation checks and get alerts
        try:
            if AlertGenerator:
                AlertGenerator.run_all_checks()
            manager_alerts = Alert.get_active_alerts(limit=5) if Alert else []
            manager_alert_stats = Alert.get_alert_statistics() if Alert else {}
        except Exception as e:
            logger.error(f"Manager dashboard alert generation error: {e}")
            manager_alerts = []
            manager_alert_stats = {
                'total_active': 0,
                'by_severity': {'critical': 0, 'error': 0, 'warning': 0, 'info': 0},
                'by_type': {},
                'recent_count': 0
            }
        
        return render_template('dashboard/manager.html',
            task_stats=task_stats,
            overdue_tasks=overdue_tasks,
            recent_tasks=recent_tasks,
            vessels=vessels,
            users=users,
            pending_syncs_count=len(pending_syncs),
            failed_syncs_count=len(failed_syncs),
            maritime_operations=maritime_operations,
            today=today,
            completed_tasks_today=completed_tasks_today,
            berth_utilization=berth_utilization,
            alerts=[alert.to_dict() for alert in manager_alerts],
            alert_stats=manager_alert_stats
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
        
        # Get current time for shift calculation
        now = datetime.utcnow()
        today = now.date()
        
        return render_template('dashboard/worker.html',
            my_tasks=my_tasks,
            pending_tasks=pending_tasks,
            in_progress_tasks=in_progress_tasks,
            completed_tasks=completed_tasks,
            overdue_tasks=overdue_tasks,
            vessel=vessel,
            vessel_tasks=vessel_tasks,
            sync_stats=user_sync_stats,
            now=now,
            today=today
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

@dashboard_bp.route('/operations')
@login_required
def operations():
    """Stevedoring operations dashboard"""
    try:
        # Get active maritime operations
        # Get maritime operations (late import to avoid circular import)
        from models.maritime.maritime_operation import MaritimeOperation
        active_operations = MaritimeOperation.query.filter(
            MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
        ).order_by(MaritimeOperation.created_at.desc()).all()
        
        # Get vessel queue (vessels not currently assigned to berths)
        vessel_queue = Vessel.query.filter(
            Vessel.berth_number.is_(None)
        ).order_by(Vessel.created_at.desc()).all()
        
        # Real berth status from active operations
        berth_status = {
            'berth_1': {'status': 'available', 'vessel': None, 'eta': None, 'progress': 0},
            'berth_2': {'status': 'available', 'vessel': None, 'eta': None, 'progress': 0},
            'berth_3': {'status': 'available', 'vessel': None, 'eta': None, 'progress': 0}
        }
        
        # Get active operations with berth assignments
        try:
            active_berth_ops = MaritimeOperation.query.filter(
                MaritimeOperation.berth_assigned.isnot(None),
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            for op in active_berth_ops:
                berth_key = f'berth_{op.berth_assigned}'
                if berth_key in berth_status:
                    berth_status[berth_key] = {
                        'status': 'occupied',
                        'vessel': op.vessel if op.vessel else None,
                        'vessel_name': op.vessel_name,
                        'eta': op.eta.strftime('%H:%M') if op.eta else None,
                        'progress': op.get_progress_percentage()
                    }
        except Exception as e:
            logger.error(f"Berth status calculation error: {e}")
        
        # Real KPI statistics from MaritimeOperation data with error handling
        now = datetime.utcnow()
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        # Operations trend: Compare today vs yesterday
        try:
            operations_today = MaritimeOperation.query.filter(
                func.date(MaritimeOperation.created_at) == today
            ).count()
            operations_yesterday = MaritimeOperation.query.filter(
                func.date(MaritimeOperation.created_at) == yesterday
            ).count()
            
            operations_trend = 0
            if operations_yesterday > 0:
                operations_trend = int(((operations_today - operations_yesterday) / operations_yesterday) * 100)
            elif operations_today > 0:
                operations_trend = 100
        except Exception as e:
            logger.error(f"Operations trend calculation error: {e}")
            operations_trend = 0
        
        # Berth utilization: Count operations with berth_assigned / 3 berths * 100
        try:
            berths_occupied = MaritimeOperation.query.filter(
                MaritimeOperation.berth_assigned.isnot(None),
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).count()
            berth_utilization = min(int((berths_occupied / 3) * 100), 100) if berths_occupied >= 0 else 0
        except Exception as e:
            logger.error(f"Berth utilization calculation error: {e}")
            berths_occupied = 0
            berth_utilization = 0
        
        # Cargo throughput: Sum cargo_weight from completed operations today / total hours
        try:
            completed_today = MaritimeOperation.query.filter(
                func.date(MaritimeOperation.completed_at) == today,
                MaritimeOperation.status == 'completed'
            ).all()
            
            total_weight = sum(op.cargo_weight or 0 for op in completed_today)
            total_hours = sum(op.actual_duration or 0 for op in completed_today)
            
            cargo_throughput = 0
            if total_hours > 0:
                cargo_throughput = int(total_weight / total_hours)
        except Exception as e:
            logger.error(f"Cargo throughput calculation error: {e}")
            cargo_throughput = 0
        
        # Calculate throughput trend (today vs yesterday)
        try:
            completed_yesterday = MaritimeOperation.query.filter(
                func.date(MaritimeOperation.completed_at) == yesterday,
                MaritimeOperation.status == 'completed'
            ).all()
            
            yesterday_weight = sum(op.cargo_weight or 0 for op in completed_yesterday)
            yesterday_hours = sum(op.actual_duration or 0 for op in completed_yesterday)
            
            yesterday_throughput = 0
            if yesterday_hours > 0:
                yesterday_throughput = yesterday_weight / yesterday_hours
            
            throughput_trend = 0
            if yesterday_throughput > 0:
                throughput_trend = int(((cargo_throughput - yesterday_throughput) / yesterday_throughput) * 100)
            elif cargo_throughput > 0:
                throughput_trend = 100
        except Exception as e:
            logger.error(f"Throughput trend calculation error: {e}")
            throughput_trend = 0
        
        # Average turnaround: Average actual_duration from completed operations last 7 days
        try:
            completed_week = MaritimeOperation.query.filter(
                func.date(MaritimeOperation.completed_at) >= week_ago,
                MaritimeOperation.status == 'completed',
                MaritimeOperation.actual_duration.isnot(None)
            ).all()
            
            avg_turnaround = 0
            if completed_week:
                avg_turnaround = int(sum(op.actual_duration for op in completed_week) / len(completed_week))
        except Exception as e:
            logger.error(f"Average turnaround calculation error: {e}")
            avg_turnaround = 0
        
        # Turnaround improvement: Compare current week vs previous week
        try:
            two_weeks_ago = week_ago - timedelta(days=7)
            completed_prev_week = MaritimeOperation.query.filter(
                func.date(MaritimeOperation.completed_at) >= two_weeks_ago,
                func.date(MaritimeOperation.completed_at) < week_ago,
                MaritimeOperation.status == 'completed',
                MaritimeOperation.actual_duration.isnot(None)
            ).all()
            
            turnaround_improvement = 0
            if completed_prev_week:
                prev_avg = sum(op.actual_duration for op in completed_prev_week) / len(completed_prev_week)
                if prev_avg > 0 and avg_turnaround > 0:
                    turnaround_improvement = int(((prev_avg - avg_turnaround) / prev_avg) * 100)
        except Exception as e:
            logger.error(f"Turnaround improvement calculation error: {e}")
            turnaround_improvement = 0
        
        kpi_stats = {
            'operations_trend': operations_trend,
            'berth_utilization': berth_utilization,
            'berths_occupied': berths_occupied,
            'cargo_throughput': cargo_throughput,
            'throughput_trend': throughput_trend,
            'avg_turnaround': avg_turnaround,
            'turnaround_improvement': turnaround_improvement
        }
        
        # Real active teams data based on actual team assignments
        active_teams = []
        try:
            team_assignments = {}
            
            # Group operations by team leads to create team data
            for op in active_operations:
                if op.operation_manager:
                    team_key = op.operation_manager
                    if team_key not in team_assignments:
                        team_assignments[team_key] = {
                            'operations': [],
                            'auto_ops_lead': op.auto_ops_lead,
                            'heavy_ops_lead': op.heavy_ops_lead,
                            'auto_ops_assistant': op.auto_ops_assistant,
                            'heavy_ops_assistant': op.heavy_ops_assistant
                        }
                    team_assignments[team_key]['operations'].append(op)
            
            # Create team data from assignments
            for idx, (manager, team_data) in enumerate(team_assignments.items(), 1):
                operations = team_data['operations']
                total_cargo = sum(op.cargo_weight or 0 for op in operations)
                
                # Count active team members
                members = set()
                for op in operations:
                    if op.operation_manager:
                        members.add(op.operation_manager)
                    if op.auto_ops_lead:
                        members.add(op.auto_ops_lead)
                    if op.heavy_ops_lead:
                        members.add(op.heavy_ops_lead)
                    if op.auto_ops_assistant:
                        members.add(op.auto_ops_assistant)
                    if op.heavy_ops_assistant:
                        members.add(op.heavy_ops_assistant)
                
                # Calculate efficiency based on progress
                avg_progress = sum(op.get_progress_percentage() for op in operations) / len(operations) if operations else 0
                
                team = {
                    'id': idx,
                    'team_name': f'Team {manager}',
                    'status': 'active',
                    'cargo_processed_today': int(total_cargo),
                    'efficiency_rating': int(avg_progress),
                    'active_members_count': len(members),
                    'current_operation': operations[0] if operations else None
                }
                active_teams.append(team)
                
        except Exception as e:
            logger.error(f"Active teams calculation error: {e}")
        
        # If no teams found, create default empty team structure
        if not active_teams:
            active_teams = [{
                'id': 1,
                'team_name': 'No Active Teams',
                'status': 'inactive',
                'cargo_processed_today': 0,
                'efficiency_rating': 0,
                'active_members_count': 0,
                'current_operation': None
            }]
        
        # Run alert generation checks
        try:
            if AlertGenerator:
                AlertGenerator.run_all_checks()
        except Exception as e:
            logger.error(f"Alert generation error: {e}")
        
        # Get real alerts data
        alerts = Alert.get_active_alerts(limit=10) if Alert else []
        alert_stats = Alert.get_alert_statistics() if Alert else {}
        
        # Convert alerts to dict format for template
        alerts_dict = [alert.to_dict() for alert in alerts] if alerts else []
        
        return render_template('dashboard/operations.html',
            active_operations=active_operations,
            active_operations_count=len(active_operations),
            vessel_queue=vessel_queue,
            berth_status=berth_status,
            kpi_stats=kpi_stats,
            active_teams=active_teams,
            alerts=alerts_dict,
            alert_stats=alert_stats
        )
        
    except Exception as e:
        logger.error(f"Operations dashboard error: {e}")
        flash('An error occurred loading operations dashboard', 'error')
        return render_template('dashboard/error.html'), 500