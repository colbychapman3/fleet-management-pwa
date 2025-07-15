"""Add comprehensive data validation constraints

Revision ID: 005
Revises: 004
Create Date: 2024-01-15 13:00:00.000000

This migration adds comprehensive data validation constraints, check constraints,
and business rule validation to ensure data integrity in maritime operations.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add comprehensive data validation constraints
    """
    
    # ============================================================================
    # VESSEL VALIDATION CONSTRAINTS
    # ============================================================================
    
    # Add check constraints for vessel dimensions and capacities
    op.create_check_constraint(
        'ck_vessels_length_positive',
        'vessels',
        sa.Column('length') >= 0
    )
    
    op.create_check_constraint(
        'ck_vessels_beam_positive',
        'vessels',
        sa.Column('beam') >= 0
    )
    
    op.create_check_constraint(
        'ck_vessels_draft_positive',
        'vessels',
        sa.Column('draft') >= 0
    )
    
    op.create_check_constraint(
        'ck_vessels_tonnage_positive',
        'vessels',
        sa.and_(
            sa.Column('gross_tonnage') >= 0,
            sa.Column('net_tonnage') >= 0
        )
    )
    
    op.create_check_constraint(
        'ck_vessels_vehicle_counts_positive',
        'vessels',
        sa.and_(
            sa.Column('total_vehicles') >= 0,
            sa.Column('total_automobiles_discharge') >= 0,
            sa.Column('heavy_equipment_discharge') >= 0,
            sa.Column('total_electric_vehicles') >= 0,
            sa.Column('total_static_cargo') >= 0
        )
    )
    
    op.create_check_constraint(
        'ck_vessels_zone_targets_positive',
        'vessels',
        sa.and_(
            sa.Column('brv_target') >= 0,
            sa.Column('zee_target') >= 0,
            sa.Column('sou_target') >= 0
        )
    )
    
    op.create_check_constraint(
        'ck_vessels_operational_values',
        'vessels',
        sa.and_(
            sa.Column('expected_rate') > 0,
            sa.Column('total_drivers') >= 0,
            sa.Column('break_duration') >= 0,
            sa.Column('progress') >= 0,
            sa.Column('progress') <= 100
        )
    )
    
    op.create_check_constraint(
        'ck_vessels_tico_vehicles_positive',
        'vessels',
        sa.and_(
            sa.Column('tico_vans') >= 0,
            sa.Column('tico_station_wagons') >= 0
        )
    )
    
    op.create_check_constraint(
        'ck_vessels_status_valid',
        'vessels',
        sa.Column('status').in_(['active', 'inactive', 'in_port', 'at_sea', 'maintenance', 'discharging', 'loading'])
    )
    
    op.create_check_constraint(
        'ck_vessels_operation_type_valid',
        'vessels',
        sa.Column('operation_type').in_(['Discharge Only', 'Loading Only', 'Discharge and Loading', 'Bunkering', 'Maintenance', 'Transit'])
    )
    
    # ============================================================================
    # USER VALIDATION CONSTRAINTS
    # ============================================================================
    
    op.create_check_constraint(
        'ck_users_email_format',
        'users',
        sa.Column('email').op('~')('[^@]+@[^@]+\.[^@]+')
    )
    
    op.create_check_constraint(
        'ck_users_role_valid',
        'users',
        sa.Column('role').in_([
            'admin', 'maritime_manager', 'operations_supervisor', 'stevedore', 
            'auto_ops_lead', 'heavy_ops_lead', 'tico_driver', 'crane_operator',
            'forklift_operator', 'quality_inspector', 'safety_officer'
        ])
    )
    
    op.create_check_constraint(
        'ck_users_shift_preference_valid',
        'users',
        sa.Column('shift_preference').in_(['morning', 'afternoon', 'night', 'rotating'])
    )
    
    op.create_check_constraint(
        'ck_users_performance_scores',
        'users',
        sa.and_(
            sa.or_(sa.Column('productivity_score').is_(None), sa.and_(sa.Column('productivity_score') >= 0, sa.Column('productivity_score') <= 5)),
            sa.or_(sa.Column('safety_record_score').is_(None), sa.and_(sa.Column('safety_record_score') >= 0, sa.Column('safety_record_score') <= 5))
        )
    )
    
    op.create_check_constraint(
        'ck_users_hours_worked_positive',
        'users',
        sa.Column('hours_worked_this_month') >= 0
    )
    
    # ============================================================================
    # TASK VALIDATION CONSTRAINTS
    # ============================================================================
    
    op.create_check_constraint(
        'ck_tasks_priority_valid',
        'tasks',
        sa.Column('priority').in_(['low', 'medium', 'high', 'urgent'])
    )
    
    op.create_check_constraint(
        'ck_tasks_status_valid',
        'tasks',
        sa.Column('status').in_(['pending', 'in_progress', 'completed', 'cancelled', 'on_hold'])
    )
    
    op.create_check_constraint(
        'ck_tasks_zone_valid',
        'tasks',
        sa.Column('zone').in_(['BRV', 'ZEE', 'SOU', 'General', 'Equipment', 'Administrative'])
    )
    
    op.create_check_constraint(
        'ck_tasks_hours_positive',
        'tasks',
        sa.and_(
            sa.or_(sa.Column('estimated_hours').is_(None), sa.Column('estimated_hours') >= 0),
            sa.or_(sa.Column('actual_hours').is_(None), sa.Column('actual_hours') >= 0)
        )
    )
    
    op.create_check_constraint(
        'ck_tasks_discharge_quantity_positive',
        'tasks',
        sa.or_(sa.Column('discharge_quantity').is_(None), sa.Column('discharge_quantity') >= 0)
    )
    
    # ============================================================================
    # CARGO OPERATIONS VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_cargo_operations_zone_valid',
        'cargo_operations',
        sa.Column('zone').in_(['BRV', 'ZEE', 'SOU', 'General'])
    )
    
    op.create_check_constraint(
        'ck_cargo_operations_quantities',
        'cargo_operations',
        sa.and_(
            sa.Column('quantity') >= 0,
            sa.Column('discharged') >= 0,
            sa.Column('discharged') <= sa.Column('quantity')
        )
    )
    
    op.create_check_constraint(
        'ck_cargo_operations_vehicle_type_valid',
        'cargo_operations',
        sa.Column('vehicle_type').in_([
            'Sedan', 'Hatchback', 'SUV', 'Pickup Truck', 'Van', 'Bus',
            'Heavy Truck', 'Trailer', 'Construction Vehicle', 'Electric Vehicle',
            'Motorcycle', 'Agricultural Vehicle', 'Special Purpose Vehicle'
        ])
    )
    
    # ============================================================================
    # STEVEDORE TEAMS VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_stevedore_teams_type_valid',
        'stevedore_teams',
        sa.Column('team_type').in_(['Auto Ops', 'Heavy Ops', 'General', 'Maintenance', 'Quality Control'])
    )
    
    # ============================================================================
    # TICO VEHICLES VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_tico_vehicles_type_valid',
        'tico_vehicles',
        sa.Column('vehicle_type').in_(['Van', 'Station Wagon', 'Bus', 'Minibus'])
    )
    
    op.create_check_constraint(
        'ck_tico_vehicles_capacity',
        'tico_vehicles',
        sa.and_(
            sa.Column('capacity') > 0,
            sa.Column('current_load') >= 0,
            sa.Column('current_load') <= sa.Column('capacity')
        )
    )
    
    op.create_check_constraint(
        'ck_tico_vehicles_status_valid',
        'tico_vehicles',
        sa.Column('status').in_(['available', 'in_transit', 'maintenance', 'out_of_service'])
    )
    
    # ============================================================================
    # DISCHARGE PROGRESS VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_discharge_progress_zone_valid',
        'discharge_progress',
        sa.Column('zone').in_(['BRV', 'ZEE', 'SOU', 'General'])
    )
    
    op.create_check_constraint(
        'ck_discharge_progress_values',
        'discharge_progress',
        sa.and_(
            sa.or_(sa.Column('vehicles_discharged').is_(None), sa.Column('vehicles_discharged') >= 0),
            sa.or_(sa.Column('hourly_rate').is_(None), sa.Column('hourly_rate') >= 0),
            sa.or_(sa.Column('total_progress').is_(None), sa.and_(sa.Column('total_progress') >= 0, sa.Column('total_progress') <= 100))
        )
    )
    
    # ============================================================================
    # BERTH VALIDATION CONSTRAINTS
    # ============================================================================
    
    op.create_check_constraint(
        'ck_berths_dimensions_positive',
        'berths',
        sa.and_(
            sa.or_(sa.Column('length_meters').is_(None), sa.Column('length_meters') > 0),
            sa.or_(sa.Column('depth_meters').is_(None), sa.Column('depth_meters') > 0),
            sa.or_(sa.Column('max_draft').is_(None), sa.Column('max_draft') > 0),
            sa.or_(sa.Column('max_loa').is_(None), sa.Column('max_loa') > 0)
        )
    )
    
    op.create_check_constraint(
        'ck_berths_equipment_positive',
        'berths',
        sa.and_(
            sa.or_(sa.Column('bollards_count').is_(None), sa.Column('bollards_count') >= 0),
            sa.or_(sa.Column('crane_capacity').is_(None), sa.Column('crane_capacity') >= 0),
            sa.or_(sa.Column('electrical_capacity').is_(None), sa.Column('electrical_capacity') >= 0)
        )
    )
    
    op.create_check_constraint(
        'ck_berths_rates_positive',
        'berths',
        sa.and_(
            sa.or_(sa.Column('hourly_rate').is_(None), sa.Column('hourly_rate') >= 0),
            sa.or_(sa.Column('daily_rate').is_(None), sa.Column('daily_rate') >= 0)
        )
    )
    
    op.create_check_constraint(
        'ck_berths_status_valid',
        'berths',
        sa.Column('status').in_(['active', 'maintenance', 'closed', 'reserved'])
    )
    
    op.create_check_constraint(
        'ck_berths_type_valid',
        'berths',
        sa.Column('berth_type').in_(['Container', 'RoRo', 'General Cargo', 'Multi-Purpose', 'Heavy Lift', 'Bulk', 'Passenger'])
    )
    
    # ============================================================================
    # BERTH RESERVATIONS VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_berth_reservations_time_logical',
        'berth_reservations',
        sa.Column('reservation_end') > sa.Column('reservation_start')
    )
    
    op.create_check_constraint(
        'ck_berth_reservations_actual_time_logical',
        'berth_reservations',
        sa.or_(
            sa.Column('actual_departure').is_(None),
            sa.Column('actual_arrival').is_(None),
            sa.Column('actual_departure') > sa.Column('actual_arrival')
        )
    )
    
    op.create_check_constraint(
        'ck_berth_reservations_type_valid',
        'berth_reservations',
        sa.Column('reservation_type').in_(['tentative', 'confirmed', 'completed', 'cancelled'])
    )
    
    op.create_check_constraint(
        'ck_berth_reservations_priority_valid',
        'berth_reservations',
        sa.Column('priority').in_(['low', 'normal', 'high', 'urgent'])
    )
    
    op.create_check_constraint(
        'ck_berth_reservations_duration_positive',
        'berth_reservations',
        sa.and_(
            sa.or_(sa.Column('estimated_duration').is_(None), sa.Column('estimated_duration') > 0),
            sa.or_(sa.Column('actual_duration').is_(None), sa.Column('actual_duration') > 0),
            sa.or_(sa.Column('total_cost').is_(None), sa.Column('total_cost') >= 0)
        )
    )
    
    # ============================================================================
    # SHIP OPERATIONS VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_ship_operations_type_valid',
        'ship_operations',
        sa.Column('operation_type').in_(['Discharge', 'Loading', 'Bunkering', 'Maintenance', 'Inspection', 'Repair'])
    )
    
    op.create_check_constraint(
        'ck_ship_operations_status_valid',
        'ship_operations',
        sa.Column('operation_status').in_(['planned', 'in_progress', 'completed', 'suspended', 'cancelled'])
    )
    
    op.create_check_constraint(
        'ck_ship_operations_time_logical',
        'ship_operations',
        sa.and_(
            sa.or_(
                sa.Column('planned_end').is_(None),
                sa.Column('planned_start').is_(None),
                sa.Column('planned_end') > sa.Column('planned_start')
            ),
            sa.or_(
                sa.Column('actual_end').is_(None),
                sa.Column('actual_start').is_(None),
                sa.Column('actual_end') > sa.Column('actual_start')
            )
        )
    )
    
    op.create_check_constraint(
        'ck_ship_operations_crew_positive',
        'ship_operations',
        sa.or_(sa.Column('crew_size').is_(None), sa.Column('crew_size') >= 0)
    )
    
    op.create_check_constraint(
        'ck_ship_operations_efficiency_valid',
        'ship_operations',
        sa.or_(
            sa.Column('efficiency_rating').is_(None), 
            sa.and_(sa.Column('efficiency_rating') >= 0, sa.Column('efficiency_rating') <= 5)
        )
    )
    
    # ============================================================================
    # PORT EQUIPMENT VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_port_equipment_capacity_positive',
        'port_equipment',
        sa.or_(sa.Column('capacity_tons').is_(None), sa.Column('capacity_tons') > 0)
    )
    
    op.create_check_constraint(
        'ck_port_equipment_hours_positive',
        'port_equipment',
        sa.and_(
            sa.Column('operating_hours') >= 0,
            sa.Column('maintenance_interval_hours') > 0
        )
    )
    
    op.create_check_constraint(
        'ck_port_equipment_year_valid',
        'port_equipment',
        sa.or_(
            sa.Column('year_manufactured').is_(None),
            sa.and_(sa.Column('year_manufactured') >= 1900, sa.Column('year_manufactured') <= sa.extract('year', sa.func.current_date()) + 1)
        )
    )
    
    op.create_check_constraint(
        'ck_port_equipment_status_valid',
        'port_equipment',
        sa.Column('status').in_(['available', 'in_use', 'maintenance', 'out_of_service'])
    )
    
    op.create_check_constraint(
        'ck_port_equipment_costs_positive',
        'port_equipment',
        sa.and_(
            sa.or_(sa.Column('fuel_consumption_rate').is_(None), sa.Column('fuel_consumption_rate') >= 0),
            sa.or_(sa.Column('operating_cost_per_hour').is_(None), sa.Column('operating_cost_per_hour') >= 0)
        )
    )
    
    # ============================================================================
    # EQUIPMENT USAGE VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_equipment_usage_time_logical',
        'equipment_usage',
        sa.or_(
            sa.Column('end_time').is_(None),
            sa.Column('end_time') > sa.Column('start_time')
        )
    )
    
    op.create_check_constraint(
        'ck_equipment_usage_hours_logical',
        'equipment_usage',
        sa.or_(
            sa.Column('end_hour_meter').is_(None),
            sa.Column('start_hour_meter').is_(None),
            sa.Column('end_hour_meter') >= sa.Column('start_hour_meter')
        )
    )
    
    op.create_check_constraint(
        'ck_equipment_usage_values_positive',
        'equipment_usage',
        sa.and_(
            sa.or_(sa.Column('fuel_consumed').is_(None), sa.Column('fuel_consumed') >= 0),
            sa.or_(sa.Column('cargo_handled_tons').is_(None), sa.Column('cargo_handled_tons') >= 0),
            sa.or_(sa.Column('cycles_completed').is_(None), sa.Column('cycles_completed') >= 0),
            sa.or_(
                sa.Column('efficiency_rating').is_(None), 
                sa.and_(sa.Column('efficiency_rating') >= 0, sa.Column('efficiency_rating') <= 5)
            )
        )
    )
    
    # ============================================================================
    # PERFORMANCE METRICS VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_performance_metrics_category_valid',
        'performance_metrics',
        sa.Column('metric_category').in_(['Operational', 'Financial', 'Safety', 'Equipment', 'Environmental', 'Quality'])
    )
    
    op.create_check_constraint(
        'ck_performance_metrics_period_valid',
        'performance_metrics',
        sa.or_(
            sa.Column('measurement_period').is_(None),
            sa.Column('measurement_period').in_(['hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'])
        )
    )
    
    # ============================================================================
    # ANALYTICS SUMMARY VALIDATION
    # ============================================================================
    
    op.create_check_constraint(
        'ck_analytics_summary_values_positive',
        'analytics_summary',
        sa.and_(
            sa.Column('total_vehicles_processed') >= 0,
            sa.Column('total_hours_worked') >= 0,
            sa.Column('average_hourly_rate') >= 0,
            sa.Column('equipment_utilization') >= 0,
            sa.Column('equipment_utilization') <= 100,
            sa.Column('berth_utilization') >= 0,
            sa.Column('berth_utilization') <= 100,
            sa.Column('total_revenue') >= 0,
            sa.Column('total_costs') >= 0,
            sa.Column('efficiency_score') >= 0,
            sa.Column('efficiency_score') <= 5,
            sa.Column('safety_incidents') >= 0,
            sa.Column('weather_delays') >= 0
        )
    )
    
    # ============================================================================
    # ADD NOT NULL CONSTRAINTS FOR CRITICAL FIELDS
    # ============================================================================
    
    # Ensure critical vessel fields are not null
    op.alter_column('vessels', 'name', nullable=False)
    op.alter_column('vessels', 'vessel_type', nullable=False)
    
    # Ensure critical user fields are not null
    op.alter_column('users', 'email', nullable=False)
    op.alter_column('users', 'username', nullable=False)
    op.alter_column('users', 'role', nullable=False)
    
    # Ensure critical task fields are not null
    op.alter_column('tasks', 'title', nullable=False)
    op.alter_column('tasks', 'task_type', nullable=False)
    op.alter_column('tasks', 'created_by_id', nullable=False)
    
    # ============================================================================
    # CREATE BUSINESS RULE VALIDATION FUNCTIONS (PostgreSQL)
    # ============================================================================
    
    try:
        # Function to validate berth availability during reservation
        op.execute("""
            CREATE OR REPLACE FUNCTION validate_berth_availability()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Check for overlapping reservations
                IF EXISTS (
                    SELECT 1 FROM berth_reservations 
                    WHERE berth_id = NEW.berth_id 
                    AND id != COALESCE(NEW.id, -1)
                    AND reservation_type IN ('confirmed', 'tentative')
                    AND (
                        (NEW.reservation_start BETWEEN reservation_start AND reservation_end) OR
                        (NEW.reservation_end BETWEEN reservation_start AND reservation_end) OR
                        (reservation_start BETWEEN NEW.reservation_start AND NEW.reservation_end)
                    )
                ) THEN
                    RAISE EXCEPTION 'Berth % is not available during the requested time period', NEW.berth_id;
                END IF;
                
                -- Check berth capacity constraints
                IF EXISTS (
                    SELECT 1 FROM berths b
                    JOIN vessels v ON v.id = NEW.vessel_id
                    WHERE b.id = NEW.berth_id
                    AND (
                        (b.max_loa IS NOT NULL AND v.length > b.max_loa) OR
                        (b.max_draft IS NOT NULL AND v.draft > b.max_draft)
                    )
                ) THEN
                    RAISE EXCEPTION 'Vessel dimensions exceed berth capacity limits';
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        op.execute("""
            CREATE TRIGGER trigger_validate_berth_availability
            BEFORE INSERT OR UPDATE ON berth_reservations
            FOR EACH ROW
            EXECUTE FUNCTION validate_berth_availability();
        """)
        
        # Function to validate cargo operation consistency
        op.execute("""
            CREATE OR REPLACE FUNCTION validate_cargo_operation()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Ensure discharged amount doesn't exceed total vessel capacity
                IF EXISTS (
                    SELECT 1 FROM vessels v
                    WHERE v.id = NEW.vessel_id
                    AND v.total_vehicles IS NOT NULL
                    AND (
                        SELECT COALESCE(SUM(discharged), 0) 
                        FROM cargo_operations 
                        WHERE vessel_id = NEW.vessel_id 
                        AND id != COALESCE(NEW.id, -1)
                    ) + NEW.discharged > v.total_vehicles
                ) THEN
                    RAISE EXCEPTION 'Total discharged vehicles cannot exceed vessel capacity';
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        op.execute("""
            CREATE TRIGGER trigger_validate_cargo_operation
            BEFORE INSERT OR UPDATE ON cargo_operations
            FOR EACH ROW
            EXECUTE FUNCTION validate_cargo_operation();
        """)
        
    except Exception:
        # Skip triggers for non-PostgreSQL databases
        pass


def downgrade():
    """
    Remove data validation constraints
    """
    
    # Drop business rule validation (PostgreSQL)
    try:
        op.execute("DROP TRIGGER IF EXISTS trigger_validate_cargo_operation ON cargo_operations")
        op.execute("DROP TRIGGER IF EXISTS trigger_validate_berth_availability ON berth_reservations")
        op.execute("DROP FUNCTION IF EXISTS validate_cargo_operation()")
        op.execute("DROP FUNCTION IF EXISTS validate_berth_availability()")
    except Exception:
        pass
    
    # Revert NOT NULL constraints
    op.alter_column('tasks', 'created_by_id', nullable=True)
    op.alter_column('tasks', 'task_type', nullable=True)
    op.alter_column('tasks', 'title', nullable=True)
    
    op.alter_column('users', 'role', nullable=True)
    op.alter_column('users', 'username', nullable=True)
    op.alter_column('users', 'email', nullable=True)
    
    op.alter_column('vessels', 'vessel_type', nullable=True)
    op.alter_column('vessels', 'name', nullable=True)
    
    # Drop all check constraints
    constraint_names = [
        'ck_analytics_summary_values_positive',
        'ck_performance_metrics_period_valid',
        'ck_performance_metrics_category_valid',
        'ck_equipment_usage_values_positive',
        'ck_equipment_usage_hours_logical',
        'ck_equipment_usage_time_logical',
        'ck_port_equipment_costs_positive',
        'ck_port_equipment_status_valid',
        'ck_port_equipment_year_valid',
        'ck_port_equipment_hours_positive',
        'ck_port_equipment_capacity_positive',
        'ck_ship_operations_efficiency_valid',
        'ck_ship_operations_crew_positive',
        'ck_ship_operations_time_logical',
        'ck_ship_operations_status_valid',
        'ck_ship_operations_type_valid',
        'ck_berth_reservations_duration_positive',
        'ck_berth_reservations_priority_valid',
        'ck_berth_reservations_type_valid',
        'ck_berth_reservations_actual_time_logical',
        'ck_berth_reservations_time_logical',
        'ck_berths_type_valid',
        'ck_berths_status_valid',
        'ck_berths_rates_positive',
        'ck_berths_equipment_positive',
        'ck_berths_dimensions_positive',
        'ck_discharge_progress_values',
        'ck_discharge_progress_zone_valid',
        'ck_tico_vehicles_status_valid',
        'ck_tico_vehicles_capacity',
        'ck_tico_vehicles_type_valid',
        'ck_stevedore_teams_type_valid',
        'ck_cargo_operations_vehicle_type_valid',
        'ck_cargo_operations_quantities',
        'ck_cargo_operations_zone_valid',
        'ck_tasks_discharge_quantity_positive',
        'ck_tasks_hours_positive',
        'ck_tasks_zone_valid',
        'ck_tasks_status_valid',
        'ck_tasks_priority_valid',
        'ck_users_hours_worked_positive',
        'ck_users_performance_scores',
        'ck_users_shift_preference_valid',
        'ck_users_role_valid',
        'ck_users_email_format',
        'ck_vessels_operation_type_valid',
        'ck_vessels_status_valid',
        'ck_vessels_tico_vehicles_positive',
        'ck_vessels_operational_values',
        'ck_vessels_zone_targets_positive',
        'ck_vessels_vehicle_counts_positive',
        'ck_vessels_tonnage_positive',
        'ck_vessels_draft_positive',
        'ck_vessels_beam_positive',
        'ck_vessels_length_positive'
    ]
    
    for constraint_name in constraint_names:
        try:
            op.drop_constraint(constraint_name, 'vessels', type_='check')
        except Exception:
            try:
                op.drop_constraint(constraint_name, 'users', type_='check')
            except Exception:
                try:
                    op.drop_constraint(constraint_name, 'tasks', type_='check')
                except Exception:
                    try:
                        op.drop_constraint(constraint_name, 'cargo_operations', type_='check')
                    except Exception:
                        try:
                            op.drop_constraint(constraint_name, 'stevedore_teams', type_='check')
                        except Exception:
                            try:
                                op.drop_constraint(constraint_name, 'tico_vehicles', type_='check')
                            except Exception:
                                try:
                                    op.drop_constraint(constraint_name, 'discharge_progress', type_='check')
                                except Exception:
                                    try:
                                        op.drop_constraint(constraint_name, 'berths', type_='check')
                                    except Exception:
                                        try:
                                            op.drop_constraint(constraint_name, 'berth_reservations', type_='check')
                                        except Exception:
                                            try:
                                                op.drop_constraint(constraint_name, 'ship_operations', type_='check')
                                            except Exception:
                                                try:
                                                    op.drop_constraint(constraint_name, 'port_equipment', type_='check')
                                                except Exception:
                                                    try:
                                                        op.drop_constraint(constraint_name, 'equipment_usage', type_='check')
                                                    except Exception:
                                                        try:
                                                            op.drop_constraint(constraint_name, 'performance_metrics', type_='check')
                                                        except Exception:
                                                            try:
                                                                op.drop_constraint(constraint_name, 'analytics_summary', type_='check')
                                                            except Exception:
                                                                pass