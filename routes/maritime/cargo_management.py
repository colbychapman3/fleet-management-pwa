"""
Maritime Cargo Management API - Discharge tracking and cargo operations
Handles real-time cargo discharge, progress tracking, and zone management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import structlog
import json
from decimal import Decimal

# Access app components via current_app or direct import
def get_app_db():
    import app
    return app.db

def get_cache_functions():
    import app
    return app.cache_get, app.cache_set, app.cache_delete, app.get_cache_key

from models.models.enhanced_vessel import Vessel
from models.models.maritime_models import (
    CargoOperation, DischargeProgress, MaritimeDocument, 
    MaritimeOperationsHelper
)
from models.models.sync_log import SyncLog

logger = structlog.get_logger()

cargo_management_bp = Blueprint('cargo_management', __name__)

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

@cargo_management_bp.route('/<int:operation_id>', methods=['GET'])
@login_required
@maritime_access_required()
def get_cargo_operations(operation_id):
    """
    Get all cargo operations for a vessel
    GET /api/maritime/cargo/{operation_id}
    """
    try:
        vessel = Vessel.query.get_or_404(operation_id)
        
        # Get all cargo operations for this vessel
        cargo_operations = CargoOperation.query.filter_by(vessel_id=vessel.id).all()
        
        # Group by zone for better organization
        cargo_by_zone = {}
        total_stats = {
            'total_quantity': 0,
            'total_discharged': 0,
            'remaining': 0,
            'progress_percentage': 0
        }
        
        for cargo_op in cargo_operations:
            zone = cargo_op.zone or 'General'
            if zone not in cargo_by_zone:
                cargo_by_zone[zone] = {
                    'zone': zone,
                    'operations': [],
                    'zone_stats': {
                        'total_quantity': 0,
                        'discharged': 0,
                        'remaining': 0,
                        'progress_percentage': 0
                    }
                }
            
            cargo_dict = cargo_op.to_dict()
            cargo_by_zone[zone]['operations'].append(cargo_dict)
            
            # Update zone stats
            cargo_by_zone[zone]['zone_stats']['total_quantity'] += cargo_op.quantity or 0
            cargo_by_zone[zone]['zone_stats']['discharged'] += cargo_op.discharged
            
            # Update total stats
            total_stats['total_quantity'] += cargo_op.quantity or 0
            total_stats['total_discharged'] += cargo_op.discharged
        
        # Calculate percentages
        for zone_data in cargo_by_zone.values():
            zone_stats = zone_data['zone_stats']
            zone_stats['remaining'] = zone_stats['total_quantity'] - zone_stats['discharged']
            if zone_stats['total_quantity'] > 0:
                zone_stats['progress_percentage'] = (zone_stats['discharged'] / zone_stats['total_quantity']) * 100
        
        total_stats['remaining'] = total_stats['total_quantity'] - total_stats['total_discharged']
        if total_stats['total_quantity'] > 0:
            total_stats['progress_percentage'] = (total_stats['total_discharged'] / total_stats['total_quantity']) * 100
        
        # Get recent discharge progress
        recent_progress = DischargeProgress.query.filter_by(vessel_id=vessel.id)\
                                                .order_by(DischargeProgress.timestamp.desc())\
                                                .limit(10).all()
        
        return jsonify({
            'vessel_id': vessel.id,
            'vessel_name': vessel.name,
            'cargo_by_zone': list(cargo_by_zone.values()),
            'total_stats': total_stats,
            'recent_progress': [p.to_dict() for p in recent_progress],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get cargo operations error: {e}")
        return jsonify({'error': 'Failed to retrieve cargo operations'}), 500

@cargo_management_bp.route('/<int:operation_id>/discharge', methods=['POST'])
@login_required
@maritime_access_required()
def record_discharge(operation_id):
    """
    Record cargo discharge progress
    POST /api/maritime/cargo/{operation_id}/discharge
    """
    try:
        vessel = Vessel.query.get_or_404(operation_id)
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['discharge_data']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        discharge_data = data['discharge_data']
        db = get_app_db()
        updated_operations = []
        
        # Process each discharge record
        for discharge_item in discharge_data:
            cargo_op_id = discharge_item.get('cargo_operation_id')
            discharged_amount = discharge_item.get('discharged_amount', 0)
            
            if not cargo_op_id:
                continue
            
            cargo_op = CargoOperation.query.get(cargo_op_id)
            if not cargo_op or cargo_op.vessel_id != vessel.id:
                continue
            
            # Validate discharge amount
            if discharged_amount < 0:
                return jsonify({'error': 'Discharge amount cannot be negative'}), 400
            
            remaining = cargo_op.remaining_quantity()
            if discharged_amount > remaining:
                return jsonify({
                    'error': f'Discharge amount ({discharged_amount}) exceeds remaining quantity ({remaining}) for operation {cargo_op_id}'
                }), 400
            
            # Update cargo operation
            old_discharged = cargo_op.discharged
            cargo_op.discharged += discharged_amount
            cargo_op.updated_at = datetime.utcnow()
            
            updated_operations.append({
                'cargo_operation_id': cargo_op.id,
                'previous_discharged': old_discharged,
                'new_discharged': cargo_op.discharged,
                'amount_added': discharged_amount,
                'progress_percentage': cargo_op.get_progress_percentage()
            })
            
            # Log the change
            SyncLog.log_action(
                user_id=current_user.id,
                action='update',
                table_name='cargo_operations',
                record_id=cargo_op.id,
                data_after={'discharged': cargo_op.discharged, 'timestamp': datetime.utcnow().isoformat()}
            )
        
        # Create overall discharge progress entry
        if data.get('zone_progress'):
            zone_progress = data['zone_progress']
            
            progress_entry = DischargeProgress(
                vessel_id=vessel.id,
                zone=zone_progress.get('zone', 'General'),
                timestamp=datetime.utcnow(),
                vehicles_discharged=zone_progress.get('vehicles_discharged', 0),
                hourly_rate=Decimal(str(zone_progress.get('hourly_rate', 0.0))),
                total_progress=Decimal(str(zone_progress.get('total_progress', 0.0))),
                created_by=current_user.id
            )
            db.session.add(progress_entry)
        
        db.session.commit()
        
        # Calculate updated vessel statistics
        total_quantity = sum(co.quantity or 0 for co in vessel.cargo_operations)
        total_discharged = sum(co.discharged for co in vessel.cargo_operations)
        overall_progress = (total_discharged / total_quantity * 100) if total_quantity > 0 else 0
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('cargo_operations', vessel.id, '*'))
        cache_delete(get_cache_key('discharge_progress', vessel.id, '*'))
        
        logger.info(f"Discharge recorded for vessel {vessel.id} by user {current_user.id}")
        
        return jsonify({
            'message': 'Discharge recorded successfully',
            'updated_operations': updated_operations,
            'vessel_stats': {
                'total_quantity': total_quantity,
                'total_discharged': total_discharged,
                'remaining': total_quantity - total_discharged,
                'overall_progress': round(overall_progress, 2)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Record discharge error: {e}")
        return jsonify({'error': 'Failed to record discharge'}), 500

@cargo_management_bp.route('/<int:operation_id>/progress', methods=['GET'])
@login_required
@maritime_access_required()
def get_discharge_progress(operation_id):
    """
    Get discharge progress history for a vessel
    GET /api/maritime/cargo/{operation_id}/progress
    """
    try:
        vessel = Vessel.query.get_or_404(operation_id)
        
        # Get query parameters
        zone = request.args.get('zone')
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = DischargeProgress.query.filter_by(vessel_id=vessel.id)
        
        # Apply zone filter
        if zone:
            query = query.filter_by(zone=zone)
        
        # Apply time filter
        if hours > 0:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(DischargeProgress.timestamp >= cutoff_time)
        
        # Order by timestamp and limit
        progress_records = query.order_by(DischargeProgress.timestamp.desc())\
                               .limit(limit).all()
        
        # Calculate analytics
        analytics = {
            'average_hourly_rate': 0,
            'peak_hourly_rate': 0,
            'total_vehicles_discharged': 0,
            'progress_trend': 'stable'
        }
        
        if progress_records:
            # Calculate average hourly rate
            rates = [float(p.hourly_rate) for p in progress_records if p.hourly_rate]
            if rates:
                analytics['average_hourly_rate'] = sum(rates) / len(rates)
                analytics['peak_hourly_rate'] = max(rates)
            
            # Get latest total vehicles discharged
            latest_record = progress_records[0]
            analytics['total_vehicles_discharged'] = latest_record.vehicles_discharged or 0
            
            # Calculate trend (comparing first half vs second half of records)
            if len(progress_records) >= 4:
                mid_point = len(progress_records) // 2
                recent_avg = sum(float(p.hourly_rate or 0) for p in progress_records[:mid_point]) / mid_point
                older_avg = sum(float(p.hourly_rate or 0) for p in progress_records[mid_point:]) / (len(progress_records) - mid_point)
                
                if recent_avg > older_avg * 1.1:
                    analytics['progress_trend'] = 'improving'
                elif recent_avg < older_avg * 0.9:
                    analytics['progress_trend'] = 'declining'
        
        # Get zone breakdown
        zone_breakdown = {}
        for zone_name in ['BRV', 'ZEE', 'SOU', 'General']:
            zone_progress = DischargeProgress.query.filter_by(
                vessel_id=vessel.id, 
                zone=zone_name
            ).order_by(DischargeProgress.timestamp.desc()).first()
            
            if zone_progress:
                zone_breakdown[zone_name] = zone_progress.to_dict()
        
        return jsonify({
            'vessel_id': vessel.id,
            'vessel_name': vessel.name,
            'progress_records': [p.to_dict() for p in progress_records],
            'analytics': analytics,
            'zone_breakdown': zone_breakdown,
            'query_params': {
                'zone': zone,
                'hours': hours,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get discharge progress error: {e}")
        return jsonify({'error': 'Failed to retrieve discharge progress'}), 500

@cargo_management_bp.route('/<int:operation_id>/zones', methods=['GET'])
@login_required
@maritime_access_required()
def get_zone_summary(operation_id):
    """
    Get comprehensive zone summary for a vessel
    GET /api/maritime/cargo/{operation_id}/zones
    """
    try:
        vessel = Vessel.query.get_or_404(operation_id)
        
        # Use the helper to get zone summary
        zone_summary = MaritimeOperationsHelper.get_zone_summary(vessel.id)
        
        # Add recent progress for each zone
        for zone_name, zone_data in zone_summary.items():
            recent_progress = DischargeProgress.query.filter_by(
                vessel_id=vessel.id,
                zone=zone_name
            ).order_by(DischargeProgress.timestamp.desc()).limit(5).all()
            
            zone_data['recent_progress'] = [p.to_dict() for p in recent_progress]
            
            # Calculate zone analytics
            if recent_progress:
                zone_data['analytics'] = {
                    'latest_hourly_rate': float(recent_progress[0].hourly_rate or 0),
                    'average_hourly_rate': sum(float(p.hourly_rate or 0) for p in recent_progress) / len(recent_progress),
                    'last_update': recent_progress[0].timestamp.isoformat()
                }
            else:
                zone_data['analytics'] = {
                    'latest_hourly_rate': 0,
                    'average_hourly_rate': 0,
                    'last_update': None
                }
        
        # Calculate overall vessel statistics
        overall_stats = {
            'total_zones': len(zone_summary),
            'zones_complete': sum(1 for zd in zone_summary.values() if zd['progress_percentage'] >= 100),
            'zones_active': sum(1 for zd in zone_summary.values() if 0 < zd['progress_percentage'] < 100),
            'zones_pending': sum(1 for zd in zone_summary.values() if zd['progress_percentage'] == 0)
        }
        
        return jsonify({
            'vessel_id': vessel.id,
            'vessel_name': vessel.name,
            'zone_summary': zone_summary,
            'overall_stats': overall_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get zone summary error: {e}")
        return jsonify({'error': 'Failed to retrieve zone summary'}), 500

@cargo_management_bp.route('/<int:operation_id>/bulk-update', methods=['PUT'])
@login_required
@maritime_access_required(['manager', 'maritime_supervisor'])
def bulk_update_cargo(operation_id):
    """
    Bulk update multiple cargo operations
    PUT /api/maritime/cargo/{operation_id}/bulk-update
    """
    try:
        vessel = Vessel.query.get_or_404(operation_id)
        data = request.get_json()
        
        # Validate required fields
        if not data.get('updates'):
            return jsonify({'error': 'updates array is required'}), 400
        
        updates = data['updates']
        db = get_app_db()
        updated_operations = []
        
        for update in updates:
            cargo_op_id = update.get('cargo_operation_id')
            if not cargo_op_id:
                continue
            
            cargo_op = CargoOperation.query.get(cargo_op_id)
            if not cargo_op or cargo_op.vessel_id != vessel.id:
                continue
            
            # Store original data for logging
            original_data = cargo_op.to_dict()
            
            # Apply updates
            updatable_fields = ['quantity', 'discharged', 'location', 'zone']
            for field in updatable_fields:
                if field in update:
                    setattr(cargo_op, field, update[field])
            
            cargo_op.updated_at = datetime.utcnow()
            
            # Log the change
            SyncLog.log_action(
                user_id=current_user.id,
                action='update',
                table_name='cargo_operations',
                record_id=cargo_op.id,
                data_before=original_data,
                data_after=cargo_op.to_dict()
            )
            
            updated_operations.append(cargo_op.to_dict())
        
        db.session.commit()
        
        # Clear relevant caches
        cache_get, cache_set, cache_delete, get_cache_key = get_cache_functions()
        cache_delete(get_cache_key('cargo_operations', vessel.id, '*'))
        
        logger.info(f"Bulk cargo update for vessel {vessel.id} by user {current_user.id}")
        
        return jsonify({
            'message': f'Successfully updated {len(updated_operations)} cargo operations',
            'updated_operations': updated_operations,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        db = get_app_db()
        db.session.rollback()
        logger.error(f"Bulk update cargo error: {e}")
        return jsonify({'error': 'Failed to bulk update cargo operations'}), 500

@cargo_management_bp.route('/<int:operation_id>/export', methods=['GET'])
@login_required
@maritime_access_required()
def export_cargo_data(operation_id):
    """
    Export cargo data for external systems
    GET /api/maritime/cargo/{operation_id}/export?format=json
    """
    try:
        vessel = Vessel.query.get_or_404(operation_id)
        export_format = request.args.get('format', 'json')
        
        # Get comprehensive cargo data
        cargo_operations = CargoOperation.query.filter_by(vessel_id=vessel.id).all()
        discharge_progress = DischargeProgress.query.filter_by(vessel_id=vessel.id)\
                                                   .order_by(DischargeProgress.timestamp.asc()).all()
        
        export_data = {
            'vessel_info': vessel.to_dict(),
            'cargo_operations': [co.to_dict() for co in cargo_operations],
            'discharge_progress': [dp.to_dict() for dp in discharge_progress],
            'zone_summary': MaritimeOperationsHelper.get_zone_summary(vessel.id),
            'export_metadata': {
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': current_user.username,
                'total_operations': len(cargo_operations),
                'total_progress_records': len(discharge_progress)
            }
        }
        
        if export_format.lower() == 'csv':
            # For CSV format, flatten the data structure
            return jsonify({
                'message': 'CSV export not yet implemented',
                'available_formats': ['json'],
                'data_preview': export_data
            })
        
        logger.info(f"Cargo data exported for vessel {vessel.id} by user {current_user.id}")
        
        return jsonify(export_data)
        
    except Exception as e:
        logger.error(f"Export cargo data error: {e}")
        return jsonify({'error': 'Failed to export cargo data'}), 500

@cargo_management_bp.route('/<int:operation_id>/analytics', methods=['GET'])
@login_required
@maritime_access_required()
def get_cargo_analytics(operation_id):
    """
    Get advanced analytics for cargo operations
    GET /api/maritime/cargo/{operation_id}/analytics
    """
    try:
        vessel = Vessel.query.get_or_404(operation_id)
        
        # Calculate comprehensive analytics
        cargo_operations = CargoOperation.query.filter_by(vessel_id=vessel.id).all()
        discharge_progress = DischargeProgress.query.filter_by(vessel_id=vessel.id)\
                                                   .order_by(DischargeProgress.timestamp.asc()).all()
        
        analytics = {
            'efficiency_metrics': {
                'average_hourly_rate': 0,
                'peak_hourly_rate': 0,
                'total_hours_worked': 0,
                'efficiency_score': 0
            },
            'completion_metrics': {
                'total_vehicles': sum(co.quantity or 0 for co in cargo_operations),
                'discharged_vehicles': sum(co.discharged for co in cargo_operations),
                'completion_percentage': 0,
                'estimated_completion': None
            },
            'zone_performance': {},
            'trend_analysis': {
                'hourly_rates': [],
                'cumulative_progress': [],
                'performance_trend': 'stable'
            }
        }
        
        # Calculate efficiency metrics
        if discharge_progress:
            hourly_rates = [float(dp.hourly_rate or 0) for dp in discharge_progress]
            if hourly_rates:
                analytics['efficiency_metrics']['average_hourly_rate'] = sum(hourly_rates) / len(hourly_rates)
                analytics['efficiency_metrics']['peak_hourly_rate'] = max(hourly_rates)
            
            # Calculate total hours worked
            if len(discharge_progress) > 1:
                time_span = discharge_progress[-1].timestamp - discharge_progress[0].timestamp
                analytics['efficiency_metrics']['total_hours_worked'] = time_span.total_seconds() / 3600
        
        # Calculate completion metrics
        total_vehicles = analytics['completion_metrics']['total_vehicles']
        discharged_vehicles = analytics['completion_metrics']['discharged_vehicles']
        
        if total_vehicles > 0:
            completion_percentage = (discharged_vehicles / total_vehicles) * 100
            analytics['completion_metrics']['completion_percentage'] = round(completion_percentage, 2)
            
            # Calculate efficiency score (0-100)
            expected_rate = vessel.expected_rate or 150
            actual_rate = analytics['efficiency_metrics']['average_hourly_rate']
            if expected_rate > 0:
                analytics['efficiency_metrics']['efficiency_score'] = min(100, (actual_rate / expected_rate) * 100)
        
        # Calculate estimated completion
        estimated_completion = MaritimeOperationsHelper.calculate_estimated_completion(vessel.id)
        if estimated_completion:
            analytics['completion_metrics']['estimated_completion'] = estimated_completion.isoformat()
        
        # Zone performance analysis
        zone_summary = MaritimeOperationsHelper.get_zone_summary(vessel.id)
        for zone_name, zone_data in zone_summary.items():
            zone_progress_records = DischargeProgress.query.filter_by(
                vessel_id=vessel.id, zone=zone_name
            ).order_by(DischargeProgress.timestamp.asc()).all()
            
            zone_hourly_rates = [float(dp.hourly_rate or 0) for dp in zone_progress_records]
            analytics['zone_performance'][zone_name] = {
                'completion_percentage': zone_data['progress_percentage'],
                'average_hourly_rate': sum(zone_hourly_rates) / len(zone_hourly_rates) if zone_hourly_rates else 0,
                'total_vehicles': zone_data['total_quantity'],
                'discharged_vehicles': zone_data['discharged']
            }
        
        # Trend analysis
        if len(discharge_progress) >= 2:
            analytics['trend_analysis']['hourly_rates'] = [
                {
                    'timestamp': dp.timestamp.isoformat(),
                    'rate': float(dp.hourly_rate or 0)
                }
                for dp in discharge_progress[-20:]  # Last 20 records
            ]
            
            analytics['trend_analysis']['cumulative_progress'] = [
                {
                    'timestamp': dp.timestamp.isoformat(),
                    'progress': float(dp.total_progress or 0)
                }
                for dp in discharge_progress[-20:]  # Last 20 records
            ]
            
            # Determine performance trend
            if len(discharge_progress) >= 6:
                recent_rates = [float(dp.hourly_rate or 0) for dp in discharge_progress[-3:]]
                older_rates = [float(dp.hourly_rate or 0) for dp in discharge_progress[-6:-3]]
                
                recent_avg = sum(recent_rates) / len(recent_rates) if recent_rates else 0
                older_avg = sum(older_rates) / len(older_rates) if older_rates else 0
                
                if recent_avg > older_avg * 1.1:
                    analytics['trend_analysis']['performance_trend'] = 'improving'
                elif recent_avg < older_avg * 0.9:
                    analytics['trend_analysis']['performance_trend'] = 'declining'
        
        logger.info(f"Cargo analytics generated for vessel {vessel.id} by user {current_user.id}")
        
        return jsonify({
            'vessel_id': vessel.id,
            'vessel_name': vessel.name,
            'analytics': analytics,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get cargo analytics error: {e}")
        return jsonify({'error': 'Failed to generate cargo analytics'}), 500