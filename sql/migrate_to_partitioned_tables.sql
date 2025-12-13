-- Migration Script: Convert Existing Tables to Partitioned Tables
-- This script migrates data from non-partitioned to partitioned tables
-- USE WITH CAUTION: Backup your database before running this script

-- ============================================================================
-- IMPORTANT: Backup Database First!
-- ============================================================================
-- pg_dump -U datauser -d dataplatform > backup_before_partitioning.sql

-- ============================================================================
-- Step 1: Create Partitioned Tables (using create_partitioned_tables.sql)
-- ============================================================================
-- Run sql/create_partitioned_tables.sql first to create partitioned table structures

-- ============================================================================
-- Step 2: Migrate pipeline_logs Data
-- ============================================================================

-- Check if old table exists and has data
DO $$
DECLARE
    row_count INTEGER;
BEGIN
    -- Check if old table exists
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'warehouse' 
        AND table_name = 'pipeline_logs'
        AND table_type = 'BASE TABLE'
    ) THEN
        -- Check if it's already partitioned
        IF NOT EXISTS (
            SELECT FROM pg_inherits 
            WHERE inhrelid = 'warehouse.pipeline_logs'::regclass
        ) THEN
            -- Get row count
            SELECT COUNT(*) INTO row_count FROM warehouse.pipeline_logs;
            
            RAISE NOTICE 'Found % rows in warehouse.pipeline_logs', row_count;
            
            -- Migrate data to partitioned table
            -- First, rename old table
            ALTER TABLE warehouse.pipeline_logs RENAME TO pipeline_logs_old;
            
            -- Create new partitioned table (if not exists from create_partitioned_tables.sql)
            -- Data will be inserted into appropriate partitions automatically
            
            -- Copy data to new partitioned table
            INSERT INTO warehouse.pipeline_logs (
                log_id, pipeline_name, status, start_time, end_time, 
                records_processed, error_message, created_at
            )
            SELECT 
                log_id, pipeline_name, status, start_time, end_time,
                records_processed, error_message, created_at
            FROM warehouse.pipeline_logs_old;
            
            RAISE NOTICE 'Migrated % rows to partitioned pipeline_logs table', row_count;
            
            -- Verify data
            IF (SELECT COUNT(*) FROM warehouse.pipeline_logs) = row_count THEN
                RAISE NOTICE 'Migration verified: All rows migrated successfully';
                -- Drop old table (uncomment when ready)
                -- DROP TABLE warehouse.pipeline_logs_old;
            ELSE
                RAISE EXCEPTION 'Migration failed: Row count mismatch';
            END IF;
        ELSE
            RAISE NOTICE 'Table warehouse.pipeline_logs is already partitioned';
        END IF;
    ELSE
        RAISE NOTICE 'Table warehouse.pipeline_logs does not exist, skipping migration';
    END IF;
END $$;

-- ============================================================================
-- Step 3: Migrate staging.raw_data
-- ============================================================================

DO $$
DECLARE
    row_count INTEGER;
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'staging' 
        AND table_name = 'raw_data'
        AND table_type = 'BASE TABLE'
    ) THEN
        IF NOT EXISTS (
            SELECT FROM pg_inherits 
            WHERE inhrelid = 'staging.raw_data'::regclass
        ) THEN
            SELECT COUNT(*) INTO row_count FROM staging.raw_data;
            RAISE NOTICE 'Found % rows in staging.raw_data', row_count;
            
            ALTER TABLE staging.raw_data RENAME TO raw_data_old;
            
            INSERT INTO staging.raw_data (id, source_name, data_content, ingested_at)
            SELECT id, source_name, data_content, ingested_at
            FROM staging.raw_data_old;
            
            RAISE NOTICE 'Migrated % rows to partitioned raw_data table', row_count;
            
            -- Verify and optionally drop old table
            -- DROP TABLE staging.raw_data_old;
        ELSE
            RAISE NOTICE 'Table staging.raw_data is already partitioned';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- Step 4: Migrate warehouse.fact_data_metrics
-- ============================================================================

DO $$
DECLARE
    row_count INTEGER;
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'warehouse' 
        AND table_name = 'fact_data_metrics'
        AND table_type = 'BASE TABLE'
    ) THEN
        IF NOT EXISTS (
            SELECT FROM pg_inherits 
            WHERE inhrelid = 'warehouse.fact_data_metrics'::regclass
        ) THEN
            SELECT COUNT(*) INTO row_count FROM warehouse.fact_data_metrics;
            RAISE NOTICE 'Found % rows in warehouse.fact_data_metrics', row_count;
            
            ALTER TABLE warehouse.fact_data_metrics RENAME TO fact_data_metrics_old;
            
            INSERT INTO warehouse.fact_data_metrics (
                metric_id, date_id, source_id, record_count, 
                processing_time_seconds, status, created_at
            )
            SELECT 
                metric_id, date_id, source_id, record_count,
                processing_time_seconds, status, created_at
            FROM warehouse.fact_data_metrics_old;
            
            RAISE NOTICE 'Migrated % rows to partitioned fact_data_metrics table', row_count;
            
            -- Verify and optionally drop old table
            -- DROP TABLE warehouse.fact_data_metrics_old;
        ELSE
            RAISE NOTICE 'Table warehouse.fact_data_metrics is already partitioned';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- Step 5: Migrate monitoring.uptime_log
-- ============================================================================

DO $$
DECLARE
    row_count INTEGER;
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'monitoring' 
        AND table_name = 'uptime_log'
        AND table_type = 'BASE TABLE'
    ) THEN
        IF NOT EXISTS (
            SELECT FROM pg_inherits 
            WHERE inhrelid = 'monitoring.uptime_log'::regclass
        ) THEN
            SELECT COUNT(*) INTO row_count FROM monitoring.uptime_log;
            RAISE NOTICE 'Found % rows in monitoring.uptime_log', row_count;
            
            ALTER TABLE monitoring.uptime_log RENAME TO uptime_log_old;
            
            INSERT INTO monitoring.uptime_log (
                id, timestamp, service_name, status, 
                response_time_ms, error_message, overall_health
            )
            SELECT 
                id, timestamp, service_name, status,
                response_time_ms, error_message, overall_health
            FROM monitoring.uptime_log_old;
            
            RAISE NOTICE 'Migrated % rows to partitioned uptime_log table', row_count;
            
            -- Verify and optionally drop old table
            -- DROP TABLE monitoring.uptime_log_old;
        ELSE
            RAISE NOTICE 'Table monitoring.uptime_log is already partitioned';
        END IF;
    END IF;
END $$;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify partitioned tables exist
SELECT 
    schemaname,
    tablename,
    CASE 
        WHEN EXISTS (
            SELECT FROM pg_inherits 
            WHERE inhrelid = (schemaname||'.'||tablename)::regclass
        ) THEN 'Partitioned'
        ELSE 'Regular'
    END as table_type
FROM pg_tables
WHERE schemaname IN ('warehouse', 'staging', 'monitoring')
AND tablename IN ('pipeline_logs', 'raw_data', 'fact_data_metrics', 'uptime_log')
ORDER BY schemaname, tablename;

-- Check partition sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname IN ('warehouse', 'staging', 'monitoring')
AND tablename LIKE '%_2025_%' OR tablename LIKE '%_2026_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. This script is idempotent - can be run multiple times safely
-- 2. Old tables are renamed (not dropped) for safety
-- 3. Uncomment DROP TABLE statements after verifying migration
-- 4. For large tables, consider migrating in batches:
--    INSERT INTO new_table SELECT * FROM old_table WHERE created_at < '2025-12-01';
--    INSERT INTO new_table SELECT * FROM old_table WHERE created_at >= '2025-12-01';

