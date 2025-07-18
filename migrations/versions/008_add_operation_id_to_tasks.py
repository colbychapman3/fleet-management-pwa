"""Add operation_id to tasks table

Revision ID: 008
Revises: 007
Create Date: 2024-01-17 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Add operation_id column to tasks table
    op.add_column('tasks', sa.Column('operation_id', sa.Integer(), nullable=True))
    op.create_index('ix_tasks_operation_id', 'tasks', ['operation_id'])
    
    # Add team_id column to tasks table
    op.add_column('tasks', sa.Column('team_id', sa.Integer(), nullable=True))
    op.create_index('ix_tasks_team_id', 'tasks', ['team_id'])
    
    # Add foreign key constraints
    op.create_foreign_key('fk_tasks_operation_id', 'tasks', 'ship_operations', ['operation_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_tasks_team_id', 'tasks', 'stevedore_teams', ['team_id'], ['id'], ondelete='SET NULL')


def downgrade():
    # Remove foreign key constraints
    op.drop_constraint('fk_tasks_team_id', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_operation_id', 'tasks', type_='foreignkey')
    
    # Remove indexes and columns
    op.drop_index('ix_tasks_team_id', 'tasks')
    op.drop_column('tasks', 'team_id')
    op.drop_index('ix_tasks_operation_id', 'tasks')
    op.drop_column('tasks', 'operation_id')