#!/usr/bin/env python3
"""
Fleet Management System - Database Management CLI
Separate CLI script for database operations to avoid initialization issues
"""

import os
import sys
import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def create_app():
    """Create Flask app for CLI operations"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:HobokenHome3!@db.mjalobwwhnrgqqlnnbfa.supabase.co:5432/postgres')
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_timeout': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    return app

app = create_app()
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models
try:
    from models.models.user import User
    from models.models.vessel import Vessel
    from models.models.task import Task
    from models.models.sync_log import SyncLog
    from models.models.berth import Berth
    from models.maritime.ship_operation import ShipOperation
    from models.maritime.stevedore_team import StevedoreTeam
    from models.models.operation_assignment import OperationAssignment
    from models.models.equipment_assignment import EquipmentAssignment
    from models.models.work_time_log import WorkTimeLog
    from models.models.cargo_batch import CargoBatch
except ImportError as e:
    logger.warning(f"Could not import some models: {e}")

@click.group()
def cli():
    """Fleet Management Database CLI"""
    pass

@cli.command()
def init_db():
    """Initialize database with tables and sample data"""
    try:
        with app.app_context():
            logger.info("Creating database tables...")
            db.create_all()
            
            # Create sample users
            if not User.query.filter_by(email='admin@fleet.com').first():
                admin = User(
                    email='admin@fleet.com',
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    role='manager',
                    is_active=True
                )
                db.session.add(admin)
                logger.info("Created admin user")
            
            if not User.query.filter_by(email='worker@fleet.com').first():
                worker = User(
                    email='worker@fleet.com',
                    username='worker',
                    password_hash=generate_password_hash('worker123'),
                    role='worker',
                    is_active=True
                )
                db.session.add(worker)
                logger.info("Created worker user")
            
            # Create default berths
            if not Berth.query.first():
                berths = [
                    Berth(berth_number='B01', berth_name='Berth 1 - Container Terminal', berth_type='Container', 
                          length_meters=250.0, depth_meters=12.0, max_draft=11.0, max_loa=240.0, 
                          status='active', hourly_rate=50.00, daily_rate=1000.00),
                    Berth(berth_number='B02', berth_name='Berth 2 - RoRo Terminal', berth_type='RoRo', 
                          length_meters=200.0, depth_meters=8.0, max_draft=7.5, max_loa=190.0, 
                          status='active', hourly_rate=40.00, daily_rate=800.00),
                    Berth(berth_number='B03', berth_name='Berth 3 - General Cargo', berth_type='General Cargo', 
                          length_meters=180.0, depth_meters=10.0, max_draft=9.0, max_loa=170.0, 
                          status='active', hourly_rate=35.00, daily_rate=700.00),
                ]
                for berth in berths:
                    db.session.add(berth)
                logger.info("Created default berths")
            
            db.session.commit()
            logger.info("Database initialized successfully!")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

@cli.command()
def create_tables():
    """Create database tables only"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        sys.exit(1)

@cli.command()
def reset_db():
    """Reset database (drop and recreate all tables)"""
    try:
        with app.app_context():
            logger.warning("Dropping all database tables...")
            db.drop_all()
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database reset successfully!")
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()