"""Initial migration - Create all tables for Fleet Management System

Revision ID: 001
Revises: 
Create Date: 2023-12-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create vessels table
    op.create_table('vessels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('imo_number', sa.String(length=20), nullable=True),
        sa.Column('vessel_type', sa.String(length=50), nullable=False),
        sa.Column('flag', sa.String(length=50), nullable=True),
        sa.Column('owner', sa.String(length=100), nullable=True),
        sa.Column('operator', sa.String(length=100), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('beam', sa.Float(), nullable=True),
        sa.Column('draft', sa.Float(), nullable=True),
        sa.Column('gross_tonnage', sa.Integer(), nullable=True),
        sa.Column('net_tonnage', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('current_port', sa.String(length=100), nullable=True),
        sa.Column('destination_port', sa.String(length=100), nullable=True),
        sa.Column('eta', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vessels_imo_number'), 'vessels', ['imo_number'], unique=True)
    op.create_index(op.f('ix_vessels_name'), 'vessels', ['name'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('first_name', sa.String(length=50), nullable=True),
        sa.Column('last_name', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create tasks table
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('equipment', sa.String(length=100), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('completion_photos', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_synced', sa.Boolean(), nullable=False),
        sa.Column('local_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_assigned_to_id'), 'tasks', ['assigned_to_id'], unique=False)
    op.create_index(op.f('ix_tasks_created_at'), 'tasks', ['created_at'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_title'), 'tasks', ['title'], unique=False)
    op.create_index(op.f('ix_tasks_vessel_id'), 'tasks', ['vessel_id'], unique=False)

    # Create sync_logs table
    op.create_table('sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('table_name', sa.String(length=50), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=True),
        sa.Column('local_id', sa.String(length=36), nullable=True),
        sa.Column('sync_direction', sa.String(length=20), nullable=False),
        sa.Column('sync_status', sa.String(length=20), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('data_before', sa.JSON(), nullable=True),
        sa.Column('data_after', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('synced_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_logs_created_at'), 'sync_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_sync_logs_user_id'), 'sync_logs', ['user_id'], unique=False)

    # Set default values
    op.execute("UPDATE vessels SET status = 'active' WHERE status IS NULL")
    op.execute("UPDATE tasks SET priority = 'medium' WHERE priority IS NULL")
    op.execute("UPDATE tasks SET status = 'pending' WHERE status IS NULL")
    op.execute("UPDATE tasks SET is_synced = true WHERE is_synced IS NULL")
    op.execute("UPDATE sync_logs SET sync_status = 'pending' WHERE sync_status IS NULL")
    op.execute("UPDATE sync_logs SET retry_count = 0 WHERE retry_count IS NULL")


def downgrade():
    op.drop_index(op.f('ix_sync_logs_user_id'), table_name='sync_logs')
    op.drop_index(op.f('ix_sync_logs_created_at'), table_name='sync_logs')
    op.drop_table('sync_logs')
    
    op.drop_index(op.f('ix_tasks_vessel_id'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_title'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_status'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_created_at'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_assigned_to_id'), table_name='tasks')
    op.drop_table('tasks')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_vessels_name'), table_name='vessels')
    op.drop_index(op.f('ix_vessels_imo_number'), table_name='vessels')
    op.drop_table('vessels')