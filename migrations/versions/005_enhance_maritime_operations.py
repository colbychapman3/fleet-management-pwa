"""enhance maritime operations

Revision ID: 005_enhance_maritime_operations
Revises: 004_enhance_maritime_operations
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '005_enhance_maritime_operations'
down_revision = '004_enhance_maritime_operations'
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to maritime_operations table
    op.add_column('maritime_operations', sa.Column('cargo_type', sa.String(length=100), nullable=True))
    op.add_column('maritime_operations', sa.Column('cargo_weight', sa.Float(), nullable=True))
    op.add_column('maritime_operations', sa.Column('cargo_description', sa.Text(), nullable=True))
    op.add_column('maritime_operations', sa.Column('cargo_origin', sa.String(length=100), nullable=True))
    op.add_column('maritime_operations', sa.Column('cargo_destination', sa.String(length=100), nullable=True))
    op.add_column('maritime_operations', sa.Column('stowage_location', sa.String(length=100), nullable=True))
    op.add_column('maritime_operations', sa.Column('stowage_notes', sa.Text(), nullable=True))
    op.add_column('maritime_operations', sa.Column('safety_requirements', sa.Text(), nullable=True))
    op.add_column('maritime_operations', sa.Column('loading_sequence', sa.Integer(), nullable=True))
    op.add_column('maritime_operations', sa.Column('special_instructions', sa.Text(), nullable=True))
    op.add_column('maritime_operations', sa.Column('priority_level', sa.String(length=20), nullable=True))
    op.add_column('maritime_operations', sa.Column('assigned_crew', sa.String(length=200), nullable=True))
    op.add_column('maritime_operations', sa.Column('eta', sa.DateTime(), nullable=True))


def downgrade():
    # Remove added fields
    op.drop_column('maritime_operations', 'eta')
    op.drop_column('maritime_operations', 'assigned_crew')
    op.drop_column('maritime_operations', 'priority_level')
    op.drop_column('maritime_operations', 'special_instructions')
    op.drop_column('maritime_operations', 'loading_sequence')
    op.drop_column('maritime_operations', 'safety_requirements')
    op.drop_column('maritime_operations', 'stowage_notes')
    op.drop_column('maritime_operations', 'stowage_location')
    op.drop_column('maritime_operations', 'cargo_destination')
    op.drop_column('maritime_operations', 'cargo_origin')
    op.drop_column('maritime_operations', 'cargo_description')
    op.drop_column('maritime_operations', 'cargo_weight')
    op.drop_column('maritime_operations', 'cargo_type')