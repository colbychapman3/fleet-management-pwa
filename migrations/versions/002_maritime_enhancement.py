"""Add maritime stevedoring features

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 10:00:00.000000

This migration transforms the Fleet Management PWA into a Maritime Stevedoring System
by adding specialized fields and tables for stevedoring operations while preserving
all existing functionality.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add maritime stevedoring capabilities to existing schema
    """
    
    # ============================================================================
    # ENHANCE VESSELS TABLE FOR MARITIME OPERATIONS
    # ============================================================================
    
    # Add maritime-specific vessel fields
    op.add_column('vessels', sa.Column('shipping_line', sa.String(50), nullable=True))
    op.add_column('vessels', sa.Column('berth', sa.String(20), nullable=True))
    op.add_column('vessels', sa.Column('operation_type', sa.String(50), 
                                     server_default='Discharge Only', nullable=False))
    op.add_column('vessels', sa.Column('operation_manager', sa.String(100), nullable=True))
    
    # Team assignments
    op.add_column('vessels', sa.Column('auto_ops_lead', sa.String(100), nullable=True))
    op.add_column('vessels', sa.Column('auto_ops_assistant', sa.String(100), nullable=True))
    op.add_column('vessels', sa.Column('heavy_ops_lead', sa.String(100), nullable=True))
    op.add_column('vessels', sa.Column('heavy_ops_assistant', sa.String(100), nullable=True))
    
    # Cargo and vehicle tracking
    op.add_column('vessels', sa.Column('total_vehicles', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('total_automobiles_discharge', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('heavy_equipment_discharge', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('total_electric_vehicles', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('total_static_cargo', sa.Integer(), 
                                     server_default='0', nullable=False))
    
    # Maritime zone targets (BRV, ZEE, SOU)
    op.add_column('vessels', sa.Column('brv_target', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('zee_target', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('sou_target', sa.Integer(), 
                                     server_default='0', nullable=False))
    
    # Operational parameters
    op.add_column('vessels', sa.Column('expected_rate', sa.Integer(), 
                                     server_default='150', nullable=False))
    op.add_column('vessels', sa.Column('total_drivers', sa.Integer(), 
                                     server_default='30', nullable=False))
    op.add_column('vessels', sa.Column('shift_start', sa.Time(), nullable=True))
    op.add_column('vessels', sa.Column('shift_end', sa.Time(), nullable=True))
    op.add_column('vessels', sa.Column('break_duration', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('target_completion', sa.String(50), nullable=True))
    
    # TICO transportation
    op.add_column('vessels', sa.Column('tico_vans', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('tico_station_wagons', sa.Integer(), 
                                     server_default='0', nullable=False))
    
    # Progress tracking
    op.add_column('vessels', sa.Column('progress', sa.Integer(), 
                                     server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('start_time', sa.DateTime(), nullable=True))
    op.add_column('vessels', sa.Column('estimated_completion', sa.DateTime(), nullable=True))
    
    # JSON data fields for widget data
    op.add_column('vessels', sa.Column('deck_data', sa.Text(), nullable=True))
    op.add_column('vessels', sa.Column('turnaround_data', sa.Text(), nullable=True))
    op.add_column('vessels', sa.Column('inventory_data', sa.Text(), nullable=True))
    op.add_column('vessels', sa.Column('hourly_quantity_data', sa.Text(), nullable=True))
    
    # ============================================================================
    # CREATE NEW MARITIME-SPECIFIC TABLES
    # ============================================================================
    
    # Cargo operations tracking table
    op.create_table('cargo_operations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('zone', sa.String(10), nullable=True),  # BRV, ZEE, SOU
        sa.Column('vehicle_type', sa.String(50), nullable=True),  # Sedan, SUV, Truck, etc.
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('discharged', sa.Integer(), server_default='0', nullable=False),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cargo_operations_vessel_id', 'cargo_operations', ['vessel_id'])
    op.create_index('ix_cargo_operations_zone', 'cargo_operations', ['zone'])
    
    # Stevedore teams table
    op.create_table('stevedore_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('team_type', sa.String(50), nullable=True),  # Auto Ops, Heavy Ops, General
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('assistant_id', sa.Integer(), nullable=True),
        sa.Column('members', sa.Text(), nullable=True),  # JSON array of member IDs
        sa.Column('shift_start', sa.Time(), nullable=True),
        sa.Column('shift_end', sa.Time(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assistant_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_stevedore_teams_vessel_id', 'stevedore_teams', ['vessel_id'])
    op.create_index('ix_stevedore_teams_team_type', 'stevedore_teams', ['team_type'])
    
    # TICO vehicles table
    op.create_table('tico_vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_type', sa.String(20), nullable=True),  # Van, Station Wagon
        sa.Column('vehicle_id', sa.String(20), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('current_load', sa.Integer(), server_default='0', nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), server_default='available', nullable=False),  # available, in_transit, maintenance
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tico_vehicles_vessel_id', 'tico_vehicles', ['vessel_id'])
    op.create_index('ix_tico_vehicles_status', 'tico_vehicles', ['status'])
    
    # Maritime documents table
    op.create_table('maritime_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('document_type', sa.String(50), nullable=True),  # Cargo Manifest, Work Order, etc.
        sa.Column('file_path', sa.String(255), nullable=True),
        sa.Column('processed_data', sa.Text(), nullable=True),  # JSON of extracted data
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_maritime_documents_vessel_id', 'maritime_documents', ['vessel_id'])
    op.create_index('ix_maritime_documents_document_type', 'maritime_documents', ['document_type'])
    
    # Real-time discharge progress table
    op.create_table('discharge_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=False),
        sa.Column('zone', sa.String(10), nullable=True),  # BRV, ZEE, SOU
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('vehicles_discharged', sa.Integer(), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('total_progress', sa.Numeric(5, 2), nullable=True),  # Percentage
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_discharge_progress_vessel_id', 'discharge_progress', ['vessel_id'])
    op.create_index('ix_discharge_progress_timestamp', 'discharge_progress', ['timestamp'])
    op.create_index('ix_discharge_progress_zone', 'discharge_progress', ['zone'])
    
    # ============================================================================
    # ENHANCE USERS TABLE FOR MARITIME ROLES
    # ============================================================================
    
    # Add maritime-specific user fields
    op.add_column('users', sa.Column('employee_id', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('department', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('shift_preference', sa.String(20), nullable=True))  # morning, afternoon, night
    op.add_column('users', sa.Column('certifications', sa.Text(), nullable=True))  # JSON array of certifications
    op.add_column('users', sa.Column('tico_driver_license', sa.Boolean(), server_default='false', nullable=False))
    
    # ============================================================================
    # ENHANCE TASKS TABLE FOR MARITIME OPERATIONS
    # ============================================================================
    
    # Add maritime-specific task fields
    op.add_column('tasks', sa.Column('zone', sa.String(10), nullable=True))  # BRV, ZEE, SOU
    op.add_column('tasks', sa.Column('cargo_type', sa.String(50), nullable=True))
    op.add_column('tasks', sa.Column('discharge_quantity', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('team_assignment', sa.String(50), nullable=True))
    op.add_column('tasks', sa.Column('safety_requirements', sa.Text(), nullable=True))
    
    # ============================================================================
    # UPDATE DEFAULT VALUES AND CONSTRAINTS
    # ============================================================================
    
    # Update existing vessels with default maritime values
    op.execute("""
        UPDATE vessels 
        SET 
            operation_type = 'Discharge Only',
            expected_rate = 150,
            total_drivers = 30,
            berth = 'TBD',
            shipping_line = 'Unknown'
        WHERE operation_type IS NULL OR expected_rate IS NULL
    """)
    
    # Update existing users with default maritime roles
    op.execute("""
        UPDATE users 
        SET 
            role = CASE 
                WHEN role = 'manager' THEN 'maritime_manager'
                WHEN role = 'worker' THEN 'stevedore'
                ELSE role 
            END,
            department = 'Maritime Operations',
            tico_driver_license = false
        WHERE department IS NULL
    """)
    
    # Update existing tasks with maritime context
    op.execute("""
        UPDATE tasks 
        SET 
            task_type = CASE 
                WHEN task_type = 'maintenance' THEN 'vessel_maintenance'
                WHEN task_type = 'inspection' THEN 'cargo_inspection'
                WHEN task_type = 'cleaning' THEN 'deck_cleaning'
                ELSE task_type 
            END,
            zone = 'General'
        WHERE zone IS NULL
    """)


def downgrade():
    """
    Remove maritime stevedoring features and revert to basic fleet management
    """
    
    # Drop new maritime tables (in reverse order due to foreign keys)
    op.drop_index('ix_discharge_progress_zone', table_name='discharge_progress')
    op.drop_index('ix_discharge_progress_timestamp', table_name='discharge_progress')
    op.drop_index('ix_discharge_progress_vessel_id', table_name='discharge_progress')
    op.drop_table('discharge_progress')
    
    op.drop_index('ix_maritime_documents_document_type', table_name='maritime_documents')
    op.drop_index('ix_maritime_documents_vessel_id', table_name='maritime_documents')
    op.drop_table('maritime_documents')
    
    op.drop_index('ix_tico_vehicles_status', table_name='tico_vehicles')
    op.drop_index('ix_tico_vehicles_vessel_id', table_name='tico_vehicles')
    op.drop_table('tico_vehicles')
    
    op.drop_index('ix_stevedore_teams_team_type', table_name='stevedore_teams')
    op.drop_index('ix_stevedore_teams_vessel_id', table_name='stevedore_teams')
    op.drop_table('stevedore_teams')
    
    op.drop_index('ix_cargo_operations_zone', table_name='cargo_operations')
    op.drop_index('ix_cargo_operations_vessel_id', table_name='cargo_operations')
    op.drop_table('cargo_operations')
    
    # Remove maritime columns from tasks table
    op.drop_column('tasks', 'safety_requirements')
    op.drop_column('tasks', 'team_assignment')
    op.drop_column('tasks', 'discharge_quantity')
    op.drop_column('tasks', 'cargo_type')
    op.drop_column('tasks', 'zone')
    
    # Remove maritime columns from users table
    op.drop_column('users', 'tico_driver_license')
    op.drop_column('users', 'certifications')
    op.drop_column('users', 'shift_preference')
    op.drop_column('users', 'department')
    op.drop_column('users', 'employee_id')
    
    # Remove maritime columns from vessels table
    op.drop_column('vessels', 'hourly_quantity_data')
    op.drop_column('vessels', 'inventory_data')
    op.drop_column('vessels', 'turnaround_data')
    op.drop_column('vessels', 'deck_data')
    op.drop_column('vessels', 'estimated_completion')
    op.drop_column('vessels', 'start_time')
    op.drop_column('vessels', 'progress')
    op.drop_column('vessels', 'tico_station_wagons')
    op.drop_column('vessels', 'tico_vans')
    op.drop_column('vessels', 'target_completion')
    op.drop_column('vessels', 'break_duration')
    op.drop_column('vessels', 'shift_end')
    op.drop_column('vessels', 'shift_start')
    op.drop_column('vessels', 'total_drivers')
    op.drop_column('vessels', 'expected_rate')
    op.drop_column('vessels', 'sou_target')
    op.drop_column('vessels', 'zee_target')
    op.drop_column('vessels', 'brv_target')
    op.drop_column('vessels', 'total_static_cargo')
    op.drop_column('vessels', 'total_electric_vehicles')
    op.drop_column('vessels', 'heavy_equipment_discharge')
    op.drop_column('vessels', 'total_automobiles_discharge')
    op.drop_column('vessels', 'total_vehicles')
    op.drop_column('vessels', 'heavy_ops_assistant')
    op.drop_column('vessels', 'heavy_ops_lead')
    op.drop_column('vessels', 'auto_ops_assistant')
    op.drop_column('vessels', 'auto_ops_lead')
    op.drop_column('vessels', 'operation_manager')
    op.drop_column('vessels', 'operation_type')
    op.drop_column('vessels', 'berth')
    op.drop_column('vessels', 'shipping_line')
    
    # Revert user roles to original values
    op.execute("""
        UPDATE users 
        SET 
            role = CASE 
                WHEN role = 'maritime_manager' THEN 'manager'
                WHEN role = 'stevedore' THEN 'worker'
                WHEN role LIKE '%_lead' THEN 'worker'
                WHEN role = 'tico_driver' THEN 'worker'
                ELSE 'worker'
            END
    """)
    
    # Revert task types to original values
    op.execute("""
        UPDATE tasks 
        SET 
            task_type = CASE 
                WHEN task_type = 'vessel_maintenance' THEN 'maintenance'
                WHEN task_type = 'cargo_inspection' THEN 'inspection'
                WHEN task_type = 'deck_cleaning' THEN 'cleaning'
                ELSE task_type 
            END
    """)