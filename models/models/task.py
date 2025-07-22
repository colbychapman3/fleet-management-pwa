"""
Enhanced Task model for stevedoring workflows, 4-step wizard, and maritime operations
"""

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import Index, text, DECIMAL
from app import db

class Task(db.Model):
    """Enhanced Task model for stevedoring operations and maritime workflows"""
    
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium', index=True)  
    # Priority: 'low', 'medium', 'high', 'urgent', 'safety_critical'
    
    status = db.Column(db.String(30), default='pending', index=True)
    # Status: 'pending', 'in_progress', 'paused', 'completed', 'cancelled', 'failed'
    
    # Enhanced task categorization for maritime operations
    task_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: 'vessel_setup', 'cargo_operation', 'equipment_maintenance', 'safety_inspection',
    #        'documentation', 'crew_assignment', 'berth_preparation', 'wizard_step'
    
    task_category = db.Column(db.String(50))
    # Categories: 'stevedoring', 'maintenance', 'safety', 'administration', 'logistics'
    
    # 4-Step Wizard Integration
    wizard_step = db.Column(db.Integer)  # 1, 2, 3, 4 for wizard steps
    wizard_sequence_id = db.Column(db.String(36))  # UUID to group wizard steps
    is_wizard_task = db.Column(db.Boolean, default=False)
    wizard_step_name = db.Column(db.String(100))  # Human-readable step name
    
    # Assignment and ownership
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vessel_id = db.Column(db.Integer, db.ForeignKey('vessels.id'), nullable=True, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('stevedore_teams.id'), nullable=True)
    operation_id = db.Column(db.Integer, db.ForeignKey('ship_operations.id'), nullable=True)
    
    # Scheduling and timing
    due_date = db.Column(db.DateTime, index=True)
    start_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    
    # Maritime-specific location and context
    location = db.Column(db.String(100))  # 'berth_1', 'deck_3', 'engine_room', 'brv_zone', etc.
    maritime_zone = db.Column(db.String(20))  # 'BRV', 'ZEE', 'SOU', 'PORT', 'ANCHORAGE'
    equipment_required = db.Column(db.JSON)  # List of required equipment
    safety_requirements = db.Column(db.JSON)  # Safety requirements and PPE
    
    # Prerequisites and dependencies
    prerequisite_tasks = db.Column(db.JSON)  # List of task IDs that must be completed first
    dependent_tasks = db.Column(db.JSON)  # List of task IDs that depend on this task
    blocks_operations = db.Column(db.Boolean, default=False)  # Critical path task
    
    # Progress tracking
    progress_percentage = db.Column(db.Integer, default=0)
    units_target = db.Column(db.Integer)  # For cargo operations (cars, containers, etc.)
    units_completed = db.Column(db.Integer, default=0)
    
    # Quality and compliance
    requires_inspection = db.Column(db.Boolean, default=False)
    inspection_status = db.Column(db.String(20))  # 'pending', 'passed', 'failed', 'not_required'
    quality_score = db.Column(db.Float)  # 1.0 - 5.0 rating
    compliance_notes = db.Column(db.Text)
    
    # Documentation and evidence
    completion_notes = db.Column(db.Text)
    completion_date = db.Column(db.DateTime)
    completion_photos = db.Column(db.JSON)  # Store photo URLs/paths
    documents_required = db.Column(db.JSON)  # Required documents
    documents_attached = db.Column(db.JSON)  # Attached document URLs
    
    # Safety and incidents
    safety_critical = db.Column(db.Boolean, default=False)
    hazards_identified = db.Column(db.JSON)  # List of safety hazards
    safety_measures = db.Column(db.JSON)  # Safety measures taken
    incident_reports = db.Column(db.JSON)  # Related incident report IDs
    
    # Cost tracking
    estimated_cost = db.Column(DECIMAL(10, 2))
    actual_cost = db.Column(DECIMAL(10, 2))
    cost_center = db.Column(db.String(50))
    
    # Communication and notifications
    notification_sent = db.Column(db.Boolean, default=False)
    escalation_level = db.Column(db.Integer, default=0)
    last_reminder_sent = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    paused_at = db.Column(db.DateTime)
    
    # Offline sync tracking
    is_synced = db.Column(db.Boolean, default=True, nullable=False)
    local_id = db.Column(db.String(36))  # UUID for offline creation
    sync_version = db.Column(db.Integer, default=1)
    
    # Relationships
    vessel = db.relationship('Vessel', backref='all_tasks', lazy=True, overlaps="tasks")
    team = db.relationship('StevedoreTeam', backref='tasks', lazy=True)
    operation = db.relationship('ShipOperation', backref='tasks', lazy=True)
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], back_populates='assigned_tasks', lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id], back_populates='created_tasks', lazy=True)
    
    def __repr__(self):
        return f'<Task {self.title} ({self.status})>'
    
    # Status and progress methods
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.status in ['completed', 'cancelled']:
            return False
        return datetime.utcnow() > self.due_date
    
    def is_critical_path(self):
        """Check if task is on critical path"""
        return self.blocks_operations or self.safety_critical
    
    def get_progress_percentage(self):
        """Calculate progress percentage"""
        if self.units_target and self.units_target > 0:
            return min(100, int((self.units_completed / self.units_target) * 100))
        return self.progress_percentage
    
    def update_progress(self, units_completed=None, percentage=None):
        """Update task progress"""
        if units_completed is not None:
            self.units_completed = min(units_completed, self.units_target or units_completed)
            if self.units_target:
                self.progress_percentage = self.get_progress_percentage()
        elif percentage is not None:
            self.progress_percentage = min(100, max(0, percentage))
        
        # Auto-complete if 100%
        if self.progress_percentage >= 100 and self.status != 'completed':
            self.mark_completed()
        
        db.session.commit()
    
    # Workflow state management
    def start_task(self, user_id=None):
        """Start the task"""
        if self.status == 'pending':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()
            if user_id and not self.assigned_to_id:
                self.assigned_to_id = user_id
            db.session.commit()
    
    def pause_task(self, reason=None):
        """Pause the task"""
        if self.status == 'in_progress':
            self.status = 'paused'
            self.paused_at = datetime.utcnow()
            if reason:
                self.completion_notes = f"Paused: {reason}\n{self.completion_notes or ''}"
            db.session.commit()
    
    def resume_task(self):
        """Resume paused task"""
        if self.status == 'paused':
            self.status = 'in_progress'
            self.paused_at = None
            db.session.commit()
    
    def mark_completed(self, completion_notes=None, actual_hours=None, 
                      completion_photos=None, quality_score=None):
        """Mark task as completed"""
        self.status = 'completed'
        self.completion_date = datetime.utcnow()
        self.progress_percentage = 100
        
        if completion_notes:
            self.completion_notes = completion_notes
        if actual_hours:
            self.actual_hours = actual_hours
        if completion_photos:
            self.completion_photos = completion_photos
        if quality_score:
            self.quality_score = quality_score
        
        # Auto-pass inspection if not safety critical
        if not self.safety_critical and self.inspection_status == 'pending':
            self.inspection_status = 'not_required'
        
        self.updated_at = datetime.utcnow()
        
        # Trigger dependent tasks
        self._check_dependent_tasks()
        
        db.session.commit()
    
    def mark_failed(self, failure_reason):
        """Mark task as failed"""
        self.status = 'failed'
        self.completion_date = datetime.utcnow()
        self.completion_notes = f"Failed: {failure_reason}"
        db.session.commit()
    
    def cancel_task(self, reason=None):
        """Cancel the task"""
        self.status = 'cancelled'
        if reason:
            self.completion_notes = f"Cancelled: {reason}"
        db.session.commit()
    
    # 4-Step Wizard methods
    def create_wizard_sequence(vessel_id, created_by_id):
        """Create a complete 4-step wizard sequence for vessel operations"""
        import uuid
        sequence_id = str(uuid.uuid4())
        
        wizard_steps = [
            {
                'step': 1,
                'name': 'Vessel Arrival & Documentation',
                'title': 'Process vessel arrival and verify documentation',
                'description': 'Verify manifest, customs clearance, and port documentation',
                'task_type': 'documentation',
                'estimated_hours': 2.0,
                'safety_requirements': ['TWIC_card', 'safety_briefing']
            },
            {
                'step': 2,
                'name': 'Berth Assignment & Setup',
                'title': 'Assign berth and prepare for operations',
                'description': 'Assign berth, position vessel, and set up equipment',
                'task_type': 'berth_preparation',
                'estimated_hours': 4.0,
                'equipment_required': ['tugs', 'mooring_equipment'],
                'safety_requirements': ['marine_traffic_clearance']
            },
            {
                'step': 3,
                'name': 'Team Assignment & Equipment Deployment',
                'title': 'Assign stevedore teams and deploy equipment',
                'description': 'Assign specialized teams and deploy required equipment',
                'task_type': 'crew_assignment',
                'estimated_hours': 1.0,
                'safety_requirements': ['equipment_inspection', 'team_briefing']
            },
            {
                'step': 4,
                'name': 'Begin Discharge Operations',
                'title': 'Commence cargo discharge operations',
                'description': 'Begin systematic cargo discharge according to plan',
                'task_type': 'cargo_operation',
                'estimated_hours': 12.0,
                'safety_requirements': ['continuous_monitoring', 'safety_officer_present']
            }
        ]
        
        created_tasks = []
        base_time = datetime.utcnow()
        
        for i, step_config in enumerate(wizard_steps):
            due_date = base_time + timedelta(hours=sum(s['estimated_hours'] for s in wizard_steps[:i+1]))
            
            task = Task(
                title=step_config['title'],
                description=step_config['description'],
                task_type=step_config['task_type'],
                task_category='stevedoring',
                priority='high',
                vessel_id=vessel_id,
                created_by_id=created_by_id,
                due_date=due_date,
                estimated_hours=step_config['estimated_hours'],
                wizard_step=step_config['step'],
                wizard_sequence_id=sequence_id,
                is_wizard_task=True,
                wizard_step_name=step_config['name'],
                equipment_required=step_config.get('equipment_required'),
                safety_requirements=step_config.get('safety_requirements'),
                blocks_operations=True  # Wizard steps are critical path
            )
            
            # Set prerequisites (each step depends on previous)
            if i > 0:
                task.prerequisite_tasks = [created_tasks[i-1].id]
            
            db.session.add(task)
            db.session.flush()  # Get ID without committing
            created_tasks.append(task)
        
        db.session.commit()
        return created_tasks
    
    def get_wizard_sequence(self):
        """Get all tasks in the same wizard sequence"""
        if not self.is_wizard_task or not self.wizard_sequence_id:
            return []
        
        return Task.query.filter_by(
            wizard_sequence_id=self.wizard_sequence_id
        ).order_by(Task.wizard_step.asc()).all()
    
    def get_next_wizard_step(self):
        """Get the next step in wizard sequence"""
        if not self.is_wizard_task:
            return None
        
        return Task.query.filter_by(
            wizard_sequence_id=self.wizard_sequence_id,
            wizard_step=self.wizard_step + 1
        ).first()
    
    def complete_wizard_step(self, **kwargs):
        """Complete wizard step and unlock next step"""
        self.mark_completed(**kwargs)
        
        next_step = self.get_next_wizard_step()
        if next_step and next_step.status == 'pending':
            # Auto-assign if current step was assigned
            if self.assigned_to_id:
                next_step.assigned_to_id = self.assigned_to_id
            next_step.status = 'pending'  # Make available
            db.session.commit()
        
        return next_step
    
    # Dependencies and prerequisites
    def _check_dependent_tasks(self):
        """Check and update dependent tasks when this task completes"""
        if not self.dependent_tasks:
            return
        
        for task_id in self.dependent_tasks:
            dependent_task = Task.query.get(task_id)
            if dependent_task and dependent_task._are_prerequisites_met():
                # Enable dependent task
                if dependent_task.status == 'pending':
                    dependent_task.status = 'pending'  # Ready to start
    
    def _are_prerequisites_met(self):
        """Check if all prerequisite tasks are completed"""
        if not self.prerequisite_tasks:
            return True
        
        for task_id in self.prerequisite_tasks:
            prereq_task = Task.query.get(task_id)
            if not prereq_task or prereq_task.status != 'completed':
                return False
        
        return True
    
    def can_start(self):
        """Check if task can be started"""
        return (self.status == 'pending' and 
                self._are_prerequisites_met() and
                self.is_resource_available())
    
    def is_resource_available(self):
        """Check if required resources are available"""
        # Check if assigned user is available
        if self.assigned_to_id:
            user = self.assigned_to
            if not user or user.availability_status != 'available':
                return False
        
        # Check equipment availability (simplified)
        if self.equipment_required:
            # In a real implementation, check equipment assignment table
            pass
        
        return True
    
    # Safety and compliance methods
    def conduct_safety_inspection(self, inspector_id, passed=True, notes=None):
        """Conduct safety inspection for task"""
        self.inspection_status = 'passed' if passed else 'failed'
        
        if notes:
            self.compliance_notes = notes
        
        if not passed:
            self.status = 'paused'
            self.completion_notes = f"Failed safety inspection: {notes}"
        
        db.session.commit()
    
    def add_safety_hazard(self, hazard_description, severity='medium'):
        """Add identified safety hazard"""
        if not self.hazards_identified:
            self.hazards_identified = []
        
        hazard = {
            'description': hazard_description,
            'severity': severity,
            'identified_at': datetime.utcnow().isoformat(),
            'status': 'open'
        }
        
        self.hazards_identified.append(hazard)
        
        if severity in ['high', 'critical']:
            self.safety_critical = True
            self.priority = 'urgent'
        
        db.session.commit()
    
    def resolve_safety_hazard(self, hazard_index, resolution_notes):
        """Resolve a safety hazard"""
        if self.hazards_identified and hazard_index < len(self.hazards_identified):
            self.hazards_identified[hazard_index]['status'] = 'resolved'
            self.hazards_identified[hazard_index]['resolved_at'] = datetime.utcnow().isoformat()
            self.hazards_identified[hazard_index]['resolution'] = resolution_notes
            db.session.commit()
    
    # Assignment and resource management
    def assign_to_user(self, user_id):
        """Assign task to a user"""
        self.assigned_to_id = user_id
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def assign_to_team(self, team_id):
        """Assign task to a team"""
        self.team_id = team_id
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def escalate_task(self, reason=None):
        """Escalate task due to delays or issues"""
        self.escalation_level += 1
        self.priority = 'urgent' if self.escalation_level > 1 else 'high'
        
        if reason:
            escalation_note = f"Escalated (Level {self.escalation_level}): {reason}"
            self.completion_notes = f"{escalation_note}\n{self.completion_notes or ''}"
        
        db.session.commit()
    
    # Cost and performance methods
    def calculate_cost_variance(self):
        """Calculate cost variance percentage"""
        if not self.estimated_cost or self.estimated_cost == 0:
            return 0.0
        
        actual = float(self.actual_cost or 0)
        estimated = float(self.estimated_cost)
        
        return round(((actual - estimated) / estimated) * 100, 2)
    
    def calculate_schedule_variance(self):
        """Calculate schedule variance in hours"""
        if not self.due_date:
            return 0.0
        
        if self.completion_date:
            variance = (self.completion_date - self.due_date).total_seconds() / 3600
        elif self.status not in ['completed', 'cancelled']:
            variance = (datetime.utcnow() - self.due_date).total_seconds() / 3600
        else:
            variance = 0.0
        
        return round(variance, 2)
    
    # Utility methods
    def get_status_display(self):
        """Get user-friendly status display"""
        status_map = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'paused': 'Paused',
            'completed': 'Completed',
            'cancelled': 'Cancelled',
            'failed': 'Failed'
        }
        return status_map.get(self.status, self.status.title())
    
    def get_priority_display(self):
        """Get user-friendly priority display"""
        priority_map = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High',
            'urgent': 'Urgent',
            'safety_critical': 'Safety Critical'
        }
        return priority_map.get(self.priority, self.priority.title())
    
    def get_type_display(self):
        """Get user-friendly task type display"""
        type_map = {
            'vessel_setup': 'Vessel Setup',
            'cargo_operation': 'Cargo Operation',
            'equipment_maintenance': 'Equipment Maintenance',
            'safety_inspection': 'Safety Inspection',
            'documentation': 'Documentation',
            'crew_assignment': 'Crew Assignment',
            'berth_preparation': 'Berth Preparation',
            'wizard_step': 'Wizard Step'
        }
        return type_map.get(self.task_type, self.task_type.replace('_', ' ').title())
    
    def to_dict(self, include_relationships=False):
        """Convert task to dictionary for API responses"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'task_type': self.task_type,
            'type_display': self.get_type_display(),
            'task_category': self.task_category,
            
            # Wizard integration
            'wizard_step': self.wizard_step,
            'wizard_sequence_id': self.wizard_sequence_id,
            'is_wizard_task': self.is_wizard_task,
            'wizard_step_name': self.wizard_step_name,
            
            # Assignment
            'assigned_to_id': self.assigned_to_id,
            'created_by_id': self.created_by_id,
            'vessel_id': self.vessel_id,
            'team_id': self.team_id,
            'operation_id': self.operation_id,
            
            # Scheduling
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            
            # Location and context
            'location': self.location,
            'maritime_zone': self.maritime_zone,
            'equipment_required': self.equipment_required,
            'safety_requirements': self.safety_requirements,
            
            # Dependencies
            'prerequisite_tasks': self.prerequisite_tasks,
            'dependent_tasks': self.dependent_tasks,
            'blocks_operations': self.blocks_operations,
            'can_start': self.can_start(),
            
            # Progress
            'progress_percentage': self.get_progress_percentage(),
            'units_target': self.units_target,
            'units_completed': self.units_completed,
            
            # Quality and compliance
            'requires_inspection': self.requires_inspection,
            'inspection_status': self.inspection_status,
            'quality_score': self.quality_score,
            'compliance_notes': self.compliance_notes,
            
            # Safety
            'safety_critical': self.safety_critical,
            'hazards_identified': self.hazards_identified,
            'safety_measures': self.safety_measures,
            
            # Cost
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'actual_cost': float(self.actual_cost) if self.actual_cost else None,
            'cost_variance': self.calculate_cost_variance(),
            'cost_center': self.cost_center,
            
            # Performance metrics
            'is_overdue': self.is_overdue(),
            'is_critical_path': self.is_critical_path(),
            'schedule_variance_hours': self.calculate_schedule_variance(),
            
            # Documentation
            'completion_notes': self.completion_notes,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'completion_photos': self.completion_photos,
            'documents_required': self.documents_required,
            'documents_attached': self.documents_attached,
            
            # Communication
            'notification_sent': self.notification_sent,
            'escalation_level': self.escalation_level,
            'last_reminder_sent': self.last_reminder_sent.isoformat() if self.last_reminder_sent else None,
            
            # Timestamps
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'paused_at': self.paused_at.isoformat() if self.paused_at else None,
            
            # Sync
            'is_synced': self.is_synced,
            'local_id': self.local_id,
            'sync_version': self.sync_version
        }
        
        if include_relationships:
            data.update({
                'assigned_to_name': self.assigned_to.get_full_name() if self.assigned_to else None,
                'assigned_to_role': self.assigned_to.get_display_role() if self.assigned_to else None,
                'created_by_name': self.created_by.get_full_name() if self.created_by else None,
                'vessel_name': self.vessel.name if self.vessel else None,
                'team_name': self.team.name if self.team else None,
                'operation_name': self.operation.operation_name if self.operation else None
            })
        
        return data
    
    # Static methods for queries
    @staticmethod
    def get_pending_tasks():
        """Get all pending tasks"""
        return Task.query.filter_by(status='pending').order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_overdue_tasks():
        """Get all overdue tasks"""
        return Task.query.filter(
            Task.status.in_(['pending', 'in_progress', 'paused']),
            Task.due_date < datetime.utcnow()
        ).order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_critical_path_tasks():
        """Get all critical path tasks"""
        return Task.query.filter(
            db.or_(Task.blocks_operations == True, Task.safety_critical == True),
            Task.status.in_(['pending', 'in_progress', 'paused'])
        ).order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_wizard_sequences_for_vessel(vessel_id):
        """Get all wizard sequences for a vessel"""
        sequences = db.session.query(Task.wizard_sequence_id).filter(
            Task.vessel_id == vessel_id,
            Task.is_wizard_task == True,
            Task.wizard_sequence_id.isnot(None)
        ).distinct().all()
        
        return [seq[0] for seq in sequences]
    
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
        return query.order_by(Task.wizard_step.asc(), Task.due_date.asc()).all()
    
    @staticmethod
    def get_tasks_for_team(team_id, status=None):
        """Get tasks assigned to a specific team"""
        query = Task.query.filter_by(team_id=team_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Task.due_date.asc()).all()
    
    @staticmethod
    def get_safety_critical_tasks():
        """Get all safety critical tasks"""
        return Task.query.filter_by(
            safety_critical=True
        ).filter(
            Task.status.in_(['pending', 'in_progress', 'paused'])
        ).order_by(Task.due_date.asc()).all()
    
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
        critical_tasks = len(Task.get_critical_path_tasks())
        safety_critical = len(Task.get_safety_critical_tasks())
        
        return {
            'total': total_tasks,
            'pending': pending_tasks,
            'in_progress': in_progress_tasks,
            'completed': completed_tasks,
            'overdue': overdue_tasks,
            'critical_path': critical_tasks,
            'safety_critical': safety_critical
        }

# Create indexes for performance
Index('idx_task_status_priority', Task.status, Task.priority)
Index('idx_task_vessel_status', Task.vessel_id, Task.status)
Index('idx_task_assigned_status', Task.assigned_to_id, Task.status)
Index('idx_task_wizard_sequence', Task.wizard_sequence_id, Task.wizard_step)
Index('idx_task_due_date_status', Task.due_date, Task.status)
Index('idx_task_type_category', Task.task_type, Task.task_category)
Index('idx_task_safety_critical', Task.safety_critical, Task.blocks_operations, Task.status)
