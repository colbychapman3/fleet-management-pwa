"""
Task model for work management and tracking
"""

from datetime import datetime
from app import db

class Task(db.Model):
    """Task model for managing work assignments and tracking"""
    
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='pending', index=True)  # pending, in_progress, completed, cancelled
    task_type = db.Column(db.String(50), nullable=False)  # maintenance, inspection, cleaning, safety, cargo_loading, cargo_discharge, berth_assignment, pilot_services, customs_clearance, equipment_operation
    
    # Assignment
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True, index=True)
    
    # Scheduling
    due_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    
    # Location and equipment
    location = db.Column(db.String(100))  # deck, engine room, bridge, berth, zone, etc.
    equipment = db.Column(db.String(100))
    
    # Maritime-specific fields
    zone = db.Column(db.String(10))  # BRV, ZEE, SOU
    berth_number = db.Column(db.String(20))
    cargo_type = db.Column(db.String(50))  # automobiles, containers, bulk, general_cargo
    quantity = db.Column(db.Float)  # Quantity of cargo or units to handle
    unit_of_measure = db.Column(db.String(20))  # TEU, units, tons, etc.
    safety_requirements = db.Column(db.JSON)  # List of safety requirements
    required_equipment = db.Column(db.JSON)  # List of required equipment
    weather_dependent = db.Column(db.Boolean, default=False)
    tide_dependent = db.Column(db.Boolean, default=False)
    
    # Completion details
    completion_notes = db.Column(db.Text)
    completion_date = db.Column(db.DateTime)
    completion_photos = db.Column(db.JSON)  # Store photo URLs/paths
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Offline sync tracking
    is_synced = db.Column(db.Boolean, default=True, nullable=False)
    local_id = db.Column(db.String(36))  # UUID for offline creation
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.status in ['completed', 'cancelled']:
            return False
        return datetime.utcnow() > self.due_date
    
    def get_status_display(self):
        """Get user-friendly status display"""
        status_map = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled'
        }
        return status_map.get(self.status, self.status.title())
    
    def get_priority_display(self):
        """Get user-friendly priority display"""
        priority_map = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High',
            'urgent': 'Urgent'
        }
        return priority_map.get(self.priority, self.priority.title())
    
    def get_task_type_display(self):
        """Get user-friendly task type display"""
        type_map = {
            'maintenance': 'Maintenance',
            'inspection': 'Inspection',
            'cleaning': 'Cleaning',
            'safety': 'Safety Check',
            'cargo_loading': 'Cargo Loading',
            'cargo_discharge': 'Cargo Discharge',
            'berth_assignment': 'Berth Assignment',
            'pilot_services': 'Pilot Services',
            'customs_clearance': 'Customs Clearance',
            'equipment_operation': 'Equipment Operation'
        }
        return type_map.get(self.task_type, self.task_type.title())
    
    def is_maritime_task(self):
        """Check if this is a maritime-specific task"""
        maritime_types = [
            'cargo_loading', 'cargo_discharge', 'berth_assignment',
            'pilot_services', 'customs_clearance', 'equipment_operation'
        ]
        return self.task_type in maritime_types
    
    def requires_zone_access(self):
        """Check if task requires specific zone access"""
        return self.zone is not None
    
    def is_weather_sensitive(self):
        """Check if task is weather dependent"""
        return self.weather_dependent
    
    def is_tide_sensitive(self):
        """Check if task is tide dependent"""
        return self.tide_dependent
    
    def get_safety_requirements_list(self):
        """Get safety requirements as a list"""
        if not self.safety_requirements:
            return []
        return self.safety_requirements if isinstance(self.safety_requirements, list) else []
    
    def get_required_equipment_list(self):
        """Get required equipment as a list"""
        if not self.required_equipment:
            return []
        return self.required_equipment if isinstance(self.required_equipment, list) else []
    
    def mark_completed(self, completion_notes=None, actual_hours=None, completion_photos=None):
        """Mark task as completed"""
        self.status = 'completed'
        self.completion_date = datetime.utcnow()
        if completion_notes:
            self.completion_notes = completion_notes
        if actual_hours:
            self.actual_hours = actual_hours
        if completion_photos:
            self.completion_photos = completion_photos
        self.updated_at = datetime.utcnow()
    
    def assign_to_user(self, user_id):
        """Assign task to a user"""
        self.assigned_to_id = user_id
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert task to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'task_type': self.task_type,
            'task_type_display': self.get_task_type_display(),
            'assigned_to_id': self.assigned_to_id,
            'created_by_id': self.created_by_id,
            'vessel_id': self.vessel_id,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'location': self.location,
            'equipment': self.equipment,
            'completion_notes': self.completion_notes,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'completion_photos': self.completion_photos,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_overdue': self.is_overdue(),
            'is_synced': self.is_synced,
            'local_id': self.local_id,
            'zone': self.zone,
            'berth_number': self.berth_number,
            'cargo_type': self.cargo_type,
            'quantity': self.quantity,
            'unit_of_measure': self.unit_of_measure,
            'safety_requirements': self.safety_requirements,
            'required_equipment': self.required_equipment,
            'weather_dependent': self.weather_dependent,
            'tide_dependent': self.tide_dependent,
            'is_maritime_task': self.is_maritime_task(),
            'requires_zone_access': self.requires_zone_access(),
            'is_weather_sensitive': self.is_weather_sensitive(),
            'is_tide_sensitive': self.is_tide_sensitive(),
            'safety_requirements_list': self.get_safety_requirements_list(),
            'required_equipment_list': self.get_required_equipment_list(),
            # Include related data
            'assigned_to_name': self.assigned_to.get_full_name() if self.assigned_to else None,
            'created_by_name': self.created_by.get_full_name() if self.created_by else None,
            'vessel_name': self.vessel.name if self.vessel else None
        }
    
    @staticmethod
    def get_pending_tasks():
        """Get all pending tasks"""
        return Task.query.filter_by(status='pending').order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_overdue_tasks():
        """Get all overdue tasks"""
        return Task.query.filter(
            Task.status.in_(['pending', 'in_progress']),
            Task.due_date < datetime.utcnow()
        ).all()
    
    @staticmethod
    def get_tasks_for_user(user_id, status=None):
        """Get tasks assigned to a specific user"""
        query = Task.query.filter_by(assigned_to_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_tasks_for_vessel(vessel_id, status=None):
        """Get tasks for a specific vessel"""
        query = Task.query.filter_by(vessel_id=vessel_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_unsynced_tasks():
        """Get tasks that haven't been synced yet"""
        return Task.query.filter_by(is_synced=False).all()
    
    @staticmethod
    def get_task_statistics():
        """Get task statistics for dashboard"""
        total_tasks = Task.query.count()
        pending_tasks = Task.query.filter_by(status='pending').count()
        in_progress_tasks = Task.query.filter_by(status='in_progress').count()
        completed_tasks = Task.query.filter_by(status='completed').count()
        overdue_tasks = len(Task.get_overdue_tasks())
        
        return {
            'total': total_tasks,
            'pending': pending_tasks,
            'in_progress': in_progress_tasks,
            'completed': completed_tasks,
            'overdue': overdue_tasks
        }
    
    @staticmethod
    def get_maritime_tasks():
        """Get all maritime-specific tasks"""
        maritime_types = [
            'cargo_loading', 'cargo_discharge', 'berth_assignment',
            'pilot_services', 'customs_clearance', 'equipment_operation'
        ]
        return Task.query.filter(Task.task_type.in_(maritime_types)).all()
    
    @staticmethod
    def get_tasks_by_zone(zone):
        """Get tasks for a specific zone"""
        return Task.query.filter_by(zone=zone).order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_tasks_by_cargo_type(cargo_type):
        """Get tasks for a specific cargo type"""
        return Task.query.filter_by(cargo_type=cargo_type).order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_weather_dependent_tasks():
        """Get all weather-dependent tasks"""
        return Task.query.filter_by(weather_dependent=True).all()
    
    @staticmethod
    def get_tide_dependent_tasks():
        """Get all tide-dependent tasks"""
        return Task.query.filter_by(tide_dependent=True).all()
    
    @staticmethod
    def get_tasks_by_berth(berth_number):
        """Get tasks for a specific berth"""
        return Task.query.filter_by(berth_number=berth_number).order_by(Task.due_date.asc()).all()