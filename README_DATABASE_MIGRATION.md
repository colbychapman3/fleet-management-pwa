# Database Migration Guide: Fixing Duplicate Index Issue

## Issue Summary
The `stevedore_teams` table had duplicate indexes on the `status` column:
- `ix_stevedore_teams_status` (auto-created by Flask-SQLAlchemy)
- `idx_stevedore_teams_status` (manually defined in model)

This caused performance degradation and wasted storage space.

## Solution Applied
**Migration 009** removes the duplicate custom index `idx_stevedore_teams_status` while keeping the Flask-SQLAlchemy auto-generated `ix_stevedore_teams_status`.

### Why Keep `ix_stevedore_teams_status`?
- Flask-SQLAlchemy automatically creates this index from `status = db.Column(..., index=True)`
- Follows Flask-SQLAlchemy naming conventions
- Automatically maintained by the ORM

### Why Remove `idx_stevedore_teams_status`?
- Custom index defined in `__table_args__` 
- Redundant with the auto-generated index
- Causes unnecessary overhead

## Production Deployment Instructions

### Prerequisites
1. **Create a database backup** before applying any migration
2. Ensure you have database admin privileges
3. Test the migration in a staging environment first

### Step-by-Step Deployment

#### 1. Backup Database
```bash
# PostgreSQL backup
pg_dump -h your_host -U your_user -d your_database > backup_before_migration_009.sql

# Or using environment variables
pg_dump $DATABASE_URL > backup_before_migration_009.sql
```

#### 2. Apply Migration in Staging
```bash
# Navigate to project directory
cd /path/to/fleet-management-pwa

# Apply the migration
alembic upgrade head

# Verify the migration was applied
alembic current
```

#### 3. Verify Index Removal
Connect to your database and verify only one index exists:
```sql
-- Check indexes on stevedore_teams table
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'stevedore_teams' 
AND indexname LIKE '%status%';

-- Expected result: Only 'ix_stevedore_teams_status' should exist
```

#### 4. Monitor Performance
After deployment, monitor:
- Query performance on status column lookups
- Database storage usage
- Application response times for stevedore team queries

#### 5. Production Deployment
```bash
# In production environment
cd /path/to/fleet-management-pwa

# Apply migration with monitoring
alembic upgrade head

# Verify migration
alembic current

# Check application health
# Test key stevedore team operations
```

### Rollback Plan
If issues occur, you can rollback:
```bash
# Rollback to previous migration
alembic downgrade 008

# This will recreate the duplicate index (not recommended long-term)
```

### Performance Impact
- **Positive**: Reduced storage usage, faster writes, eliminated index maintenance overhead
- **Neutral**: Query performance remains the same (one index still exists)
- **Risk**: Very low - the remaining index provides the same query optimization

### Monitoring Queries
Use these queries to monitor the fix:

```sql
-- Check current indexes
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes 
WHERE tablename = 'stevedore_teams'
ORDER BY indexname;

-- Monitor query performance
EXPLAIN ANALYZE SELECT * FROM stevedore_teams WHERE status = 'available';

-- Check index usage statistics
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'stevedore_teams';
```

## Files Modified
1. **New Migration**: `migrations/versions/009_remove_duplicate_stevedore_teams_status_index.py`
2. **Model Update**: `models/maritime/stevedore_team.py` (removed duplicate index from `__table_args__`)
3. **Documentation**: This README file

## Contact
If you encounter any issues during deployment, ensure you have the database backup ready and can rollback if necessary. The migration is designed to be safe and non-destructive.
