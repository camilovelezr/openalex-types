# OpenAlex Database Recovery & Monitoring System 0.2.0

## Overview

This repository contains a comprehensive solution for recovering from the OpenAlex database corruption incident and implementing a robust monitoring system to prevent future issues.

### What Happened

The `openalex.works` table suffered severe corruption due to a forcefully terminated data ingestion process. The corruption manifested at three levels:
1. **Logical corruption**: Duplicate primary keys
2. **Index corruption**: Broken index structures  
3. **Physical corruption**: TOAST errors indicating scrambled on-disk pointers

**The table was deemed unrecoverable** and required a complete rebuild.

### Solution Components

1. **Database Recovery Script** (`database_recovery_with_indexes.sql`)
2. **Index Monitoring System** (`index_monitoring.py`)  
3. **Automated Setup Script** (`setup_monitoring.sh`)
4. **Comprehensive Documentation** (this README)

---

## Quick Start

### 1. Database Recovery

```bash
# First, drop the corrupted table and rename the clean template
psql -d openalex -c "DROP TABLE openalex.works;"
psql -d openalex -c "ALTER TABLE openalex.works_clean RENAME TO works;"

# Then run the recovery script to add all constraints and indexes
psql -d openalex -f database_recovery_with_indexes.sql

# Finally, restart your data ingestion
python scripts/upload_1.py
```

### 2. Monitoring Setup

```bash
# Full automated setup
./setup_monitoring.sh --full-setup

# Or step by step
./setup_monitoring.sh --install-deps
./setup_monitoring.sh --create-config
./setup_monitoring.sh --test-connection
./setup_monitoring.sh --setup-cron
```

---

## Detailed Instructions

### Database Recovery Process

#### Prerequisites
- PostgreSQL database with `openalex` schema
- A clean `openalex.works_clean` table template
- Administrative access to the database

#### Step 1: Emergency Recovery
```sql
-- Connect to your database
psql -d openalex

-- Drop the corrupted table
DROP TABLE openalex.works;

-- Rename the clean template
ALTER TABLE openalex.works_clean RENAME TO works;
```

#### Step 2: Apply Constraints and Indexes
```bash
# Run the comprehensive recovery script
psql -d openalex -f database_recovery_with_indexes.sql
```

This script will:
- ✅ Add all primary key constraints
- ✅ Create strategic indexes on high-priority columns
- ✅ Add foreign key constraints for referential integrity
- ✅ Create composite indexes for common query patterns
- ✅ Update table statistics for query optimization

#### Step 3: Restart Data Ingestion
```bash
# Resume data loading from OpenAlex snapshot files
python scripts/upload_1.py
```

### Index Strategy Details

#### Primary Key Constraints
All tables now have proper primary key constraints:
- `authors(id)`
- `works(id)` 
- `concepts(id)`
- `institutions(id)`
- `sources(id)`
- `publishers(id)`
- `topics(id)`
- Plus all subsidiary tables

#### Strategic Indexes Created

**Frequently Queried Identifiers:**
- `works.doi`
- `authors.orcid`
- `institutions.ror`
- `sources.issn_l`

**Date/Time Columns:**
- `works.publication_year`
- `works.publication_date`
- `*_counts_by_year.year` (all tables)

**Count Columns (for popularity/impact sorting):**
- `*.works_count` (all main entity tables)
- `*.cited_by_count` (all main entity tables)

**Boolean Flags:**
- `works.is_retracted`
- `works.is_paratext`
- `sources.is_oa`
- `works_open_access.is_oa`

**Foreign Key Relationships:**
- All relationship tables have indexes on foreign key columns
- Optimized for JOIN performance

#### Columns Excluded from Indexing
- Large text fields (title, display_name, description)
- URL fields (rarely queried directly)
- JSON columns (need specialized indexes if queried)
- Low-cardinality columns (unless frequently filtered)

---

## Monitoring System

### Features

The monitoring system provides:
- **Index Usage Statistics**: Track which indexes are being used
- **Unused Index Detection**: Identify indexes that can be removed
- **Query Performance Analysis**: Find slow queries needing optimization
- **Table Scan Analysis**: Detect missing indexes
- **Automated Alerts**: Email notifications for issues
- **Trend Analysis**: Historical performance tracking
- **Maintenance Recommendations**: Automated optimization suggestions

### Installation

#### Manual Setup
```bash
# Install Python dependencies
pip3 install psycopg2-binary pandas tabulate

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=openalex
export DB_USER=postgres
export DB_PASSWORD=your_password

# Run monitoring
python3 index_monitoring.py
```

#### Automated Setup
```bash
# Complete setup with interactive configuration
./setup_monitoring.sh --full-setup

# Individual steps
./setup_monitoring.sh --install-deps
./setup_monitoring.sh --create-config
./setup_monitoring.sh --test-connection
./setup_monitoring.sh --setup-cron
```

### Usage Examples

```bash
# Daily monitoring summary
python3 index_monitoring.py

# Generate daily report
python3 index_monitoring.py --report-type daily

# Generate weekly comprehensive report
python3 index_monitoring.py --report-type weekly

# Check for unused indexes
python3 index_monitoring.py --check-unused

# Check for index bloat
python3 index_monitoring.py --check-bloat

# Check alert thresholds
python3 index_monitoring.py --alert-thresholds

# Export data to CSV
python3 index_monitoring.py --export-csv

# Use custom configuration
python3 index_monitoring.py --config-file custom_config.json
```

### Automated Monitoring Schedule

When you run `--setup-cron`, the following schedule is created:

| Task | Frequency | Time |
|------|-----------|------|
| Daily Reports | Daily | 8:00 AM |
| Weekly Reports | Weekly (Monday) | 6:00 AM |
| Alert Threshold Checks | Every 4 hours | On the hour |
| CSV Data Export | Weekly (Sunday) | 11:00 PM |

### Alert Thresholds

The system monitors these metrics:

| Metric | Default Threshold | Description |
|--------|------------------|-------------|
| Unused Indexes | 30 days | Indexes with no reads/fetches |
| Low Hit Ratio | 90% | Index hit ratio below threshold |
| High Sequential Scans | 50% | Tables with high seq scan ratio |
| Index Bloat | 20% | Estimated bloat percentage |
| Slow Queries | 1000ms | Mean query execution time |

### Configuration

Create `monitoring_config.json`:
```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "database": "openalex",
        "user": "postgres",
        "password": "your_password"
    },
    "alert_thresholds": {
        "unused_days": 30,
        "low_hit_ratio": 90.0,
        "high_seq_scan_ratio": 50.0,
        "bloat_ratio": 20.0,
        "slow_query_time": 1000.0
    },
    "email": {
        "enabled": true,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your_email@gmail.com",
        "password": "your_app_password",
        "from_email": "your_email@gmail.com",
        "to_emails": ["admin@yourcompany.com"]
    }
}
```

---

## Prevention & Best Practices

### 1. Graceful Script Termination

**Always implement signal handlers in data ingestion scripts:**

```python
import signal
import sys

def signal_handler(sig, frame):
    print('Gracefully shutting down...')
    # Close database connections
    # Commit or rollback current transaction
    # Clean up resources
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### 2. Regular Backups

Set up automated PostgreSQL backups:

```bash
# Daily full backup
pg_dump -h localhost -U postgres -d openalex | gzip > openalex_backup_$(date +%Y%m%d).sql.gz

# Continuous archiving (recommended for production)
# Configure postgresql.conf:
# archive_mode = on
# archive_command = 'cp %p /backup/archive/%f'
```

### 3. Connection Pooling

Use connection pooling to prevent connection exhaustion:

```python
from psycopg2 import pool

# Create connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min and max connections
    host='localhost',
    database='openalex',
    user='postgres',
    password='password'
)
```

### 4. Transaction Management

Use proper transaction boundaries:

```python
try:
    conn.autocommit = False
    cursor = conn.cursor()
    
    # Perform multiple operations
    cursor.execute("INSERT ...")
    cursor.execute("UPDATE ...")
    
    # Commit only if all operations succeed
    conn.commit()
    
except Exception as e:
    # Rollback on any error
    conn.rollback()
    raise e
finally:
    cursor.close()
```

### 5. Index Maintenance

Regular maintenance schedule:

```sql
-- Weekly index maintenance
REINDEX DATABASE openalex;

-- Update table statistics
ANALYZE;

-- Check for bloated indexes
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'openalex';
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused
```
psycopg2.OperationalError: could not connect to server
```
**Solution:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify connection parameters in config
- Check firewall settings

#### 2. Permission Denied
```
psycopg2.OperationalError: FATAL: permission denied for database
```
**Solution:**
- Verify user has correct permissions
- Grant necessary privileges: `GRANT ALL PRIVILEGES ON DATABASE openalex TO your_user;`

#### 3. Missing Dependencies
```
ModuleNotFoundError: No module named 'psycopg2'
```
**Solution:**
```bash
pip3 install psycopg2-binary pandas tabulate
```

#### 4. Cron Jobs Not Running
**Check cron service:**
```bash
sudo systemctl status cron
crontab -l  # List current cron jobs
```

**Check logs:**
```bash
tail -f /var/log/openalex_monitoring.log
```

#### 5. Index Creation Failures
If `CREATE INDEX CONCURRENTLY` fails:
```sql
-- Check for invalid indexes
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'openalex' 
AND indexdef IS NULL;

-- Drop and recreate failed indexes
DROP INDEX CONCURRENTLY IF EXISTS problematic_index;
CREATE INDEX CONCURRENTLY problematic_index ON table_name(column_name);
```

### Recovery Scenarios

#### Scenario 1: Monitoring Script Crashes
```bash
# Check the log file
tail -f index_monitoring.log

# Test database connection
python3 index_monitoring.py --alert-thresholds

# Reset database statistics if needed
SELECT pg_stat_reset();
```

#### Scenario 2: High Index Bloat
```sql
-- Identify bloated indexes
SELECT schemaname, tablename, indexname, 
       pg_size_pretty(pg_relation_size(indexrelname::regclass)) as size
FROM pg_stat_user_indexes 
WHERE schemaname = 'openalex'
ORDER BY pg_relation_size(indexrelname::regclass) DESC;

-- Rebuild specific index
REINDEX INDEX CONCURRENTLY index_name;
```

#### Scenario 3: Slow Query Performance
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1 second
SELECT pg_reload_conf();

-- Check pg_stat_statements
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
WHERE query LIKE '%openalex%'
ORDER BY mean_time DESC;
```

---

## File Structure

```
openalex-types/
├── database_recovery_with_indexes.sql  # Main recovery script
├── index_monitoring.py                 # Monitoring system
├── setup_monitoring.sh                 # Automated setup
├── README.md                          # This documentation
├── error_report.md                    # Original incident report
├── openalex-pg-schema.sql            # Original schema
├── monitoring_reports/               # Generated reports (created automatically)
├── scripts/
│   ├── upload_1.py                   # Data ingestion script
│   └── build_indexes.sh             # Index building script
└── src/
    └── openalex_types/              # Python type definitions
```

---

## Maintenance Schedule

### Daily
- Monitor alert notifications
- Review daily monitoring reports
- Check system logs for errors

### Weekly  
- Review weekly comprehensive reports
- Analyze index usage trends
- Check for unused indexes
- Review CSV exports

### Monthly
- Full index maintenance (`REINDEX`)
- Update table statistics (`ANALYZE`)
- Review and optimize alert thresholds
- Database backup verification

### Quarterly
- Schema review and optimization
- Query performance analysis
- Capacity planning review
- Documentation updates

---

## Support & Contributing

### Getting Help

1. **Check the logs:** `tail -f index_monitoring.log`
2. **Test connectivity:** `./setup_monitoring.sh --test-connection`
3. **Review configuration:** Verify `monitoring_config.json`
4. **Check PostgreSQL logs:** `/var/log/postgresql/postgresql-*.log`

### Reporting Issues

When reporting issues, please include:
- Error messages and stack traces
- Configuration file (with passwords redacted)
- Database version and system information
- Steps to reproduce the issue

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

---

## License & Acknowledgments

This monitoring system was developed in response to the OpenAlex database corruption incident. It incorporates PostgreSQL best practices and monitoring techniques from the database administration community.

Special thanks to the PostgreSQL community for their extensive documentation and tools that made this recovery possible.

---

## Appendix

### Useful PostgreSQL Queries

#### Check Database Size
```sql
SELECT pg_size_pretty(pg_database_size('openalex'));
```

#### Check Table Sizes
```sql
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'openalex'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Check Index Usage
```sql
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'openalex'
ORDER BY idx_tup_read + idx_tup_fetch DESC;
```

#### Check Connection Status
```sql
SELECT datname, usename, application_name, client_addr, state, query_start
FROM pg_stat_activity 
WHERE datname = 'openalex';
```

### Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `DB_NAME` | Database name | openalex |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | (empty) |
| `SMTP_SERVER` | Email server | (empty) |
| `SMTP_PORT` | Email server port | 587 |
| `SMTP_USER` | Email username | (empty) |
| `SMTP_PASS` | Email password | (empty) |
| `FROM_EMAIL` | From email address | (empty) |
| `TO_EMAILS` | Comma-separated recipient list | (empty) |

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-07  
**Status:** Production Ready
