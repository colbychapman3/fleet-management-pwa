"""
Monitoring and health check routes
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import psutil
import structlog

def get_app_db():
    import app
    return app.db

def get_app_components():
    import app
    return app.db, app.redis_client, app.metrics
from models.models.enhanced_user import User
from models.models.enhanced_task import Task
from models.models.enhanced_vessel import Vessel
from models.models.sync_log import SyncLog

logger = structlog.get_logger()

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/health')
def health():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@monitoring_bp.route('/health/detailed')
def health_detailed():
    """Detailed health check with dependencies"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'dependencies': {},
        'metrics': {}
    }
    
    # Get app components
    db, redis_client, metrics = get_app_components()
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        db_connections = db.engine.pool.checkedout()
        health_status['dependencies']['database'] = {
            'status': 'healthy',
            'connections_active': db_connections
        }
        health_status['metrics']['database_connections'] = db_connections
    except Exception as e:
        health_status['dependencies']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        if redis_client:
            redis_info = redis_client.ping()
            memory_info = redis_client.info('memory')
            health_status['dependencies']['redis'] = {
                'status': 'healthy',
                'memory_used': memory_info.get('used_memory_human'),
                'connected_clients': redis_client.info('clients').get('connected_clients')
            }
        else:
            health_status['dependencies']['redis'] = {
                'status': 'unavailable',
                'message': 'Redis client not initialized'
            }
    except Exception as e:
        health_status['dependencies']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status['metrics']['system'] = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available // 1024 // 1024,
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free // 1024 // 1024 // 1024
        }
        
        # Alert if resources are critically low
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            health_status['status'] = 'warning'
            
    except Exception as e:
        health_status['metrics']['system_error'] = str(e)
    
    # Application metrics
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_tasks = Task.query.count()
        pending_tasks = Task.query.filter_by(status='pending').count()
        overdue_tasks = len(Task.get_overdue_tasks())
        pending_syncs = len(SyncLog.get_pending_syncs())
        
        health_status['metrics']['application'] = {
            'total_users': total_users,
            'active_users': active_users,
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'pending_syncs': pending_syncs
        }
        
        # Update Prometheus metrics
        db, redis_client, metrics = get_app_components()
        metrics.gauge('active_users_total').set(active_users)
        
    except Exception as e:
        health_status['metrics']['application_error'] = str(e)
    
    return jsonify(health_status)

@monitoring_bp.route('/metrics/prometheus')
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        # Get app components
        db, redis_client, metrics = get_app_components()
        
        # Update custom metrics before returning
        active_users = User.query.filter_by(is_active=True).count()
        pending_tasks = Task.query.filter_by(status='pending').count()
        overdue_tasks = len(Task.get_overdue_tasks())
        pending_syncs = len(SyncLog.get_pending_syncs())
        
        # Update gauges
        metrics.gauge('active_users_total').set(active_users)
        metrics.gauge('pending_tasks_total').set(pending_tasks)
        metrics.gauge('overdue_tasks_total').set(overdue_tasks)
        metrics.gauge('pending_syncs_total').set(pending_syncs)
        
        # Database connections
        try:
            db_connections = db.engine.pool.checkedout()
            metrics.gauge('database_connections_active').set(db_connections)
        except:
            pass
        
        # The prometheus_flask_exporter handles the actual metrics output
        return metrics.generate_latest()
        
    except Exception as e:
        logger.error(f"Prometheus metrics error: {e}")
        return "# Error generating metrics\n", 500

@monitoring_bp.route('/metrics/application')
def application_metrics():
    """Application-specific metrics"""
    try:
        # Task statistics
        task_stats = Task.get_task_statistics()
        
        # User statistics
        user_stats = {
            'total': User.query.count(),
            'active': User.query.filter_by(is_active=True).count(),
            'managers': len(User.get_managers()),
            'workers': len(User.get_workers())
        }
        
        # Vessel statistics
        vessel_stats = {
            'total': Vessel.query.count(),
            'active': len(Vessel.get_active_vessels())
        }
        
        # Sync statistics
        sync_stats = SyncLog.get_sync_statistics()
        
        # Performance metrics
        overdue_tasks = Task.get_overdue_tasks()
        recent_activity = Task.query.filter(
            Task.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        # System load
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            system_stats = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except:
            system_stats = {'error': 'System metrics unavailable'}
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'tasks': task_stats,
            'users': user_stats,
            'vessels': vessel_stats,
            'sync': sync_stats,
            'performance': {
                'overdue_tasks': len(overdue_tasks),
                'recent_activity_24h': recent_activity
            },
            'system': system_stats
        })
        
    except Exception as e:
        logger.error(f"Application metrics error: {e}")
        return jsonify({'error': 'Failed to retrieve application metrics'}), 500

@monitoring_bp.route('/metrics/sync')
def sync_metrics():
    """Synchronization metrics"""
    try:
        # Overall sync statistics
        sync_stats = SyncLog.get_sync_statistics()
        
        # Failed syncs by user
        failed_syncs = SyncLog.get_failed_syncs()
        failed_by_user = {}
        for sync in failed_syncs:
            user_id = sync.user_id
            if user_id not in failed_by_user:
                failed_by_user[user_id] = 0
            failed_by_user[user_id] += 1
        
        # Sync activity over time (last 24 hours)
        time_windows = []
        now = datetime.utcnow()
        for i in range(24):
            window_start = now - timedelta(hours=i+1)
            window_end = now - timedelta(hours=i)
            
            window_syncs = SyncLog.query.filter(
                SyncLog.created_at >= window_start,
                SyncLog.created_at < window_end
            ).count()
            
            time_windows.append({
                'hour': window_start.strftime('%H:00'),
                'syncs': window_syncs
            })
        
        # Pending syncs by table
        pending_syncs = SyncLog.get_pending_syncs()
        pending_by_table = {}
        for sync in pending_syncs:
            table = sync.table_name
            if table not in pending_by_table:
                pending_by_table[table] = 0
            pending_by_table[table] += 1
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'overall': sync_stats,
            'failed_by_user': failed_by_user,
            'activity_24h': time_windows,
            'pending_by_table': pending_by_table,
            'unsynced_tasks': len(Task.get_unsynced_tasks())
        })
        
    except Exception as e:
        logger.error(f"Sync metrics error: {e}")
        return jsonify({'error': 'Failed to retrieve sync metrics'}), 500

@monitoring_bp.route('/metrics/performance')
def performance_metrics():
    """Performance and efficiency metrics"""
    try:
        # Task completion rates
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_tasks = Task.query.filter(Task.created_at >= thirty_days_ago).all()
        
        completed_on_time = len([
            t for t in recent_tasks 
            if t.status == 'completed' and t.due_date and t.completion_date <= t.due_date
        ])
        completed_late = len([
            t for t in recent_tasks 
            if t.status == 'completed' and t.due_date and t.completion_date > t.due_date
        ])
        
        # Average completion time
        completed_tasks = [t for t in recent_tasks if t.status == 'completed' and t.completion_date]
        if completed_tasks:
            avg_completion_hours = sum([
                (t.completion_date - t.created_at).total_seconds() / 3600 
                for t in completed_tasks
            ]) / len(completed_tasks)
        else:
            avg_completion_hours = 0
        
        # Worker productivity
        worker_productivity = []
        for user in User.get_workers():
            user_tasks = [t for t in recent_tasks if t.assigned_to_id == user.id]
            completed_user_tasks = [t for t in user_tasks if t.status == 'completed']
            
            worker_productivity.append({
                'user_id': user.id,
                'username': user.username,
                'total_assigned': len(user_tasks),
                'completed': len(completed_user_tasks),
                'completion_rate': len(completed_user_tasks) / len(user_tasks) if user_tasks else 0,
                'avg_hours': sum(t.actual_hours or 0 for t in completed_user_tasks) / len(completed_user_tasks) if completed_user_tasks else 0
            })
        
        # Vessel efficiency
        vessel_efficiency = []
        for vessel in Vessel.get_active_vessels():
            vessel_tasks = [t for t in recent_tasks if t.vessel_id == vessel.id]
            completed_vessel_tasks = [t for t in vessel_tasks if t.status == 'completed']
            
            vessel_efficiency.append({
                'vessel_id': vessel.id,
                'vessel_name': vessel.name,
                'total_tasks': len(vessel_tasks),
                'completed': len(completed_vessel_tasks),
                'completion_rate': len(completed_vessel_tasks) / len(vessel_tasks) if vessel_tasks else 0
            })
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'period_days': 30,
            'completion_metrics': {
                'on_time': completed_on_time,
                'late': completed_late,
                'avg_completion_hours': round(avg_completion_hours, 2)
            },
            'worker_productivity': worker_productivity,
            'vessel_efficiency': vessel_efficiency,
            'current_overdue': len(Task.get_overdue_tasks())
        })
        
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        return jsonify({'error': 'Failed to retrieve performance metrics'}), 500

@monitoring_bp.route('/logs')
def recent_logs():
    """Recent application logs and events"""
    try:
        # Get recent sync logs
        recent_syncs = SyncLog.query.order_by(
            SyncLog.created_at.desc()
        ).limit(50).all()
        
        # Get recent task updates
        recent_tasks = Task.query.order_by(
            Task.updated_at.desc()
        ).limit(20).all()
        
        # Get recent user logins
        recent_logins = User.query.filter(
            User.last_login >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(User.last_login.desc()).all()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'recent_syncs': [sync.to_dict() for sync in recent_syncs],
            'recent_task_updates': [
                {
                    'id': task.id,
                    'title': task.title,
                    'status': task.status,
                    'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                    'assigned_to': task.assigned_to.username if task.assigned_to else None
                } for task in recent_tasks
            ],
            'recent_logins': [
                {
                    'user_id': user.id,
                    'username': user.username,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                } for user in recent_logins
            ]
        })
        
    except Exception as e:
        logger.error(f"Recent logs error: {e}")
        return jsonify({'error': 'Failed to retrieve recent logs'}), 500

@monitoring_bp.route('/alerts')
def get_alerts():
    """Get system alerts and warnings"""
    try:
        alerts = []
        
        # Check for overdue tasks
        overdue_tasks = Task.get_overdue_tasks()
        if overdue_tasks:
            alerts.append({
                'type': 'warning',
                'category': 'tasks',
                'message': f'{len(overdue_tasks)} tasks are overdue',
                'count': len(overdue_tasks),
                'severity': 'high' if len(overdue_tasks) > 10 else 'medium'
            })
        
        # Check for failed syncs
        failed_syncs = SyncLog.get_failed_syncs()
        if failed_syncs:
            alerts.append({
                'type': 'error',
                'category': 'sync',
                'message': f'{len(failed_syncs)} sync operations have failed',
                'count': len(failed_syncs),
                'severity': 'high' if len(failed_syncs) > 5 else 'medium'
            })
        
        # Check for system resources
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                alerts.append({
                    'type': 'warning',
                    'category': 'system',
                    'message': f'High memory usage: {memory.percent:.1f}%',
                    'severity': 'high'
                })
            
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                alerts.append({
                    'type': 'warning',
                    'category': 'system',
                    'message': f'High disk usage: {disk.percent:.1f}%',
                    'severity': 'high'
                })
        except:
            pass
        
        # Check for database connectivity
        try:
            db, redis_client, metrics = get_app_components()
            db.session.execute('SELECT 1')
        except Exception as e:
            alerts.append({
                'type': 'error',
                'category': 'database',
                'message': f'Database connectivity issue: {str(e)[:100]}',
                'severity': 'critical'
            })
        
        # Check for Redis connectivity
        try:
            if redis_client:
                redis_client.ping()
        except Exception as e:
            alerts.append({
                'type': 'warning',
                'category': 'redis',
                'message': f'Redis connectivity issue: {str(e)[:100]}',
                'severity': 'medium'
            })
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'alerts': alerts,
            'total_alerts': len(alerts),
            'critical_count': len([a for a in alerts if a.get('severity') == 'critical']),
            'high_count': len([a for a in alerts if a.get('severity') == 'high'])
        })
        
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return jsonify({'error': 'Failed to retrieve alerts'}), 500