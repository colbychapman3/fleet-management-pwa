"""Remove duplicate index on stevedore_teams.status column

Revision ID: 009
Revises: 008
Create Date: 2024-07-21 10:00:00.000000

This migration removes the duplicate index idx_stevedore_teams_status.
Flask-SQLAlchemy automatically creates ix_stevedore_teams_status from the 
model definition (status = db.Column(..., index=True)), making the custom
idx_stevedore_teams_status redundant and causing performance issues.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove the duplicate custom index idx_stevedore_teams_status.
    Keep the Flask-SQLAlchemy auto-generated ix_stevedore_teams_status.
    """
    # Drop the custom duplicate index
    op.drop_index('idx_stevedore_teams_status', table_name='stevedore_teams')


def downgrade():
    """
    Recreate the custom index (though this would recreate the duplicate issue).
    """
    # Recreate the custom index for rollback purposes
    op.create_index('idx_stevedore_teams_status', 'stevedore_teams', ['status'])
