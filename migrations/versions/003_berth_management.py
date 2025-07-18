"""Add berth management and port infrastructure

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 11:00:00.000000

This migration adds comprehensive berth management, port infrastructure,
and advanced scheduling capabilities for maritime operations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add berth management and port infrastructure tables
    """
    
    # ============================================================================
    # CREATE BERTH MANAGEMENT TABLES
    # ============================================================================
    
    # Berths table for port infrastructure
    op.create_table('berths',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('berth_number', sa.String(20), nullable=False),
        sa.Column('berth_name', sa.String(100), nullable=True),
        sa.Column('berth_type', sa.String(50), nullable=True),  # Container, RoRo, General Cargo
        sa.Column('length_meters', sa.Float(), nullable=True),
        sa.Column('depth_meters', sa.Float(), nullable=True),
        sa.Column('max_draft', sa.Float(), nullable=True),
        sa.Column('max_loa', sa.Float(), nullable=True),  # Length Overall
        sa.Column('bollards_count', sa.Integer(), nullable=True),
        sa.Column('crane_capacity', sa.Integer(), nullable=True),  # In tons
        sa.Column('electrical_capacity', sa.Integer(), nullable=True),  # In kW
        sa.Column('water_supply', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('fuel_supply', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),  # active, maintenance, closed
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('daily_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('facilities', sa.Text(), nullable=True),  # JSON of available facilities
        sa.Column('restrictions', sa.Text(), nullable=True),  # JSON of restrictions/limitations
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('berth_number')
    )
    op.create_index('ix_berths_berth_number', 'berths', ['berth_number'])
    op.create_index('ix_berths_berth_type', 'berths', ['berth_type'])
    op.create_index('ix_berths_status', 'berths', ['status'])
    
    # Berth reservations for scheduling
    op.create_table('berth_reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('berth_id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('reservation_start', sa.DateTime(), nullable=False),
        sa.Column('reservation_end', sa.DateTime(), nullable=False),
        sa.Column('actual_arrival', sa.DateTime(), nullable=True),
        sa.Column('actual_departure', sa.DateTime(), nullable=True),
        sa.Column('reservation_type', sa.String(20), server_default='confirmed', nullable=False),  # tentative, confirmed, completed, cancelled
        sa.Column('purpose', sa.String(100), nullable=True),  # Loading, Discharge, Bunkering, etc.
        sa.Column('priority', sa.String(20), server_default='normal', nullable=False),  # low, normal, high, urgent
        sa.Column('estimated_duration', sa.Integer(), nullable=True),  # Hours
        sa.Column('actual_duration', sa.Integer(), nullable=True),  # Hours
        sa.Column('total_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_berth_reservations_berth_id', 'berth_reservations', ['berth_id'])
    op.create_index('ix_berth_reservations_vessel_id', 'berth_reservations', ['vessel_id'])
    op.create_index('ix_berth_reservations_reservation_start', 'berth_reservations', ['reservation_start'])
    op.create_index('ix_berth_reservations_reservation_type', 'berth_reservations', ['reservation_type'])
    op.create_index('ix_berth_reservations_priority', 'berth_reservations', ['priority'])
    
    # ============================================================================
    # CREATE SHIP OPERATIONS TRACKING
    # ============================================================================
    
    # Ship operations for detailed operation tracking
    op.create_table('ship_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('berth_id', sa.Integer(), nullable=True),
        sa.Column('operation_type', sa.String(50), nullable=False),  # Discharge, Loading, Bunkering, Maintenance
        sa.Column('operation_status', sa.String(20), server_default='planned', nullable=False),  # planned, in_progress, completed, suspended, cancelled
        sa.Column('planned_start', sa.DateTime(), nullable=True),
        sa.Column('actual_start', sa.DateTime(), nullable=True),
        sa.Column('planned_end', sa.DateTime(), nullable=True),
        sa.Column('actual_end', sa.DateTime(), nullable=True),
        sa.Column('operation_manager_id', sa.Integer(), nullable=True),
        sa.Column('supervisor_id', sa.Integer(), nullable=True),
        sa.Column('crew_size', sa.Integer(), nullable=True),
        sa.Column('equipment_used', sa.Text(), nullable=True),  # JSON array of equipment
        sa.Column('weather_conditions', sa.String(100), nullable=True),
        sa.Column('tide_level', sa.String(50), nullable=True),
        sa.Column('safety_incidents', sa.Text(), nullable=True),  # JSON array of incidents
        sa.Column('delays', sa.Text(), nullable=True),  # JSON array of delay reasons
        sa.Column('efficiency_rating', sa.Numeric(3, 2), nullable=True),  # 0.00 to 5.00
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['operation_manager_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supervisor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ship_operations_vessel_id', 'ship_operations', ['vessel_id'])
    op.create_index('ix_ship_operations_berth_id', 'ship_operations', ['berth_id'])
    op.create_index('ix_ship_operations_operation_type', 'ship_operations', ['operation_type'])
    op.create_index('ix_ship_operations_operation_status', 'ship_operations', ['operation_status'])
    op.create_index('ix_ship_operations_planned_start', 'ship_operations', ['planned_start'])
    
    # ============================================================================
    # CREATE EQUIPMENT MANAGEMENT
    # ============================================================================
    
    # Equipment tracking for port operations
    op.create_table('port_equipment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_code', sa.String(50), nullable=False),
        sa.Column('equipment_name', sa.String(100), nullable=False),
        sa.Column('equipment_type', sa.String(50), nullable=False),  # Crane, Forklift, Reach Stacker, etc.
        sa.Column('manufacturer', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('year_manufactured', sa.Integer(), nullable=True),
        sa.Column('capacity_tons', sa.Numeric(8, 2), nullable=True),
        sa.Column('operating_hours', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(20), server_default='available', nullable=False),  # available, in_use, maintenance, out_of_service
        sa.Column('current_location', sa.String(100), nullable=True),
        sa.Column('assigned_operator_id', sa.Integer(), nullable=True),
        sa.Column('last_maintenance', sa.Date(), nullable=True),
        sa.Column('next_maintenance', sa.Date(), nullable=True),
        sa.Column('maintenance_interval_hours', sa.Integer(), server_default='1000', nullable=False),
        sa.Column('fuel_consumption_rate', sa.Numeric(8, 2), nullable=True),  # Liters per hour
        sa.Column('operating_cost_per_hour', sa.Numeric(8, 2), nullable=True),
        sa.Column('specifications', sa.Text(), nullable=True),  # JSON of technical specifications
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['assigned_operator_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('equipment_code')
    )
    op.create_index('ix_port_equipment_equipment_code', 'port_equipment', ['equipment_code'])
    op.create_index('ix_port_equipment_equipment_type', 'port_equipment', ['equipment_type'])
    op.create_index('ix_port_equipment_status', 'port_equipment', ['status'])
    op.create_index('ix_port_equipment_assigned_operator_id', 'port_equipment', ['assigned_operator_id'])
    
    # Equipment usage tracking
    op.create_table('equipment_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('operation_id', sa.Integer(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('start_hour_meter', sa.Integer(), nullable=True),
        sa.Column('end_hour_meter', sa.Integer(), nullable=True),
        sa.Column('fuel_consumed', sa.Numeric(8, 2), nullable=True),
        sa.Column('cargo_handled_tons', sa.Numeric(10, 2), nullable=True),
        sa.Column('cycles_completed', sa.Integer(), nullable=True),
        sa.Column('efficiency_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('issues_reported', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['equipment_id'], ['port_equipment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['operation_id'], ['ship_operations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_equipment_usage_equipment_id', 'equipment_usage', ['equipment_id'])
    op.create_index('ix_equipment_usage_vessel_id', 'equipment_usage', ['vessel_id'])
    op.create_index('ix_equipment_usage_operator_id', 'equipment_usage', ['operator_id'])
    op.create_index('ix_equipment_usage_start_time', 'equipment_usage', ['start_time'])
    
    # ============================================================================
    # ENHANCE VESSELS TABLE WITH BERTH REFERENCES
    # ============================================================================
    
    # Update vessels table to reference berths
    op.add_column('vessels', sa.Column('current_berth_id', sa.Integer(), nullable=True))
    op.add_column('vessels', sa.Column('berth_arrival_time', sa.DateTime(), nullable=True))
    op.add_column('vessels', sa.Column('berth_departure_time', sa.DateTime(), nullable=True))
    op.add_column('vessels', sa.Column('pilot_required', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('vessels', sa.Column('tug_assistance', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('vessels', sa.Column('customs_clearance', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('vessels', sa.Column('immigration_clearance', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('vessels', sa.Column('health_clearance', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('vessels', sa.Column('security_clearance', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('vessels', sa.Column('agent_company', sa.String(100), nullable=True))
    op.add_column('vessels', sa.Column('agent_contact', sa.String(100), nullable=True))
    op.add_column('vessels', sa.Column('cargo_manifest_received', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('vessels', sa.Column('work_permits_approved', sa.Boolean(), server_default='false', nullable=False))
    
    # Add foreign key constraint for berth
    op.create_foreign_key('fk_vessels_current_berth_id', 'vessels', 'berths', ['current_berth_id'], ['id'])
    
    # ============================================================================
    # CREATE DEFAULT DATA
    # ============================================================================
    
    # Insert default berths
    op.execute("""
        INSERT INTO berths (berth_number, berth_name, berth_type, length_meters, depth_meters, max_draft, max_loa, status, hourly_rate, daily_rate)
        VALUES 
            ('B01', 'Berth 1 - Container Terminal', 'Container', 250.0, 12.0, 11.0, 240.0, 'active', 50.00, 1000.00),
            ('B02', 'Berth 2 - RoRo Terminal', 'RoRo', 200.0, 8.0, 7.5, 190.0, 'active', 40.00, 800.00),
            ('B03', 'Berth 3 - General Cargo', 'General Cargo', 180.0, 10.0, 9.0, 170.0, 'active', 35.00, 700.00),
            ('B04', 'Berth 4 - Multi-Purpose', 'Multi-Purpose', 220.0, 11.0, 10.0, 210.0, 'active', 45.00, 900.00),
            ('B05', 'Berth 5 - Heavy Lift', 'Heavy Lift', 160.0, 15.0, 14.0, 150.0, 'active', 60.00, 1200.00)
    """)
    
    # Insert default port equipment
    op.execute("""
        INSERT INTO port_equipment (equipment_code, equipment_name, equipment_type, capacity_tons, status, maintenance_interval_hours, operating_cost_per_hour)
        VALUES 
            ('QC01', 'Quay Crane 1', 'Quay Crane', 50.0, 'available', 2000, 150.00),
            ('QC02', 'Quay Crane 2', 'Quay Crane', 50.0, 'available', 2000, 150.00),
            ('RST01', 'Reach Stacker 1', 'Reach Stacker', 40.0, 'available', 1500, 80.00),
            ('RST02', 'Reach Stacker 2', 'Reach Stacker', 40.0, 'available', 1500, 80.00),
            ('FL01', 'Forklift 1 - Heavy', 'Forklift', 15.0, 'available', 1000, 40.00),
            ('FL02', 'Forklift 2 - Heavy', 'Forklift', 15.0, 'available', 1000, 40.00),
            ('FL03', 'Forklift 3 - Standard', 'Forklift', 8.0, 'available', 800, 25.00),
            ('FL04', 'Forklift 4 - Standard', 'Forklift', 8.0, 'available', 800, 25.00),
            ('TT01', 'Terminal Tractor 1', 'Terminal Tractor', 25.0, 'available', 1200, 60.00),
            ('TT02', 'Terminal Tractor 2', 'Terminal Tractor', 25.0, 'available', 1200, 60.00)
    """)
    
    # Update existing vessels to reference default berths
    op.execute("""
        UPDATE vessels 
        SET 
            berth = (SELECT berth_number FROM berths ORDER BY id LIMIT 1),
            current_berth_id = (SELECT id FROM berths ORDER BY id LIMIT 1),
            pilot_required = true,
            agent_company = 'Port Services Ltd.'
        WHERE current_berth_id IS NULL
    """)


def downgrade():
    """
    Remove berth management and port infrastructure
    """
    
    # Remove foreign key constraints first
    op.drop_constraint('fk_vessels_current_berth_id', 'vessels', type_='foreignkey')
    
    # Remove enhanced vessel columns
    op.drop_column('vessels', 'work_permits_approved')
    op.drop_column('vessels', 'cargo_manifest_received')
    op.drop_column('vessels', 'agent_contact')
    op.drop_column('vessels', 'agent_company')
    op.drop_column('vessels', 'security_clearance')
    op.drop_column('vessels', 'health_clearance')
    op.drop_column('vessels', 'immigration_clearance')
    op.drop_column('vessels', 'customs_clearance')
    op.drop_column('vessels', 'tug_assistance')
    op.drop_column('vessels', 'pilot_required')
    op.drop_column('vessels', 'berth_departure_time')
    op.drop_column('vessels', 'berth_arrival_time')
    op.drop_column('vessels', 'current_berth_id')
    
    # Drop equipment tables (in reverse order)
    op.drop_index('ix_equipment_usage_start_time', table_name='equipment_usage')
    op.drop_index('ix_equipment_usage_operator_id', table_name='equipment_usage')
    op.drop_index('ix_equipment_usage_vessel_id', table_name='equipment_usage')
    op.drop_index('ix_equipment_usage_equipment_id', table_name='equipment_usage')
    op.drop_table('equipment_usage')
    
    op.drop_index('ix_port_equipment_assigned_operator_id', table_name='port_equipment')
    op.drop_index('ix_port_equipment_status', table_name='port_equipment')
    op.drop_index('ix_port_equipment_equipment_type', table_name='port_equipment')
    op.drop_index('ix_port_equipment_equipment_code', table_name='port_equipment')
    op.drop_table('port_equipment')
    
    # Drop ship operations table
    op.drop_index('ix_ship_operations_planned_start', table_name='ship_operations')
    op.drop_index('ix_ship_operations_operation_status', table_name='ship_operations')
    op.drop_index('ix_ship_operations_operation_type', table_name='ship_operations')
    op.drop_index('ix_ship_operations_berth_id', table_name='ship_operations')
    op.drop_index('ix_ship_operations_vessel_id', table_name='ship_operations')
    op.drop_table('ship_operations')
    
    # Drop berth tables
    op.drop_index('ix_berth_reservations_priority', table_name='berth_reservations')
    op.drop_index('ix_berth_reservations_reservation_type', table_name='berth_reservations')
    op.drop_index('ix_berth_reservations_reservation_start', table_name='berth_reservations')
    op.drop_index('ix_berth_reservations_vessel_id', table_name='berth_reservations')
    op.drop_index('ix_berth_reservations_berth_id', table_name='berth_reservations')
    op.drop_table('berth_reservations')
    
    op.drop_index('ix_berths_status', table_name='berths')
    op.drop_index('ix_berths_berth_type', table_name='berths')
    op.drop_index('ix_berths_berth_number', table_name='berths')
    op.drop_table('berths')