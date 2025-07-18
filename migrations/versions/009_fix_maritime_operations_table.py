"""Fix maritime operations table and migration chain

Revision ID: 009
Revises: 008
Create Date: 2024-01-17 16:00:00.000000

This migration fixes the missing maritime_operations table that was referenced
in migrations 004-006 but never created, causing foreign key constraint failures.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Create the missing maritime_operations table
    op.create_table('maritime_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('operation_id', sa.String(50), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('priority', sa.String(20), server_default='normal', nullable=False),
        sa.Column('zone_assignment', sa.String(10), nullable=True),
        sa.Column('current_step', sa.Integer(), server_default='1', nullable=False),
        sa.Column('total_steps', sa.Integer(), server_default='4', nullable=False),
        sa.Column('step_1_data', sa.JSON(), nullable=True),
        sa.Column('step_2_data', sa.JSON(), nullable=True),
        sa.Column('step_3_data', sa.JSON(), nullable=True),
        sa.Column('step_4_data', sa.JSON(), nullable=True),
        sa.Column('completion_percentage', sa.Integer(), server_default='0', nullable=False),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('actual_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.current_timestamp()),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('assigned_supervisor_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_supervisor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('operation_id')
    )
    
    # Create indexes
    op.create_index('ix_maritime_operations_operation_id', 'maritime_operations', ['operation_id'])
    op.create_index('ix_maritime_operations_vessel_id', 'maritime_operations', ['vessel_id'])
    op.create_index('ix_maritime_operations_status', 'maritime_operations', ['status'])
    op.create_index('ix_maritime_operations_zone_assignment', 'maritime_operations', ['zone_assignment'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_maritime_operations_zone_assignment', 'maritime_operations')
    op.drop_index('ix_maritime_operations_status', 'maritime_operations')
    op.drop_index('ix_maritime_operations_vessel_id', 'maritime_operations')
    op.drop_index('ix_maritime_operations_operation_id', 'maritime_operations')
    
    # Drop table
    op.drop_table('maritime_operations')