"""
Alert system for stevedoring operations monitoring
"""

from datetime import datetime, timedelta
from app import db
from sqlalchemy import and_, or_
import uuid
import random
import structlog

logger = structlog.get_logger()

class Alert(db.Model):
    """Alert model for stevedoring operations"""
    
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default='info', index=True)  # info, warning, error, critical
    icon = db.Column(db.String(50), default='alert-circle')
    operation_id = db.Column(db.Integer, db.ForeignKey('maritime_operations.id'), nullable=True, index=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    alert_type = db.Column(db.String(50), nullable=False, index=True)  # berth_capacity, operation_delay, safety_violation, equipment_failure, etc.
    alert_code = db.Column(db.String(20), nullable=False, index=True)  # Unique identifier for alert type
    alert_metadata = db.Column(db.Text)  # JSON string for additional alert-specific data
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    dismissed_at = db.Column(db.DateTime, nullable=True, index=True)
    dismissed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    auto_dismiss_at = db.Column(db.DateTime, nullable=True, index=True)  # For auto-expiring alerts
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    # Use back_populates instead of backref to avoid conflicts and provide better control
    # Use string references to avoid import order issues
    operation = db.relationship('MaritimeOperation', back_populates='alerts', lazy='select')
    vessel = db.relationship('Vessel', back_populates='alerts', lazy='select')
    user = db.relationship('User', foreign_keys=[user_id], back_populates='user_alerts', lazy='select')
    dismissed_by_user = db.relationship('User', foreign_keys=[dismissed_by], back_populates='dismissed_alerts', lazy='select')
    
    def __repr__(self):
        return f'<Alert {self.id}: {self.title} ({self.severity})>'
    
    def is_dismissed(self):
        """Check if alert has been dismissed"""
        return self.dismissed_at is not None
    
    def is_expired(self):
        """Check if alert has auto-expired"""
        return self.auto_dismiss_at is not None and datetime.utcnow() > self.auto_dismiss_at
    
    def is_displayable(self):
        """Check if alert should be displayed (active, not dismissed, not expired)"""
        return (self.is_active and 
                not self.is_dismissed() and 
                not self.is_expired())
    
    def get_age_minutes(self):
        """Get alert age in minutes"""
        return int((datetime.utcnow() - self.created_at).total_seconds() / 60)
    
    def get_metadata(self):
        """Get metadata as dictionary"""
        if self.alert_metadata:
            try:
                import json
                return json.loads(self.alert_metadata)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_metadata(self, data):
        """Set metadata from dictionary"""
        if data:
            import json
            self.alert_metadata = json.dumps(data)
        else:
            self.alert_metadata = None
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'severity': self.severity,
            'icon': self.icon,
            'operation_id': self.operation_id,
            'vessel_id': self.vessel_id,
            'user_id': self.user_id,
            'alert_type': self.alert_type,
            'alert_code': self.alert_code,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat(),
            'dismissed_at': self.dismissed_at.isoformat() if self.dismissed_at else None,
            'dismissed_by': self.dismissed_by,
            'auto_dismiss_at': self.auto_dismiss_at.isoformat() if self.auto_dismiss_at else None,
            'is_active': self.is_active,
            'is_dismissed': self.is_dismissed(),
            'is_expired': self.is_expired(),
            'age_minutes': self.get_age_minutes()
        }
    
    @classmethod
    def create_alert(cls, title, message, severity='info', icon='alert-circle', 
                     operation_id=None, vessel_id=None, user_id=None, 
                     alert_type='general', alert_code=None, metadata=None,
                     auto_dismiss_hours=None):
        """Create a new alert"""
        try:
            # Generate alert code if not provided
            if not alert_code:
                alert_code = f"{alert_type}_{str(uuid.uuid4())[:8]}"
            
            # Check for duplicate active alerts with same code
            existing_alert = cls.query.filter_by(
                alert_code=alert_code,
                is_active=True
            ).filter(cls.dismissed_at.is_(None)).first()
            
            if existing_alert:
                logger.info(f"Alert with code {alert_code} already exists")
                return existing_alert
            
            # Create new alert
            alert = cls(
                title=title,
                message=message,
                severity=severity,
                icon=icon,
                operation_id=operation_id,
                vessel_id=vessel_id,
                user_id=user_id,
                alert_type=alert_type,
                alert_code=alert_code
            )
            
            # Set metadata if provided
            if metadata:
                alert.set_metadata(metadata)
            
            # Set auto-dismiss time if specified
            if auto_dismiss_hours:
                alert.auto_dismiss_at = datetime.utcnow() + timedelta(hours=auto_dismiss_hours)
            
            db.session.add(alert)
            db.session.commit()
            
            logger.info(f"Alert created: {alert.id} - {alert.title}")
            return alert
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating alert: {e}")
            raise
    
    @classmethod
    def dismiss_alert(cls, alert_id, user_id=None):
        """Dismiss a specific alert"""
        try:
            alert = cls.query.get(alert_id)
            if not alert:
                return False
            
            alert.dismissed_at = datetime.utcnow()
            alert.dismissed_by = user_id
            
            db.session.commit()
            
            logger.info(f"Alert dismissed: {alert_id} by user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error dismissing alert {alert_id}: {e}")
            return False
    
    @classmethod
    def get_active_alerts(cls, limit=50):
        """Get all active (non-dismissed, non-expired) alerts"""
        now = datetime.utcnow()
        return cls.query.filter(
            cls.is_active == True,
            cls.dismissed_at.is_(None),
            or_(cls.auto_dismiss_at.is_(None), cls.auto_dismiss_at > now)
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_alerts_for_operation(cls, operation_id, include_dismissed=False):
        """Get alerts for a specific operation"""
        query = cls.query.filter_by(operation_id=operation_id, is_active=True)
        
        if not include_dismissed:
            query = query.filter(cls.dismissed_at.is_(None))
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_alerts_for_vessel(cls, vessel_id, include_dismissed=False):
        """Get alerts for a specific vessel"""
        query = cls.query.filter_by(vessel_id=vessel_id, is_active=True)
        
        if not include_dismissed:
            query = query.filter(cls.dismissed_at.is_(None))
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_alerts_by_severity(cls, severity, limit=20):
        """Get alerts by severity level"""
        now = datetime.utcnow()
        return cls.query.filter(
            cls.severity == severity,
            cls.is_active == True,
            cls.dismissed_at.is_(None),
            or_(cls.auto_dismiss_at.is_(None), cls.auto_dismiss_at > now)
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_alerts_by_type(cls, alert_type, limit=20):
        """Get alerts by type"""
        now = datetime.utcnow()
        return cls.query.filter(
            cls.alert_type == alert_type,
            cls.is_active == True,
            cls.dismissed_at.is_(None),
            or_(cls.auto_dismiss_at.is_(None), cls.auto_dismiss_at > now)
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def cleanup_expired_alerts(cls, days_old=30):
        """Clean up old dismissed or expired alerts"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Mark old dismissed alerts as inactive
            dismissed_alerts = cls.query.filter(
                cls.dismissed_at < cutoff_date,
                cls.is_active == True
            ).all()
            
            for alert in dismissed_alerts:
                alert.is_active = False
            
            # Mark old expired alerts as inactive
            expired_alerts = cls.query.filter(
                cls.auto_dismiss_at < cutoff_date,
                cls.is_active == True
            ).all()
            
            for alert in expired_alerts:
                alert.is_active = False
            
            db.session.commit()
            
            total_cleaned = len(dismissed_alerts) + len(expired_alerts)
            logger.info(f"Cleaned up {total_cleaned} old alerts")
            
            return total_cleaned
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up alerts: {e}")
            return 0
    
    @classmethod
    def get_alert_statistics(cls):
        """Get alert statistics for dashboard"""
        try:
            now = datetime.utcnow()
            
            # Active alerts by severity
            active_alerts = cls.query.filter(
                cls.is_active == True,
                cls.dismissed_at.is_(None),
                or_(cls.auto_dismiss_at.is_(None), cls.auto_dismiss_at > now)
            ).all()
            
            stats = {
                'total_active': len(active_alerts),
                'by_severity': {
                    'critical': len([a for a in active_alerts if a.severity == 'critical']),
                    'error': len([a for a in active_alerts if a.severity == 'error']),
                    'warning': len([a for a in active_alerts if a.severity == 'warning']),
                    'info': len([a for a in active_alerts if a.severity == 'info'])
                },
                'by_type': {},
                'recent_count': len([a for a in active_alerts if a.get_age_minutes() < 60])
            }
            
            # Count by type
            for alert in active_alerts:
                alert_type = alert.alert_type
                if alert_type not in stats['by_type']:
                    stats['by_type'][alert_type] = 0
                stats['by_type'][alert_type] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {
                'total_active': 0,
                'by_severity': {'critical': 0, 'error': 0, 'warning': 0, 'info': 0},
                'by_type': {},
                'recent_count': 0
            }


class AlertGenerator:
    """Helper class for generating stevedoring operation alerts"""
    
    # Alert severity levels
    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_ERROR = 'error'
    SEVERITY_CRITICAL = 'critical'
    
    # Alert types
    TYPE_BERTH_CAPACITY = 'berth_capacity'
    TYPE_OPERATION_DELAY = 'operation_delay'
    TYPE_SAFETY_VIOLATION = 'safety_violation'
    TYPE_EQUIPMENT_FAILURE = 'equipment_failure'
    TYPE_PERFORMANCE = 'performance'
    TYPE_RESOURCE = 'resource'
    TYPE_SCHEDULE = 'schedule'
    
    @staticmethod
    def check_berth_capacity_alerts():
        """Check for berth capacity warnings (>80% utilization)"""
        try:
            from models.maritime.maritime_operation import MaritimeOperation
            
            # Get active operations with berth assignments
            active_ops = MaritimeOperation.query.filter(
                MaritimeOperation.berth_assigned.isnot(None),
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            # Calculate berth utilization (assuming 3 berths)
            berths_occupied = len(active_ops)
            utilization_percent = (berths_occupied / 3) * 100
            
            if utilization_percent >= 90:
                Alert.create_alert(
                    title="Critical Berth Capacity",
                    message=f"Berth utilization at {utilization_percent:.0f}% - Immediate action required",
                    severity=AlertGenerator.SEVERITY_CRITICAL,
                    icon="alert-triangle",
                    alert_type=AlertGenerator.TYPE_BERTH_CAPACITY,
                    alert_code="berth_capacity_critical",
                    metadata={'utilization_percent': utilization_percent, 'berths_occupied': berths_occupied},
                    auto_dismiss_hours=2
                )
            elif utilization_percent >= 80:
                Alert.create_alert(
                    title="High Berth Capacity",
                    message=f"Berth utilization at {utilization_percent:.0f}% - Monitor closely",
                    severity=AlertGenerator.SEVERITY_WARNING,
                    icon="alert-circle",
                    alert_type=AlertGenerator.TYPE_BERTH_CAPACITY,
                    alert_code="berth_capacity_warning",
                    metadata={'utilization_percent': utilization_percent, 'berths_occupied': berths_occupied},
                    auto_dismiss_hours=4
                )
            
        except Exception as e:
            logger.error(f"Error checking berth capacity alerts: {e}")
    
    @staticmethod
    def check_operation_delay_alerts():
        """Check for operation delays (past estimated completion)"""
        try:
            from models.maritime.maritime_operation import MaritimeOperation
            
            now = datetime.utcnow()
            
            # Get operations that should be completed by now
            delayed_ops = MaritimeOperation.query.filter(
                MaritimeOperation.eta < now,
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            for op in delayed_ops:
                if op.eta:
                    delay_hours = (now - op.eta).total_seconds() / 3600
                    
                    if delay_hours >= 4:
                        Alert.create_alert(
                            title="Critical Operation Delay",
                            message=f"Operation {op.vessel_name} delayed by {delay_hours:.1f} hours",
                            severity=AlertGenerator.SEVERITY_CRITICAL,
                            icon="clock",
                            operation_id=op.id,
                            vessel_id=op.vessel_id,
                            alert_type=AlertGenerator.TYPE_OPERATION_DELAY,
                            alert_code=f"delay_critical_{op.id}",
                            metadata={'delay_hours': delay_hours, 'original_eta': op.eta.isoformat()},
                            auto_dismiss_hours=6
                        )
                    elif delay_hours >= 2:
                        Alert.create_alert(
                            title="Operation Delay Warning",
                            message=f"Operation {op.vessel_name} delayed by {delay_hours:.1f} hours",
                            severity=AlertGenerator.SEVERITY_WARNING,
                            icon="clock",
                            operation_id=op.id,
                            vessel_id=op.vessel_id,
                            alert_type=AlertGenerator.TYPE_OPERATION_DELAY,
                            alert_code=f"delay_warning_{op.id}",
                            metadata={'delay_hours': delay_hours, 'original_eta': op.eta.isoformat()},
                            auto_dismiss_hours=8
                        )
            
        except Exception as e:
            logger.error(f"Error checking operation delay alerts: {e}")
    
    @staticmethod
    def check_safety_requirement_alerts():
        """Check for safety requirement violations"""
        try:
            from models.maritime.maritime_operation import MaritimeOperation
            
            # Get operations with safety requirements
            operations_with_safety = MaritimeOperation.query.filter(
                MaritimeOperation.safety_requirements.isnot(None),
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            for op in operations_with_safety:
                safety_reqs = op.safety_requirements or ""
                
                # Check for critical safety keywords
                critical_keywords = ['hazardous', 'dangerous', 'toxic', 'flammable', 'explosive']
                warning_keywords = ['special handling', 'caution', 'restricted', 'permit required']
                
                if any(keyword in safety_reqs.lower() for keyword in critical_keywords):
                    Alert.create_alert(
                        title="Critical Safety Requirements",
                        message=f"Operation {op.vessel_name} has critical safety requirements",
                        severity=AlertGenerator.SEVERITY_CRITICAL,
                        icon="shield-alert",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_SAFETY_VIOLATION,
                        alert_code=f"safety_critical_{op.id}",
                        metadata={'safety_requirements': safety_reqs},
                        auto_dismiss_hours=12
                    )
                elif any(keyword in safety_reqs.lower() for keyword in warning_keywords):
                    Alert.create_alert(
                        title="Safety Requirements Notice",
                        message=f"Operation {op.vessel_name} has special safety requirements",
                        severity=AlertGenerator.SEVERITY_WARNING,
                        icon="shield",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_SAFETY_VIOLATION,
                        alert_code=f"safety_warning_{op.id}",
                        metadata={'safety_requirements': safety_reqs},
                        auto_dismiss_hours=24
                    )
            
        except Exception as e:
            logger.error(f"Error checking safety requirement alerts: {e}")
    
    @staticmethod
    def check_equipment_availability_alerts():
        """Check for equipment availability issues"""
        try:
            from models.models.tico_vehicle import TicoVehicle
            
            # Get TICO vehicle availability
            total_vehicles = TicoVehicle.query.count()
            available_vehicles = TicoVehicle.query.filter_by(status='available').count()
            
            if total_vehicles > 0:
                availability_percent = (available_vehicles / total_vehicles) * 100
                
                if availability_percent < 20:
                    Alert.create_alert(
                        title="Critical Equipment Shortage",
                        message=f"Only {availability_percent:.0f}% of TICO vehicles available",
                        severity=AlertGenerator.SEVERITY_CRITICAL,
                        icon="truck",
                        alert_type=AlertGenerator.TYPE_EQUIPMENT_FAILURE,
                        alert_code="equipment_critical",
                        metadata={'availability_percent': availability_percent, 'available_count': available_vehicles},
                        auto_dismiss_hours=2
                    )
                elif availability_percent < 50:
                    Alert.create_alert(
                        title="Equipment Availability Warning",
                        message=f"Only {availability_percent:.0f}% of TICO vehicles available",
                        severity=AlertGenerator.SEVERITY_WARNING,
                        icon="truck",
                        alert_type=AlertGenerator.TYPE_EQUIPMENT_FAILURE,
                        alert_code="equipment_warning",
                        metadata={'availability_percent': availability_percent, 'available_count': available_vehicles},
                        auto_dismiss_hours=4
                    )
            
        except Exception as e:
            logger.error(f"Error checking equipment availability alerts: {e}")
    
    @staticmethod
    def check_team_performance_alerts():
        """Check for team performance issues"""
        try:
            from models.maritime.maritime_operation import MaritimeOperation
            
            # Get operations with low progress after significant time
            now = datetime.utcnow()
            threshold_time = now - timedelta(hours=4)
            
            low_progress_ops = MaritimeOperation.query.filter(
                MaritimeOperation.created_at < threshold_time,
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2']),
                MaritimeOperation.progress < 25
            ).all()
            
            for op in low_progress_ops:
                hours_elapsed = (now - op.created_at).total_seconds() / 3600
                
                Alert.create_alert(
                    title="Low Operation Progress",
                    message=f"Operation {op.vessel_name} showing low progress after {hours_elapsed:.1f} hours",
                    severity=AlertGenerator.SEVERITY_WARNING,
                    icon="trending-down",
                    operation_id=op.id,
                    vessel_id=op.vessel_id,
                    alert_type=AlertGenerator.TYPE_PERFORMANCE,
                    alert_code=f"low_progress_{op.id}",
                    metadata={'hours_elapsed': hours_elapsed, 'progress': op.progress},
                    auto_dismiss_hours=6
                )
            
        except Exception as e:
            logger.error(f"Error checking team performance alerts: {e}")
    
    @staticmethod
    def check_turnaround_time_alerts():
        """Check for turnaround time overruns"""
        try:
            from models.maritime.maritime_operation import MaritimeOperation
            
            # Get completed operations from last 24 hours
            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)
            
            completed_ops = MaritimeOperation.query.filter(
                MaritimeOperation.status == 'completed',
                MaritimeOperation.completed_at >= yesterday,
                MaritimeOperation.actual_duration.isnot(None)
            ).all()
            
            # Check for excessive turnaround times
            for op in completed_ops:
                if op.actual_duration > 24:  # Over 24 hours
                    Alert.create_alert(
                        title="Excessive Turnaround Time",
                        message=f"Operation {op.vessel_name} took {op.actual_duration:.1f} hours to complete",
                        severity=AlertGenerator.SEVERITY_WARNING,
                        icon="clock",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_PERFORMANCE,
                        alert_code=f"turnaround_long_{op.id}",
                        metadata={'actual_duration': op.actual_duration},
                        auto_dismiss_hours=48
                    )
                elif op.actual_duration > 36:  # Over 36 hours - critical
                    Alert.create_alert(
                        title="Critical Turnaround Time",
                        message=f"Operation {op.vessel_name} took {op.actual_duration:.1f} hours - exceeds critical threshold",
                        severity=AlertGenerator.SEVERITY_CRITICAL,
                        icon="clock",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_PERFORMANCE,
                        alert_code=f"turnaround_critical_{op.id}",
                        metadata={'actual_duration': op.actual_duration},
                        auto_dismiss_hours=72
                    )
            
        except Exception as e:
            logger.error(f"Error checking turnaround time alerts: {e}")
    
    @staticmethod
    def check_cargo_handling_delays():
        """Check for cargo handling delays"""
        try:
            from models.models.maritime_models import DischargeProgress
            from models.maritime.maritime_operation import MaritimeOperation
            
            # Get operations with recent progress updates
            now = datetime.utcnow()
            one_hour_ago = now - timedelta(hours=1)
            
            active_ops = MaritimeOperation.query.filter(
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            for op in active_ops:
                # Check if operation has recent progress updates
                latest_progress = DischargeProgress.query.filter_by(
                    vessel_id=op.vessel_id
                ).order_by(DischargeProgress.timestamp.desc()).first()
                
                if latest_progress and latest_progress.timestamp < one_hour_ago:
                    # No progress update in last hour
                    Alert.create_alert(
                        title="Cargo Handling Delay",
                        message=f"No progress update for {op.vessel_name} in last hour",
                        severity=AlertGenerator.SEVERITY_WARNING,
                        icon="package",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_PERFORMANCE,
                        alert_code=f"cargo_delay_{op.id}",
                        metadata={'last_update': latest_progress.timestamp.isoformat()},
                        auto_dismiss_hours=2
                    )
                
                # Check for low hourly rates
                if (latest_progress and latest_progress.hourly_rate and 
                    latest_progress.hourly_rate < (op.expected_rate or 150) * 0.7):
                    Alert.create_alert(
                        title="Low Cargo Handling Rate",
                        message=f"Operation {op.vessel_name} below expected rate: {latest_progress.hourly_rate}/hr",
                        severity=AlertGenerator.SEVERITY_WARNING,
                        icon="trending-down",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_PERFORMANCE,
                        alert_code=f"low_rate_{op.id}",
                        metadata={
                            'current_rate': float(latest_progress.hourly_rate),
                            'expected_rate': op.expected_rate or 150
                        },
                        auto_dismiss_hours=3
                    )
            
        except Exception as e:
            logger.error(f"Error checking cargo handling delays: {e}")
    
    @staticmethod
    def check_resource_allocation_alerts():
        """Check for resource allocation issues"""
        try:
            from models.maritime.stevedore_team import StevedoreTeam
            from models.maritime.maritime_operation import MaritimeOperation
            
            # Get active operations
            active_ops = MaritimeOperation.query.filter(
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            # Check for operations without assigned teams
            for op in active_ops:
                if not op.operation_manager:
                    Alert.create_alert(
                        title="Missing Operation Manager",
                        message=f"Operation {op.vessel_name} has no assigned operation manager",
                        severity=AlertGenerator.SEVERITY_ERROR,
                        icon="user-x",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_RESOURCE,
                        alert_code=f"no_manager_{op.id}",
                        metadata={},
                        auto_dismiss_hours=6
                    )
                
                # Check for inadequate team coverage
                team_members = []
                if op.auto_ops_lead:
                    team_members.append(op.auto_ops_lead)
                if op.heavy_ops_lead:
                    team_members.append(op.heavy_ops_lead)
                if op.auto_ops_assistant:
                    team_members.append(op.auto_ops_assistant)
                if op.heavy_ops_assistant:
                    team_members.append(op.heavy_ops_assistant)
                
                if len(team_members) < 2:
                    Alert.create_alert(
                        title="Insufficient Team Coverage",
                        message=f"Operation {op.vessel_name} has insufficient team members assigned",
                        severity=AlertGenerator.SEVERITY_WARNING,
                        icon="users",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_RESOURCE,
                        alert_code=f"insufficient_team_{op.id}",
                        metadata={'team_count': len(team_members)},
                        auto_dismiss_hours=4
                    )
            
        except Exception as e:
            logger.error(f"Error checking resource allocation alerts: {e}")
    
    @staticmethod
    def check_schedule_conflict_alerts():
        """Check for schedule conflicts"""
        try:
            from models.maritime.maritime_operation import MaritimeOperation
            
            # Get operations scheduled for same berth at overlapping times
            active_ops = MaritimeOperation.query.filter(
                MaritimeOperation.berth_assigned.isnot(None),
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            # Group by berth
            berth_ops = {}
            for op in active_ops:
                berth = op.berth_assigned
                if berth not in berth_ops:
                    berth_ops[berth] = []
                berth_ops[berth].append(op)
            
            # Check for conflicts
            for berth, ops in berth_ops.items():
                if len(ops) > 1:
                    vessel_names = [op.vessel_name for op in ops]
                    Alert.create_alert(
                        title="Berth Schedule Conflict",
                        message=f"Multiple operations assigned to berth {berth}: {', '.join(vessel_names)}",
                        severity=AlertGenerator.SEVERITY_ERROR,
                        icon="calendar-x",
                        alert_type=AlertGenerator.TYPE_SCHEDULE,
                        alert_code=f"berth_conflict_{berth}",
                        metadata={'berth': berth, 'vessels': vessel_names},
                        auto_dismiss_hours=12
                    )
            
        except Exception as e:
            logger.error(f"Error checking schedule conflict alerts: {e}")
    
    @staticmethod
    def check_weather_impact_alerts():
        """Check for weather-related operational impacts"""
        try:
            from models.maritime.maritime_operation import MaritimeOperation
            
            # This would integrate with weather API in production
            # For now, simulate weather impact checks
            active_ops = MaritimeOperation.query.filter(
                MaritimeOperation.status.in_(['initiated', 'in_progress', 'step_1', 'step_2', 'step_3', 'step_4'])
            ).all()
            
            # Simulate weather conditions (in production, this would be real data)
            weather_conditions = ['clear', 'rain', 'strong_wind', 'fog', 'storm']
            current_weather = random.choice(weather_conditions)
            
            if current_weather in ['strong_wind', 'storm']:
                for op in active_ops:
                    Alert.create_alert(
                        title="Weather Impact Warning",
                        message=f"Operation {op.vessel_name} may be affected by {current_weather} conditions",
                        severity=AlertGenerator.SEVERITY_WARNING,
                        icon="cloud-rain",
                        operation_id=op.id,
                        vessel_id=op.vessel_id,
                        alert_type=AlertGenerator.TYPE_SAFETY_VIOLATION,
                        alert_code=f"weather_{current_weather}_{op.id}",
                        metadata={'weather_condition': current_weather},
                        auto_dismiss_hours=6
                    )
            
        except Exception as e:
            logger.error(f"Error checking weather impact alerts: {e}")
    
    @staticmethod
    def check_equipment_maintenance_alerts():
        """Check for equipment maintenance requirements"""
        try:
            from models.models.tico_vehicle import TicoVehicle
            
            # Get vehicles that might need maintenance (in production, this would be based on usage hours)
            vehicles = TicoVehicle.query.filter_by(status='maintenance').all()
            
            if vehicles:
                Alert.create_alert(
                    title="Equipment Maintenance Required",
                    message=f"{len(vehicles)} TICO vehicles require maintenance",
                    severity=AlertGenerator.SEVERITY_WARNING,
                    icon="wrench",
                    alert_type=AlertGenerator.TYPE_EQUIPMENT_FAILURE,
                    alert_code="equipment_maintenance",
                    metadata={'vehicle_count': len(vehicles)},
                    auto_dismiss_hours=24
                )
            
            # Check for vehicles that have been in maintenance too long
            from datetime import datetime
            for vehicle in vehicles:
                # Simulate maintenance start time (in production, this would be tracked)
                maintenance_duration = random.randint(1, 72)  # hours
                if maintenance_duration > 48:
                    Alert.create_alert(
                        title="Extended Equipment Maintenance",
                        message=f"Vehicle {vehicle.vehicle_id} has been in maintenance for {maintenance_duration} hours",
                        severity=AlertGenerator.SEVERITY_ERROR,
                        icon="wrench",
                        alert_type=AlertGenerator.TYPE_EQUIPMENT_FAILURE,
                        alert_code=f"extended_maintenance_{vehicle.id}",
                        metadata={'vehicle_id': vehicle.vehicle_id, 'maintenance_hours': maintenance_duration},
                        auto_dismiss_hours=12
                    )
            
        except Exception as e:
            logger.error(f"Error checking equipment maintenance alerts: {e}")
    
    @staticmethod
    def run_all_checks():
        """Run all alert checks"""
        logger.info("Running all alert checks...")
        
        AlertGenerator.check_berth_capacity_alerts()
        AlertGenerator.check_operation_delay_alerts()
        AlertGenerator.check_safety_requirement_alerts()
        AlertGenerator.check_equipment_availability_alerts()
        AlertGenerator.check_team_performance_alerts()
        AlertGenerator.check_turnaround_time_alerts()
        AlertGenerator.check_cargo_handling_delays()
        AlertGenerator.check_resource_allocation_alerts()
        AlertGenerator.check_schedule_conflict_alerts()
        AlertGenerator.check_weather_impact_alerts()
        AlertGenerator.check_equipment_maintenance_alerts()
        
        logger.info("Alert checks completed")