"""
Sync log model for tracking offline/online synchronization
"""

from datetime import datetime
from app import db

class SyncLog(db.Model):
    """Model for tracking data synchronization between offline and online states"""
    
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)  # create, update, delete
    table_name = db.Column(db.String(50), nullable=False)  # tasks, users, vessels
    record_id = db.Column(db.Integer, nullable=True)  # ID of affected record
    local_id = db.Column(db.String(36), nullable=True)  # UUID for offline-created records
    
    # Sync details
    sync_direction = db.Column(db.String(20), nullable=False)  # up (to server), down (from server)
    sync_status = db.Column(db.String(20), default='pending')  # pending, success, failed
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
    # Data payload
    data_before = db.Column(db.JSON)  # Previous state (for updates/deletes)
    data_after = db.Column(db.JSON)   # New state (for creates/updates)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    synced_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<SyncLog {self.action} {self.table_name}:{self.record_id}>'
    
    def mark_success(self):
        """Mark sync as successful"""
        self.sync_status = 'success'
        self.synced_at = datetime.utcnow()
        self.error_message = None
    
    def mark_failed(self, error_message):
        """Mark sync as failed with error message"""
        self.sync_status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
    
    def to_dict(self):
        """Convert sync log to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'local_id': self.local_id,
            'sync_direction': self.sync_direction,
            'sync_status': self.sync_status,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'data_before': self.data_before,
            'data_after': self.data_after,
            'created_at': self.created_at.isoformat(),
            'synced_at': self.synced_at.isoformat() if self.synced_at else None
        }
    
    @staticmethod
    def log_action(user_id, action, table_name, record_id=None, local_id=None, 
                   sync_direction='up', data_before=None, data_after=None):
        """Create a new sync log entry"""
        sync_log = SyncLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            local_id=local_id,
            sync_direction=sync_direction,
            data_before=data_before,
            data_after=data_after
        )
        db.session.add(sync_log)
        db.session.commit()
        return sync_log
    
    @staticmethod
    def get_pending_syncs(user_id=None):
        """Get all pending sync operations"""
        query = SyncLog.query.filter_by(sync_status='pending')
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(SyncLog.created_at.asc()).all()
    
    @staticmethod
    def get_failed_syncs(user_id=None):
        """Get all failed sync operations"""
        query = SyncLog.query.filter_by(sync_status='failed')
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(SyncLog.created_at.desc()).all()
    
    @staticmethod
    def get_sync_statistics(user_id=None):
        """Get synchronization statistics"""
        base_query = SyncLog.query
        if user_id:
            base_query = base_query.filter_by(user_id=user_id)
        
        total_syncs = base_query.count()
        pending_syncs = base_query.filter_by(sync_status='pending').count()
        successful_syncs = base_query.filter_by(sync_status='success').count()
        failed_syncs = base_query.filter_by(sync_status='failed').count()
        
        # Get latest sync time
        latest_sync = base_query.filter_by(sync_status='success').order_by(
            SyncLog.synced_at.desc()
        ).first()
        
        return {
            'total': total_syncs,
            'pending': pending_syncs,
            'successful': successful_syncs,
            'failed': failed_syncs,
            'last_sync': latest_sync.synced_at.isoformat() if latest_sync and latest_sync.synced_at else None
        }
    
    @staticmethod
    def cleanup_old_logs(days=30):
        """Clean up sync logs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_logs = SyncLog.query.filter(
            SyncLog.created_at < cutoff_date,
            SyncLog.sync_status == 'success'
        ).all()
        
        for log in old_logs:
            db.session.delete(log)
        
        db.session.commit()
        return len(old_logs)