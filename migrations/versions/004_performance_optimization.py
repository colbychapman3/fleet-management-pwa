"""Add performance optimizations and advanced indexes

Revision ID: 004
Revises: 003
Create Date: 2024-01-15 12:00:00.000000

This migration adds advanced database indexes, materialized views for analytics,
and performance optimizations for maritime operations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add performance optimizations and advanced indexes
    """
    
    # ============================================================================
    # ADVANCED INDEXES FOR QUERY PERFORMANCE
    # ============================================================================
    
    # Composite indexes for common queries
    op.create_index('ix_vessels_status_type_berth', 'vessels', ['status', 'vessel_type', 'current_berth_id'])
    op.create_index('ix_vessels_operation_progress', 'vessels', ['operation_type', 'progress', 'status'])
    op.create_index('ix_vessels_eta_port', 'vessels', ['eta', 'current_port'])
    op.create_index('ix_vessels_shipping_line_status', 'vessels', ['shipping_line', 'status'])
    
    # Task-related composite indexes
    op.create_index('ix_tasks_vessel_status_priority', 'tasks', ['vessel_id', 'status', 'priority'])
    op.create_index('ix_tasks_assigned_due_status', 'tasks', ['assigned_to_id', 'due_date', 'status'])
    op.create_index('ix_tasks_zone_type_status', 'tasks', ['zone', 'task_type', 'status'])
    op.create_index('ix_tasks_created_updated', 'tasks', ['created_at', 'updated_at'])
    
    # User performance indexes
    op.create_index('ix_users_role_department_active', 'users', ['role', 'department', 'is_active'])
    op.create_index('ix_users_vessel_role', 'users', ['vessel_id', 'role'])
    op.create_index('ix_users_shift_department', 'users', ['shift_preference', 'department'])
    
    # Maritime operations indexes
    op.create_index('ix_cargo_operations_vessel_zone_complete', 'cargo_operations', ['vessel_id', 'zone', 'quantity', 'discharged'])
    op.create_index('ix_stevedore_teams_vessel_type_lead', 'stevedore_teams', ['vessel_id', 'team_type', 'lead_id'])
    op.create_index('ix_tico_vehicles_vessel_status_type', 'tico_vehicles', ['vessel_id', 'status', 'vehicle_type'])
    op.create_index('ix_discharge_progress_vessel_zone_time', 'discharge_progress', ['vessel_id', 'zone', 'timestamp'])
    
    # Berth and operations indexes
    op.create_index('ix_berths_type_status_capacity', 'berths', ['berth_type', 'status', 'max_draft'])
    op.create_index('ix_berth_reservations_time_range', 'berth_reservations', ['reservation_start', 'reservation_end', 'reservation_type'])
    op.create_index('ix_ship_operations_vessel_status_type', 'ship_operations', ['vessel_id', 'operation_status', 'operation_type'])
    op.create_index('ix_equipment_usage_equipment_time', 'equipment_usage', ['equipment_id', 'start_time', 'end_time'])
    
    # Partial indexes for active records only (PostgreSQL specific)
    try:
        # These will only work on PostgreSQL
        op.execute("""
            CREATE INDEX CONCURRENTLY ix_vessels_active_operations 
            ON vessels (id, status, progress) 
            WHERE status IN ('in_port', 'discharging', 'loading')
        """)
        
        op.execute("""
            CREATE INDEX CONCURRENTLY ix_tasks_pending_active 
            ON tasks (vessel_id, priority, due_date) 
            WHERE status IN ('pending', 'in_progress')
        """)
        
        op.execute("""
            CREATE INDEX CONCURRENTLY ix_berth_reservations_current 
            ON berth_reservations (berth_id, reservation_start, reservation_end) 
            WHERE reservation_type = 'confirmed' AND reservation_end >= NOW()
        """)
        
        op.execute("""
            CREATE INDEX CONCURRENTLY ix_equipment_available 
            ON port_equipment (equipment_type, capacity_tons, current_location) 
            WHERE status = 'available'
        """)
    except Exception:
        # Fallback for SQLite or if concurrent index creation fails
        pass
    
    # ============================================================================
    # CREATE ANALYTICS TABLES FOR PERFORMANCE
    # ============================================================================
    
    # Analytics summary table for dashboard performance
    op.create_table('analytics_summary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_date', sa.Date(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('berth_id', sa.Integer(), nullable=True),
        sa.Column('total_vehicles_processed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_hours_worked', sa.Numeric(8, 2), server_default='0', nullable=False),
        sa.Column('average_hourly_rate', sa.Numeric(8, 2), server_default='0', nullable=False),
        sa.Column('equipment_utilization', sa.Numeric(5, 2), server_default='0', nullable=False),  # Percentage
        sa.Column('berth_utilization', sa.Numeric(5, 2), server_default='0', nullable=False),  # Percentage
        sa.Column('total_revenue', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('total_costs', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('efficiency_score', sa.Numeric(5, 2), server_default='0', nullable=False),
        sa.Column('safety_incidents', sa.Integer(), server_default='0', nullable=False),
        sa.Column('weather_delays', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_summary_date', 'analytics_summary', ['summary_date'])
    op.create_index('ix_analytics_summary_vessel_date', 'analytics_summary', ['vessel_id', 'summary_date'])
    op.create_index('ix_analytics_summary_berth_date', 'analytics_summary', ['berth_id', 'summary_date'])
    
    # Performance metrics table for KPI tracking
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_category', sa.String(50), nullable=False),  # Operational, Financial, Safety, Equipment
        sa.Column('metric_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('metric_unit', sa.String(20), nullable=True),
        sa.Column('target_value', sa.Numeric(15, 4), nullable=True),
        sa.Column('threshold_min', sa.Numeric(15, 4), nullable=True),
        sa.Column('threshold_max', sa.Numeric(15, 4), nullable=True),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('berth_id', sa.Integer(), nullable=True),
        sa.Column('equipment_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('measurement_date', sa.DateTime(), nullable=False),
        sa.Column('measurement_period', sa.String(20), nullable=True),  # daily, weekly, monthly, yearly
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['berth_id'], ['berths.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['equipment_id'], ['port_equipment.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_performance_metrics_name_date', 'performance_metrics', ['metric_name', 'measurement_date'])
    op.create_index('ix_performance_metrics_category_period', 'performance_metrics', ['metric_category', 'measurement_period'])
    op.create_index('ix_performance_metrics_vessel_date', 'performance_metrics', ['vessel_id', 'measurement_date'])
    
    # ============================================================================
    # CREATE CACHING TABLES FOR COMPLEX QUERIES
    # ============================================================================
    
    # Cached dashboard data for fast loading
    op.create_table('dashboard_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('cache_data', sa.Text(), nullable=False),  # JSON data
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )
    op.create_index('ix_dashboard_cache_key_expires', 'dashboard_cache', ['cache_key', 'expires_at'])
    op.create_index('ix_dashboard_cache_user_vessel', 'dashboard_cache', ['user_id', 'vessel_id'])
    
    # ============================================================================
    # ADD TRIGGERS FOR AUTOMATIC ANALYTICS (PostgreSQL only)
    # ============================================================================
    
    try:
        # Trigger to automatically update vessel progress
        op.execute("""
            CREATE OR REPLACE FUNCTION update_vessel_progress()
            RETURNS TRIGGER AS $$
            BEGIN
                UPDATE vessels 
                SET progress = (
                    SELECT COALESCE(
                        ROUND(
                            (SUM(discharged)::numeric / NULLIF(SUM(quantity), 0)::numeric) * 100
                        ), 0
                    )
                    FROM cargo_operations 
                    WHERE vessel_id = NEW.vessel_id
                )
                WHERE id = NEW.vessel_id;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        op.execute("""
            CREATE TRIGGER trigger_update_vessel_progress
            AFTER INSERT OR UPDATE ON cargo_operations
            FOR EACH ROW
            EXECUTE FUNCTION update_vessel_progress();
        """)
        
        # Trigger to clean expired cache entries
        op.execute("""
            CREATE OR REPLACE FUNCTION clean_expired_cache()
            RETURNS TRIGGER AS $$
            BEGIN
                DELETE FROM dashboard_cache WHERE expires_at < NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        op.execute("""
            CREATE TRIGGER trigger_clean_expired_cache
            AFTER INSERT ON dashboard_cache
            FOR EACH ROW
            EXECUTE FUNCTION clean_expired_cache();
        """)
        
    except Exception:
        # Skip triggers for non-PostgreSQL databases
        pass
    
    # ============================================================================
    # ADD PERFORMANCE-RELATED COLUMNS
    # ============================================================================
    
    # Add performance tracking to existing tables
    op.add_column('vessels', sa.Column('last_performance_update', sa.DateTime(), nullable=True))
    op.add_column('vessels', sa.Column('average_turnaround_hours', sa.Numeric(8, 2), nullable=True))
    op.add_column('vessels', sa.Column('total_port_calls', sa.Integer(), server_default='0', nullable=False))
    op.add_column('vessels', sa.Column('reliability_score', sa.Numeric(5, 2), nullable=True))
    
    op.add_column('users', sa.Column('productivity_score', sa.Numeric(5, 2), nullable=True))
    op.add_column('users', sa.Column('safety_record_score', sa.Numeric(5, 2), nullable=True))
    op.add_column('users', sa.Column('hours_worked_this_month', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('last_performance_review', sa.Date(), nullable=True))
    
    # ============================================================================
    # CREATE STORED PROCEDURES FOR COMMON OPERATIONS (PostgreSQL)
    # ============================================================================
    
    try:
        # Function to calculate vessel efficiency
        op.execute("""
            CREATE OR REPLACE FUNCTION calculate_vessel_efficiency(vessel_id_param INTEGER)
            RETURNS NUMERIC AS $$
            DECLARE
                efficiency_score NUMERIC;
            BEGIN
                SELECT 
                    COALESCE(
                        AVG(
                            CASE 
                                WHEN hourly_rate > 0 THEN 
                                    LEAST(100, (hourly_rate / 150.0) * 100)
                                ELSE 0 
                            END
                        ), 0
                    ) INTO efficiency_score
                FROM discharge_progress 
                WHERE vessel_id = vessel_id_param 
                AND timestamp >= NOW() - INTERVAL '24 hours';
                
                RETURN COALESCE(efficiency_score, 0);
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Function to get berth utilization
        op.execute("""
            CREATE OR REPLACE FUNCTION get_berth_utilization(berth_id_param INTEGER, days_back INTEGER DEFAULT 7)
            RETURNS NUMERIC AS $$
            DECLARE
                utilization_pct NUMERIC;
                total_hours NUMERIC;
                occupied_hours NUMERIC;
            BEGIN
                total_hours := days_back * 24;
                
                SELECT 
                    COALESCE(
                        SUM(
                            EXTRACT(EPOCH FROM (
                                LEAST(reservation_end, NOW()) - 
                                GREATEST(reservation_start, NOW() - INTERVAL '1 day' * days_back)
                            )) / 3600
                        ), 0
                    ) INTO occupied_hours
                FROM berth_reservations 
                WHERE berth_id = berth_id_param 
                AND reservation_start <= NOW()
                AND reservation_end >= NOW() - INTERVAL '1 day' * days_back
                AND reservation_type = 'confirmed';
                
                utilization_pct := (occupied_hours / total_hours) * 100;
                
                RETURN LEAST(100, COALESCE(utilization_pct, 0));
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Function to optimize equipment assignment
        op.execute("""
            CREATE OR REPLACE FUNCTION suggest_equipment_assignment(
                operation_type_param VARCHAR(50),
                required_capacity_param NUMERIC
            )
            RETURNS TABLE(
                equipment_id INTEGER,
                equipment_code VARCHAR(50),
                equipment_type VARCHAR(50),
                capacity_tons NUMERIC,
                utilization_score NUMERIC
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    pe.id,
                    pe.equipment_code,
                    pe.equipment_type,
                    pe.capacity_tons,
                    COALESCE(
                        100 - (
                            COUNT(eu.id) * 10 + 
                            AVG(EXTRACT(EPOCH FROM (eu.end_time - eu.start_time)) / 3600) * 2
                        ), 100
                    ) as utilization_score
                FROM port_equipment pe
                LEFT JOIN equipment_usage eu ON pe.id = eu.equipment_id 
                    AND eu.start_time >= NOW() - INTERVAL '24 hours'
                WHERE pe.status = 'available'
                AND pe.capacity_tons >= required_capacity_param
                GROUP BY pe.id, pe.equipment_code, pe.equipment_type, pe.capacity_tons
                ORDER BY utilization_score DESC, pe.capacity_tons ASC
                LIMIT 5;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
    except Exception:
        # Skip stored procedures for non-PostgreSQL databases
        pass


def downgrade():
    """
    Remove performance optimizations and advanced indexes
    """
    
    # Drop stored procedures (PostgreSQL)
    try:
        op.execute("DROP FUNCTION IF EXISTS suggest_equipment_assignment(VARCHAR(50), NUMERIC)")
        op.execute("DROP FUNCTION IF EXISTS get_berth_utilization(INTEGER, INTEGER)")
        op.execute("DROP FUNCTION IF EXISTS calculate_vessel_efficiency(INTEGER)")
        op.execute("DROP TRIGGER IF EXISTS trigger_clean_expired_cache ON dashboard_cache")
        op.execute("DROP TRIGGER IF EXISTS trigger_update_vessel_progress ON cargo_operations")
        op.execute("DROP FUNCTION IF EXISTS clean_expired_cache()")
        op.execute("DROP FUNCTION IF EXISTS update_vessel_progress()")
    except Exception:
        pass
    
    # Remove performance columns
    op.drop_column('users', 'last_performance_review')
    op.drop_column('users', 'hours_worked_this_month')
    op.drop_column('users', 'safety_record_score')
    op.drop_column('users', 'productivity_score')
    
    op.drop_column('vessels', 'reliability_score')
    op.drop_column('vessels', 'total_port_calls')
    op.drop_column('vessels', 'average_turnaround_hours')
    op.drop_column('vessels', 'last_performance_update')
    
    # Drop caching tables
    op.drop_index('ix_dashboard_cache_user_vessel', table_name='dashboard_cache')
    op.drop_index('ix_dashboard_cache_key_expires', table_name='dashboard_cache')
    op.drop_table('dashboard_cache')
    
    # Drop analytics tables
    op.drop_index('ix_performance_metrics_vessel_date', table_name='performance_metrics')
    op.drop_index('ix_performance_metrics_category_period', table_name='performance_metrics')
    op.drop_index('ix_performance_metrics_name_date', table_name='performance_metrics')
    op.drop_table('performance_metrics')
    
    op.drop_index('ix_analytics_summary_berth_date', table_name='analytics_summary')
    op.drop_index('ix_analytics_summary_vessel_date', table_name='analytics_summary')
    op.drop_index('ix_analytics_summary_date', table_name='analytics_summary')
    op.drop_table('analytics_summary')
    
    # Drop partial indexes (PostgreSQL)
    try:
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_equipment_available")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_berth_reservations_current")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_tasks_pending_active")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_vessels_active_operations")
    except Exception:
        pass
    
    # Drop composite indexes
    op.drop_index('ix_equipment_usage_equipment_time', table_name='equipment_usage')
    op.drop_index('ix_ship_operations_vessel_status_type', table_name='ship_operations')
    op.drop_index('ix_berth_reservations_time_range', table_name='berth_reservations')
    op.drop_index('ix_berths_type_status_capacity', table_name='berths')
    
    op.drop_index('ix_discharge_progress_vessel_zone_time', table_name='discharge_progress')
    op.drop_index('ix_tico_vehicles_vessel_status_type', table_name='tico_vehicles')
    op.drop_index('ix_stevedore_teams_vessel_type_lead', table_name='stevedore_teams')
    op.drop_index('ix_cargo_operations_vessel_zone_complete', table_name='cargo_operations')
    
    op.drop_index('ix_users_shift_department', table_name='users')
    op.drop_index('ix_users_vessel_role', table_name='users')
    op.drop_index('ix_users_role_department_active', table_name='users')
    
    op.drop_index('ix_tasks_created_updated', table_name='tasks')
    op.drop_index('ix_tasks_zone_type_status', table_name='tasks')
    op.drop_index('ix_tasks_assigned_due_status', table_name='tasks')
    op.drop_index('ix_tasks_vessel_status_priority', table_name='tasks')
    
    op.drop_index('ix_vessels_shipping_line_status', table_name='vessels')
    op.drop_index('ix_vessels_eta_port', table_name='vessels')
    op.drop_index('ix_vessels_operation_progress', table_name='vessels')
    op.drop_index('ix_vessels_status_type_berth', table_name='vessels')