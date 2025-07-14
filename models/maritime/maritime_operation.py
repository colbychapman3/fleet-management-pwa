from app import db
from datetime import datetime

class MaritimeOperation(db.Model):
    __tablename__ = 'maritime_operations'

    id = db.Column(db.Integer, primary_key=True)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=False)
    operation_type = db.Column(db.String(100), nullable=False) # e.g., 'loading', 'discharging'
    status = db.Column(db.String(50), default='pending') # e.g., 'pending', 'in_progress', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MaritimeOperation {self.id}>'
