"""enhance maritime operations with stevedoring fields

Revision ID: 004
Revises: 003
Create Date: 2024-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_enhance_maritime_operations'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add comprehensive stevedoring fields to maritime_operations table"""
    # Add vessel and operation details
    op.add_column('maritime_operations', sa.Column('vessel_name', sa.String(200), nullable=True))
    op.add_column('maritime_operations', sa.Column('vessel_type', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('shipping_line', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('port', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('operation_date', sa.Date(), nullable=True))
    op.add_column('maritime_operations', sa.Column('company', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('berth', sa.String(50), nullable=True))
    
    # Add team assignments
    op.add_column('maritime_operations', sa.Column('operation_manager', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('auto_ops_lead', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('auto_ops_assistant', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('heavy_ops_lead', sa.String(100), nullable=True))
    op.add_column('maritime_operations', sa.Column('heavy_ops_assistant', sa.String(100), nullable=True))
    
    # Add cargo and vehicle breakdown
    op.add_column('maritime_operations', sa.Column('total_vehicles', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('total_automobiles_discharge', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('heavy_equipment_discharge', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('total_electric_vehicles', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('total_static_cargo', sa.Integer(), nullable=True, default=0))
    
    # Add terminal targets and planning
    op.add_column('maritime_operations', sa.Column('brv_target', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('zee_target', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('sou_target', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('expected_rate', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('total_drivers', sa.Integer(), nullable=True, default=0))
    
    # Add shift and timing
    op.add_column('maritime_operations', sa.Column('shift_start', sa.String(20), nullable=True))
    op.add_column('maritime_operations', sa.Column('shift_end', sa.String(20), nullable=True))
    op.add_column('maritime_operations', sa.Column('break_duration', sa.Integer(), nullable=True, default=30))
    op.add_column('maritime_operations', sa.Column('target_completion', sa.String(20), nullable=True))
    op.add_column('maritime_operations', sa.Column('start_time', sa.String(20), nullable=True))
    op.add_column('maritime_operations', sa.Column('estimated_completion', sa.String(20), nullable=True))
    
    # Add equipment allocation
    op.add_column('maritime_operations', sa.Column('tico_vans', sa.Integer(), nullable=True, default=0))
    op.add_column('maritime_operations', sa.Column('tico_station_wagons', sa.Integer(), nullable=True, default=0))
    
    # Add progress tracking
    op.add_column('maritime_operations', sa.Column('progress', sa.Integer(), nullable=True, default=0))
    
    # Add JSON fields for complex data
    op.add_column('maritime_operations', sa.Column('deck_data', sa.Text(), nullable=True))
    op.add_column('maritime_operations', sa.Column('turnaround_data', sa.Text(), nullable=True))
    op.add_column('maritime_operations', sa.Column('inventory_data', sa.Text(), nullable=True))
    op.add_column('maritime_operations', sa.Column('hourly_quantity_data', sa.Text(), nullable=True))
    
    # Add advanced maritime fields
    op.add_column('maritime_operations', sa.Column('imo_number', sa.String(20), nullable=True))
    op.add_column('maritime_operations', sa.Column('mmsi', sa.String(15), nullable=True))
    op.add_column('maritime_operations', sa.Column('call_sign', sa.String(20), nullable=True))
    op.add_column('maritime_operations', sa.Column('flag_state', sa.String(50), nullable=True))
    
    # Create indexes for performance
    op.create_index('idx_maritime_operations_vessel_name', 'maritime_operations', ['vessel_name'])
    op.create_index('idx_maritime_operations_shipping_line', 'maritime_operations', ['shipping_line'])
    op.create_index('idx_maritime_operations_operation_date', 'maritime_operations', ['operation_date'])
    op.create_index('idx_maritime_operations_status', 'maritime_operations', ['status'])
    op.create_index('idx_maritime_operations_berth', 'maritime_operations', ['berth'])


def downgrade():
    """Remove stevedoring fields from maritime_operations table"""
    # Drop indexes first
    op.drop_index('idx_maritime_operations_berth', table_name='maritime_operations')
    op.drop_index('idx_maritime_operations_status', table_name='maritime_operations')
    op.drop_index('idx_maritime_operations_operation_date', table_name='maritime_operations')
    op.drop_index('idx_maritime_operations_shipping_line', table_name='maritime_operations')
    op.drop_index('idx_maritime_operations_vessel_name', table_name='maritime_operations')
    
    # Remove advanced maritime fields
    op.drop_column('maritime_operations', 'flag_state')
    op.drop_column('maritime_operations', 'call_sign')
    op.drop_column('maritime_operations', 'mmsi')
    op.drop_column('maritime_operations', 'imo_number')
    
    # Remove JSON fields
    op.drop_column('maritime_operations', 'hourly_quantity_data')
    op.drop_column('maritime_operations', 'inventory_data')
    op.drop_column('maritime_operations', 'turnaround_data')
    op.drop_column('maritime_operations', 'deck_data')
    
    # Remove progress tracking
    op.drop_column('maritime_operations', 'progress')
    
    # Remove equipment allocation
    op.drop_column('maritime_operations', 'tico_station_wagons')
    op.drop_column('maritime_operations', 'tico_vans')
    
    # Remove shift and timing
    op.drop_column('maritime_operations', 'estimated_completion')
    op.drop_column('maritime_operations', 'start_time')
    op.drop_column('maritime_operations', 'target_completion')
    op.drop_column('maritime_operations', 'break_duration')
    op.drop_column('maritime_operations', 'shift_end')
    op.drop_column('maritime_operations', 'shift_start')
    
    # Remove terminal targets
    op.drop_column('maritime_operations', 'total_drivers')
    op.drop_column('maritime_operations', 'expected_rate')
    op.drop_column('maritime_operations', 'sou_target')
    op.drop_column('maritime_operations', 'zee_target')
    op.drop_column('maritime_operations', 'brv_target')
    
    # Remove cargo breakdown
    op.drop_column('maritime_operations', 'total_static_cargo')
    op.drop_column('maritime_operations', 'total_electric_vehicles')
    op.drop_column('maritime_operations', 'heavy_equipment_discharge')
    op.drop_column('maritime_operations', 'total_automobiles_discharge')
    op.drop_column('maritime_operations', 'total_vehicles')
    
    # Remove team assignments
    op.drop_column('maritime_operations', 'heavy_ops_assistant')
    op.drop_column('maritime_operations', 'heavy_ops_lead')
    op.drop_column('maritime_operations', 'auto_ops_assistant')
    op.drop_column('maritime_operations', 'auto_ops_lead')
    op.drop_column('maritime_operations', 'operation_manager')
    
    # Remove vessel and operation details
    op.drop_column('maritime_operations', 'berth')
    op.drop_column('maritime_operations', 'company')
    op.drop_column('maritime_operations', 'operation_date')
    op.drop_column('maritime_operations', 'port')
    op.drop_column('maritime_operations', 'shipping_line')
    op.drop_column('maritime_operations', 'vessel_type')
    op.drop_column('maritime_operations', 'vessel_name')