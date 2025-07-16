"""Add TICO vehicle tables for stevedoring operations

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create tico_vehicles table
    op.create_table('tico_vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_type', sa.String(length=20), nullable=False),
        sa.Column('license_plate', sa.String(length=20), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('current_location', sa.String(length=100), nullable=True),
        sa.Column('zone_assignment', sa.String(length=10), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('current_load', sa.Integer(), nullable=False),
        sa.Column('last_maintenance', sa.DateTime(), nullable=True),
        sa.Column('next_maintenance', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_tico_vehicles_vessel_id', 'tico_vehicles', ['vessel_id'], unique=False)
    op.create_index('ix_tico_vehicles_vehicle_type', 'tico_vehicles', ['vehicle_type'], unique=False)
    op.create_index('ix_tico_vehicles_license_plate', 'tico_vehicles', ['license_plate'], unique=True)
    op.create_index('ix_tico_vehicles_status', 'tico_vehicles', ['status'], unique=False)
    op.create_index('ix_tico_vehicles_zone_assignment', 'tico_vehicles', ['zone_assignment'], unique=False)
    
    # Create tico_vehicle_assignments table
    op.create_table('tico_vehicle_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('zone', sa.String(length=10), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('passenger_count', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['tico_vehicles.id'], ),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_tico_vehicle_assignments_vehicle_id', 'tico_vehicle_assignments', ['vehicle_id'], unique=False)
    op.create_index('ix_tico_vehicle_assignments_zone', 'tico_vehicle_assignments', ['zone'], unique=False)
    
    # Create tico_vehicle_locations table
    op.create_table('tico_vehicle_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('coordinates', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['vehicle_id'], ['tico_vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_tico_vehicle_locations_vehicle_id', 'tico_vehicle_locations', ['vehicle_id'], unique=False)
    op.create_index('ix_tico_vehicle_locations_timestamp', 'tico_vehicle_locations', ['timestamp'], unique=False)
    
    # Add default values for existing columns
    op.execute("UPDATE tico_vehicles SET status = 'available' WHERE status IS NULL")
    op.execute("UPDATE tico_vehicles SET current_load = 0 WHERE current_load IS NULL")
    op.execute("UPDATE tico_vehicles SET created_at = datetime('now') WHERE created_at IS NULL")
    op.execute("UPDATE tico_vehicles SET updated_at = datetime('now') WHERE updated_at IS NULL")


def downgrade():
    # Drop tables in reverse order
    op.drop_table('tico_vehicle_locations')
    op.drop_table('tico_vehicle_assignments')
    op.drop_table('tico_vehicles')