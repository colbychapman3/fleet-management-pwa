# Maritime Database Migration Guide

This comprehensive guide covers the migration strategy for transforming the Fleet Management PWA into a Maritime Stevedoring System while maintaining backward compatibility and data integrity.

## Table of Contents

1. [Overview](#overview)
2. [Migration Strategy](#migration-strategy)
3. [Prerequisites](#prerequisites)
4. [Migration Files](#migration-files)
5. [Database Compatibility](#database-compatibility)
6. [Deployment Instructions](#deployment-instructions)
7. [Testing and Verification](#testing-and-verification)
8. [Rollback Procedures](#rollback-procedures)
9. [Data Validation](#data-validation)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting](#troubleshooting)

## Overview

The maritime migration transforms the existing fleet management system into a comprehensive stevedoring operations platform. The migration is designed to:

- Preserve all existing user data, vessel information, and task records
- Add maritime-specific functionality for cargo operations, berth management, and stevedore teams
- Enhance performance with optimized indexes and caching
- Implement comprehensive data validation and business rule constraints
- Support both PostgreSQL and SQLite databases

## Migration Strategy

### Phased Approach

The migration follows a phased approach to minimize risk and ensure system stability:

**Phase 1: Foundation Enhancement (Migration 002)**
- Extend existing tables with maritime fields
- Add default values for backward compatibility
- Create core maritime tables

**Phase 2: Infrastructure Addition (Migration 003)**
- Add berth management and port infrastructure
- Create equipment tracking and usage monitoring
- Implement operational workflow management

**Phase 3: Performance Optimization (Migration 004)**
- Add advanced indexes for query performance
- Create analytics and caching tables
- Implement stored procedures (PostgreSQL only)

**Phase 4: Data Validation (Migration 005)**
- Add comprehensive check constraints
- Implement business rule validation
- Create data integrity triggers

## Prerequisites

### Software Requirements

- Python 3.8+
- Flask-Migrate (Alembic)
- PostgreSQL 12+ OR SQLite 3.25+
- Git (for version control)

### Environment Setup

```bash
# Install required packages
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development  # or production
export DATABASE_URL=your_database_url
```

### Database Access

Ensure you have:
- Database administrator privileges
- Backup capabilities
- Sufficient disk space (estimate 2x current database size)
- Network connectivity for remote databases

## Migration Files

### Migration 001: Initial Migration
**File:** `migrations/versions/001_initial_migration.py`
**Purpose:** Creates the base schema with users, vessels, tasks, and sync_logs tables.

### Migration 002: Maritime Enhancement
**File:** `migrations/versions/002_maritime_enhancement.py`
**Purpose:** Transforms the fleet management system into maritime stevedoring platform.

**Key Changes:**
- Extends `vessels` table with maritime operations fields
- Adds cargo tracking, team management, and operational parameters
- Creates new tables: `cargo_operations`, `stevedore_teams`, `tico_vehicles`, `maritime_documents`, `discharge_progress`
- Updates user roles and task types for maritime context

### Migration 003: Berth Management
**File:** `migrations/versions/003_berth_management.py`
**Purpose:** Adds comprehensive berth and port infrastructure management.

**Key Features:**
- Berth definitions and capacity management
- Reservation and scheduling system
- Ship operations tracking
- Port equipment management and usage tracking
- Default berth and equipment data

### Migration 004: Performance Optimization
**File:** `migrations/versions/004_performance_optimization.py`
**Purpose:** Optimizes database performance for maritime operations.

**Optimizations:**
- Advanced composite indexes for common queries
- Analytics summary tables for dashboard performance
- Performance metrics tracking
- Caching mechanisms
- PostgreSQL-specific optimizations (stored procedures, triggers)

### Migration 005: Data Validation Constraints
**File:** `migrations/versions/005_data_validation_constraints.py`
**Purpose:** Ensures data integrity with comprehensive validation rules.

**Validation Features:**
- Check constraints for data ranges and formats
- Business rule validation
- Foreign key integrity enforcement
- Email format validation
- Operational parameter constraints

## Database Compatibility

### PostgreSQL Support

The migrations are optimized for PostgreSQL with advanced features:
- Stored procedures for complex calculations
- Triggers for automatic data updates
- Partial indexes for performance
- JSON data types for flexible storage
- Concurrent index creation

### SQLite Support

SQLite compatibility is maintained with:
- Simplified constraint handling
- Alternative indexing strategies
- JSON storage as TEXT
- Compatible data types
- Graceful feature degradation

### Compatibility Matrix

| Feature | PostgreSQL | SQLite | Notes |
|---------|------------|--------|-------|
| Basic Tables | ✅ | ✅ | Full compatibility |
| Foreign Keys | ✅ | ✅ | Enabled with PRAGMA |
| Check Constraints | ✅ | ✅ | Full support |
| Indexes | ✅ | ✅ | Optimized for each |
| Stored Procedures | ✅ | ❌ | PostgreSQL only |
| Triggers | ✅ | ✅ | Limited in SQLite |
| JSON Support | ✅ | ✅ | Native vs TEXT |
| Partial Indexes | ✅ | ❌ | PostgreSQL only |

## Deployment Instructions

### 1. Pre-Migration Preparation

```bash
# Create database backup
pg_dump your_database > backup_$(date +%Y%m%d_%H%M%S).sql

# Or for SQLite
cp your_database.db backup_$(date +%Y%m%d_%H%M%S).db

# Check current migration status
flask db current

# Verify no pending changes
flask db check
```

### 2. Run Migrations

```bash
# Initialize migration repository (if not exists)
flask db init

# Apply migrations in sequence
flask db upgrade

# Verify migration completion
flask db current
flask db show
```

### 3. Data Validation

```bash
# Run migration tests
python scripts/test_migrations.py

# Verify rollback functionality
python scripts/verify_rollback.py

# Check data integrity
python scripts/validate_data.py
```

### 4. Post-Migration Verification

```bash
# Test application functionality
python -m pytest tests/

# Verify API endpoints
curl -X GET http://localhost:5000/api/vessels
curl -X GET http://localhost:5000/api/berths

# Check database performance
python scripts/performance_check.py
```

## Testing and Verification

### Automated Testing

The migration package includes comprehensive testing tools:

**Migration Tests (`scripts/test_migrations.py`)**
- Tests each migration individually
- Verifies data integrity
- Checks both PostgreSQL and SQLite compatibility
- Validates foreign key relationships

**Rollback Verification (`scripts/verify_rollback.py`)**
- Tests rollback functionality
- Verifies data preservation
- Checks constraint integrity
- Validates foreign key handling

### Manual Testing Checklist

- [ ] All existing users can log in
- [ ] Existing vessels display correctly
- [ ] Task assignments work properly
- [ ] New maritime features are accessible
- [ ] Berth management functions
- [ ] Cargo operations can be created
- [ ] Performance is acceptable
- [ ] Data validation works correctly

### Performance Testing

```bash
# Run performance benchmarks
python scripts/performance_benchmark.py

# Monitor query performance
EXPLAIN ANALYZE SELECT * FROM vessels WHERE status = 'active';

# Check index usage
SELECT * FROM pg_stat_user_indexes;  # PostgreSQL
PRAGMA index_info(index_name);       # SQLite
```

## Rollback Procedures

### Automatic Rollback

```bash
# Rollback to specific migration
flask db downgrade 001

# Rollback one migration
flask db downgrade -1

# Verify rollback success
flask db current
```

### Manual Rollback

If automatic rollback fails:

1. **Stop the application**
2. **Restore from backup**
3. **Verify data integrity**
4. **Restart application**

```bash
# Restore PostgreSQL backup
psql your_database < backup_file.sql

# Restore SQLite backup
cp backup_file.db your_database.db

# Verify restoration
python scripts/verify_rollback.py
```

### Emergency Procedures

In case of critical issues:

1. **Immediate Actions:**
   - Stop application traffic
   - Switch to maintenance mode
   - Assess the situation

2. **Recovery Steps:**
   - Identify the issue source
   - Determine rollback necessity
   - Execute recovery plan
   - Validate system integrity

3. **Communication:**
   - Notify stakeholders
   - Document the incident
   - Plan prevention measures

## Data Validation

### Constraint Validation

The migration implements comprehensive data validation:

**Vessel Constraints:**
- Dimensions must be positive
- Progress percentage (0-100)
- Valid operation types
- Positive vehicle counts

**User Constraints:**
- Valid email format
- Authorized roles only
- Performance scores (0-5)
- Positive work hours

**Operational Constraints:**
- Logical time relationships
- Positive quantities and rates
- Valid zone assignments
- Equipment capacity limits

### Business Rule Validation

**Berth Availability:**
- No overlapping reservations
- Vessel size compatibility
- Berth capacity limits

**Cargo Operations:**
- Discharged ≤ Total quantity
- Zone consistency
- Valid vehicle types

**Equipment Usage:**
- Logical time sequences
- Operator assignments
- Maintenance schedules

## Performance Considerations

### Index Strategy

The migration implements a comprehensive indexing strategy:

**Primary Indexes:**
- Single-column indexes on foreign keys
- Unique indexes on natural keys
- Status and type columns

**Composite Indexes:**
- Common query patterns
- Multi-column searches
- Optimized join operations

**Specialized Indexes:**
- Partial indexes for active records (PostgreSQL)
- Text search indexes
- Date range queries

### Query Optimization

**Optimized Queries:**
- Use prepared statements
- Leverage index hints
- Implement pagination
- Cache frequent queries

**Monitoring:**
- Query execution plans
- Index usage statistics
- Performance metrics tracking
- Slow query identification

### Caching Strategy

**Application-Level Caching:**
- Dashboard data caching
- User session caching
- Configuration caching

**Database-Level Caching:**
- Query result caching
- Materialized views
- Computed columns

## Troubleshooting

### Common Issues

**Migration Failures:**

*Issue:* Migration fails with constraint violations
*Solution:* Check data compatibility, clean invalid data, retry migration

*Issue:* Foreign key constraint errors
*Solution:* Verify referential integrity, fix orphaned records

*Issue:* Timeout during migration
*Solution:* Increase timeout limits, run in smaller batches

**Performance Issues:**

*Issue:* Slow query performance
*Solution:* Check index usage, update statistics, optimize queries

*Issue:* High memory usage
*Solution:* Reduce batch sizes, implement pagination, clear caches

*Issue:* Lock contention
*Solution:* Schedule migrations during low usage, use shorter transactions

### Diagnostic Commands

```bash
# Check migration status
flask db current
flask db history

# Verify database structure
\d+ table_name  # PostgreSQL
.schema table_name  # SQLite

# Check constraints
SELECT * FROM information_schema.check_constraints;  # PostgreSQL
PRAGMA foreign_key_check;  # SQLite

# Monitor performance
SELECT * FROM pg_stat_activity;  # PostgreSQL
PRAGMA optimize;  # SQLite
```

### Support Resources

**Documentation:**
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

**Community Support:**
- Stack Overflow tags: flask-migrate, alembic, postgresql, sqlite
- Flask community forums
- Database-specific communities

**Professional Support:**
- Database administrator consultation
- Migration specialist services
- Performance tuning experts

---

## Migration Checklist

### Pre-Migration
- [ ] Database backup completed
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Migration tests passed
- [ ] Stakeholders notified

### During Migration
- [ ] Application stopped
- [ ] Migration executed successfully
- [ ] No error messages
- [ ] Data validation passed
- [ ] Performance acceptable

### Post-Migration
- [ ] Application restarted
- [ ] Functionality verified
- [ ] Performance monitored
- [ ] Users notified
- [ ] Documentation updated

### Emergency Rollback
- [ ] Issue identified
- [ ] Rollback executed
- [ ] Data integrity verified
- [ ] Application restored
- [ ] Incident documented

---

*For additional support or questions, contact the development team or refer to the project documentation.*