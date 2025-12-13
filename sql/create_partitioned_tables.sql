-- Table Partitioning for Scalability (100 GB/day support)
-- This script creates partitioned versions of high-volume tables
-- Partitioning improves query performance and enables partition pruning

-- ============================================================================
-- 1. Pipeline Logs Table (Partitioned by created_at)
-- ============================================================================
-- This table stores all pipeline execution logs and can grow very large

-- Drop existing table if it exists (use with caution in production)
-- DROP TABLE IF EXISTS warehouse.pipeline_logs CASCADE;

-- Create partitioned table
CREATE TABLE IF NOT EXISTS warehouse.pipeline_logs (
    log_id SERIAL,
    pipeline_name VARCHAR(100),
    status VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    records_processed INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for current and next 3 months
-- December 2025
CREATE TABLE IF NOT EXISTS warehouse.pipeline_logs_2025_12 
    PARTITION OF warehouse.pipeline_logs
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- January 2026
CREATE TABLE IF NOT EXISTS warehouse.pipeline_logs_2026_01 
    PARTITION OF warehouse.pipeline_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- February 2026
CREATE TABLE IF NOT EXISTS warehouse.pipeline_logs_2026_02 
    PARTITION OF warehouse.pipeline_logs
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- March 2026
CREATE TABLE IF NOT EXISTS warehouse.pipeline_logs_2026_03 
    PARTITION OF warehouse.pipeline_logs
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Create indexes on partitioned table
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_created_at 
    ON warehouse.pipeline_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_pipeline_name 
    ON warehouse.pipeline_logs(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_status 
    ON warehouse.pipeline_logs(status);

-- ============================================================================
-- 2. Staging Raw Data Table (Partitioned by ingested_at)
-- ============================================================================
-- This table stores raw ingested data and can grow very large with 100 GB/day

-- Drop existing table if it exists (use with caution in production)
-- DROP TABLE IF EXISTS staging.raw_data CASCADE;

-- Create partitioned table
CREATE TABLE IF NOT EXISTS staging.raw_data (
    id SERIAL,
    source_name VARCHAR(100),
    data_content JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, ingested_at)
) PARTITION BY RANGE (ingested_at);

-- Create monthly partitions
CREATE TABLE IF NOT EXISTS staging.raw_data_2025_12 
    PARTITION OF staging.raw_data
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS staging.raw_data_2026_01 
    PARTITION OF staging.raw_data
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS staging.raw_data_2026_02 
    PARTITION OF staging.raw_data
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS staging.raw_data_2026_03 
    PARTITION OF staging.raw_data
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_raw_data_ingested_at 
    ON staging.raw_data(ingested_at);
CREATE INDEX IF NOT EXISTS idx_raw_data_source 
    ON staging.raw_data(source_name);
CREATE INDEX IF NOT EXISTS idx_raw_data_jsonb 
    ON staging.raw_data USING GIN(data_content);

-- ============================================================================
-- 3. Fact Data Metrics Table (Partitioned by created_at)
-- ============================================================================
-- This table stores aggregated metrics and can grow large

-- Drop existing table if it exists (use with caution in production)
-- DROP TABLE IF EXISTS warehouse.fact_data_metrics CASCADE;

-- Create partitioned table
CREATE TABLE IF NOT EXISTS warehouse.fact_data_metrics (
    metric_id SERIAL,
    date_id INT REFERENCES warehouse.dim_date(date_id),
    source_id INT REFERENCES warehouse.dim_source(source_id),
    record_count INT,
    processing_time_seconds DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (metric_id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE IF NOT EXISTS warehouse.fact_data_metrics_2025_12 
    PARTITION OF warehouse.fact_data_metrics
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS warehouse.fact_data_metrics_2026_01 
    PARTITION OF warehouse.fact_data_metrics
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS warehouse.fact_data_metrics_2026_02 
    PARTITION OF warehouse.fact_data_metrics
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS warehouse.fact_data_metrics_2026_03 
    PARTITION OF warehouse.fact_data_metrics
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_fact_metrics_created_at 
    ON warehouse.fact_data_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_fact_metrics_date 
    ON warehouse.fact_data_metrics(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_metrics_source 
    ON warehouse.fact_data_metrics(source_id);

-- ============================================================================
-- 4. Uptime Log Table (Partitioned by timestamp)
-- ============================================================================
-- This table stores health check results and can grow large with 5-minute checks

-- Create monitoring schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Create partitioned table
CREATE TABLE IF NOT EXISTS monitoring.uptime_log (
    id SERIAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms FLOAT,
    error_message TEXT,
    overall_health VARCHAR(20),
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE IF NOT EXISTS monitoring.uptime_log_2025_12 
    PARTITION OF monitoring.uptime_log
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS monitoring.uptime_log_2026_01 
    PARTITION OF monitoring.uptime_log
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS monitoring.uptime_log_2026_02 
    PARTITION OF monitoring.uptime_log
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE IF NOT EXISTS monitoring.uptime_log_2026_03 
    PARTITION OF monitoring.uptime_log
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_uptime_log_timestamp 
    ON monitoring.uptime_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_uptime_log_service 
    ON monitoring.uptime_log(service_name);
CREATE INDEX IF NOT EXISTS idx_uptime_log_status 
    ON monitoring.uptime_log(status);

-- ============================================================================
-- Function to automatically create monthly partitions
-- ============================================================================
-- This function can be called monthly to create new partitions

CREATE OR REPLACE FUNCTION create_monthly_partition(
    table_name TEXT,
    schema_name TEXT,
    partition_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
    sql_stmt TEXT;
BEGIN
    -- Calculate partition boundaries
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    
    -- Generate partition name (e.g., pipeline_logs_2026_01)
    partition_name := table_name || '_' || TO_CHAR(start_date, 'YYYY_MM');
    
    -- Build SQL statement
    sql_stmt := format(
        'CREATE TABLE IF NOT EXISTS %I.%I PARTITION OF %I.%I FOR VALUES FROM (%L) TO (%L)',
        schema_name,
        partition_name,
        schema_name,
        table_name,
        start_date,
        end_date
    );
    
    -- Execute SQL
    EXECUTE sql_stmt;
    
    RAISE NOTICE 'Created partition % for table %', partition_name, table_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. Partitions are created monthly for better balance between:
--    - Query performance (smaller partitions = faster queries)
--    - Management overhead (fewer partitions = easier maintenance)
--
-- 2. For 100 GB/day scale:
--    - Monthly partitions handle ~3 TB/month per table
--    - Partition pruning enables fast queries on date ranges
--    - Old partitions can be archived/dropped easily
--
-- 3. To create future partitions, use:
--    SELECT create_monthly_partition('pipeline_logs', 'warehouse', '2026-04-01');
--
-- 4. To drop old partitions (e.g., older than 12 months):
--    DROP TABLE IF EXISTS warehouse.pipeline_logs_2024_12;
--
-- 5. For production, consider:
--    - Automated partition creation (via cron or Airflow DAG)
--    - Automated partition archival/deletion
--    - Monitoring partition sizes

