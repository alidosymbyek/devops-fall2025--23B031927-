-- Create schemas for organizing tables
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Staging table for raw data
CREATE TABLE IF NOT EXISTS staging.raw_data (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100),
    data_content JSONB,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension table: Date
CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INT,
    month INT,
    day INT,
    day_of_week INT,
    quarter INT,
    is_weekend BOOLEAN
);

-- Dimension table: Source
CREATE TABLE IF NOT EXISTS warehouse.dim_source (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) UNIQUE NOT NULL,
    source_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact table: Data metrics
CREATE TABLE IF NOT EXISTS warehouse.fact_data_metrics (
    metric_id SERIAL PRIMARY KEY,
    date_id INT REFERENCES warehouse.dim_date(date_id),
    source_id INT REFERENCES warehouse.dim_source(source_id),
    record_count INT,
    processing_time_seconds DECIMAL(10,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_fact_metrics_date ON warehouse.fact_data_metrics(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_metrics_source ON warehouse.fact_data_metrics(source_id);
CREATE INDEX IF NOT EXISTS idx_staging_source ON staging.raw_data(source_name);

-- Pipeline execution log table
CREATE TABLE IF NOT EXISTS warehouse.pipeline_logs (
    log_id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100),
    status VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    records_processed INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);