"""Add alert system for stevedoring operations

Revision ID: 006_add_alert_system
Revises: 005_enhance_maritime_operations
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '006_add_alert_system'
down_revision = '005_enhance_maritime_operations'
branch_labels = None
depends_on = None

def upgrade():
    """Add alert system table"""
    
    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, default='info'),
        sa.Column('icon', sa.String(50), default='alert-circle'),
        sa.Column('operation_id', sa.Integer(), nullable=True),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('alert_code', sa.String(20), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_by', sa.Integer(), nullable=True),
        sa.Column('auto_dismiss_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_alert_type', 'alerts', ['alert_type'])
    op.create_index('ix_alerts_alert_code', 'alerts', ['alert_code'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])
    op.create_index('ix_alerts_dismissed_at', 'alerts', ['dismissed_at'])
    op.create_index('ix_alerts_auto_dismiss_at', 'alerts', ['auto_dismiss_at'])
    op.create_index('ix_alerts_is_active', 'alerts', ['is_active'])
    op.create_index('ix_alerts_operation_id', 'alerts', ['operation_id'])
    op.create_index('ix_alerts_vessel_id', 'alerts', ['vessel_id'])
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])
    
    # Create foreign key constraints
    op.create_foreign_key(
        'fk_alerts_operation_id', 'alerts', 'maritime_operations',
        ['operation_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_alerts_vessel_id', 'alerts', 'vessels',
        ['vessel_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_alerts_user_id', 'alerts', 'users',
        ['user_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_alerts_dismissed_by', 'alerts', 'users',
        ['dismissed_by'], ['id'], ondelete='SET NULL'
    )
    
    # Add check constraint for severity values
    op.create_check_constraint(
        'ck_alerts_severity',
        'alerts',
        "severity IN ('info', 'warning', 'error', 'critical')"
    )
    
    # Add check constraint for alert_type values
    op.create_check_constraint(
        'ck_alerts_alert_type',
        'alerts',
        "alert_type IN ('berth_capacity', 'operation_delay', 'safety_violation', 'equipment_failure', 'performance', 'resource', 'schedule', 'general')"
    )
    
    print("✅ Alert system table created successfully")

def downgrade():
    """Remove alert system table"""
    
    # Drop foreign key constraints
    op.drop_constraint('fk_alerts_dismissed_by', 'alerts', type_='foreignkey')
    op.drop_constraint('fk_alerts_user_id', 'alerts', type_='foreignkey')
    op.drop_constraint('fk_alerts_vessel_id', 'alerts', type_='foreignkey')
    op.drop_constraint('fk_alerts_operation_id', 'alerts', type_='foreignkey')
    
    # Drop check constraints
    op.drop_constraint('ck_alerts_alert_type', 'alerts', type_='check')
    op.drop_constraint('ck_alerts_severity', 'alerts', type_='check')
    
    # Drop indexes
    op.drop_index('ix_alerts_user_id', 'alerts')
    op.drop_index('ix_alerts_vessel_id', 'alerts')
    op.drop_index('ix_alerts_operation_id', 'alerts')
    op.drop_index('ix_alerts_is_active', 'alerts')
    op.drop_index('ix_alerts_auto_dismiss_at', 'alerts')
    op.drop_index('ix_alerts_dismissed_at', 'alerts')
    op.drop_index('ix_alerts_created_at', 'alerts')
    op.drop_index('ix_alerts_alert_code', 'alerts')
    op.drop_index('ix_alerts_alert_type', 'alerts')
    op.drop_index('ix_alerts_severity', 'alerts')
    
    # Drop table
    op.drop_table('alerts')
    
    print("✅ Alert system table removed successfully")