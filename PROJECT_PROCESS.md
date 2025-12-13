# Data Platform Project - Process Flow Documentation

**Project ID**: 23B031927  
**Student**: ALI DOSYMBYEK  
**Last Updated**: 2025-12-13

---

## Overview

This document explains the complete data processing workflow of the Data Platform project, from data ingestion to visualization and monitoring.

---

## High-Level Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Data Sources   │────▶│  ETL Pipeline │────▶│  PostgreSQL │
│  (CSV, API)     │     │  (Airflow)   │     │  Database   │
└─────────────────┘     └──────────────┘     └─────────────┘
        │                       │                      │
        │                       │                      │
        └───────────┬───────────┴──────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │   Kafka Stream        │
        │   (Real-Time)         │
        └──────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  Streamlit Dashboard  │
        └──────────────────────┘
```

---

## Process Flows

### 1. Batch ETL Pipeline Process (Daily)

**Schedule**: Runs daily at 2:00 AM via Airflow  
**DAG**: `daily_etl_pipeline`  
**Components**: Extract → Transform → Load

#### Step-by-Step Process:

1. **Orchestration Trigger** (Airflow)
   - Airflow scheduler triggers `daily_etl_pipeline` DAG at 2 AM
   - Creates task: `run_etl_pipeline`

2. **EXTRACT Phase**
   - **CSV Extraction** (`pipelines/extract/csv_extractor.py`)
     - Scans `./data/raw/` directory
     - Reads all CSV files (e.g., `customers.csv`, `sales_data.csv`)
     - Returns dictionary of DataFrames keyed by filename
   
   - **API Extraction** (`pipelines/extract/api_extractor.py`)
     - Fetches data from configured API endpoints
     - Default: `https://jsonplaceholder.typicode.com/users`
     - Handles API failures gracefully (logs warning, continues)
   
   - **Result**: Dictionary of DataFrames ready for transformation

3. **TRANSFORM Phase** (`pipelines/transform/data_transformer.py`)
   - For each data source:
     - **Data Cleaning**:
       - Removes duplicates
       - Handles missing values
       - Standardizes data types
     - **Data Validation**:
       - Checks data quality
       - Validates required fields
     - **Metadata Enrichment**:
       - Adds extraction timestamp
       - Adds source information
     - **Data Quality Checks** (`pipelines/quality/data_quality_checker.py`):
       - Validates data integrity
       - Checks for anomalies
   
   - **Result**: Clean, validated DataFrames

4. **LOAD Phase** (`pipelines/load/data_loader.py`)
   - For each transformed dataset:
     - **Staging Layer**:
       - Creates/updates staging tables in PostgreSQL
       - Table names: `staging.{source_name}` (sanitized)
       - Uses batch inserts (chunked for large datasets)
     - **Data Warehouse**:
       - Transforms staging data to warehouse schema
       - Creates dimension and fact tables
   
   - **Pipeline Logging**:
     - Logs execution to `pipeline_executions` table
     - Records: status, records processed, duration, errors

5. **Notification** (Airflow Task: `send_success_notification`)
   - Logs success message
   - Can trigger email alerts if configured

6. **Monitoring & Alerts**
   - Execution logged to database
   - Email alerts sent on failure (via `EmailAlertManager`)
   - Logs written to `logs/daily_etl_YYYYMMDD.log`

---

### 2. Real-Time Stream Processing Process (Every 5 Minutes)

**Schedule**: Runs every 5 minutes via Airflow  
**DAGs**: 
- `kafka_data_ingestion` (Producer)
- `stream_processing_pipeline` (Consumer)

#### Producer Flow (Data Ingestion to Kafka):

1. **Orchestration Trigger** (Airflow)
   - Airflow scheduler triggers `kafka_data_ingestion` DAG every 5 minutes
   - Creates task: `ingest_to_kafka`

2. **Data Ingestion** (`pipelines/stream/kafka_producer.py`)
   - **Kafka Producer Initialization**:
     - Connects to Kafka broker (`kafka:29092` in Docker network)
     - Topic: `data-stream`
   
   - **Data Collection**:
     - Fetches data from APIs (same endpoints as batch ETL)
     - Optionally reads from CSV files
     - Formats data as JSON messages
   
   - **Message Production**:
     - Sends messages to Kafka topic in batches
     - Each message contains:
       - Source information
       - Timestamp
       - Data payload (JSON)
     - Uses idempotent producer for reliability
   
   - **Result**: Data available in Kafka topic `data-stream`

#### Consumer Flow (Kafka to Database):

1. **Orchestration Trigger** (Airflow)
   - Airflow scheduler triggers `stream_processing_pipeline` DAG every 5 minutes
   - Creates task: `process_kafka_stream`

2. **Stream Processing** (`pipelines/stream/kafka_processor.py`)
   - **Kafka Consumer Initialization**:
     - Connects to Kafka broker
     - Subscribes to `data-stream` topic
     - Consumer group: `stream_processor_group`
   
   - **Message Consumption**:
     - Polls messages from Kafka (configurable batch size)
     - Processes messages in batches for efficiency
     - Handles consumer offsets for reliability
   
   - **Data Transformation**:
     - Uses same transformer as batch ETL
     - Cleans and validates stream data
     - Applies data quality checks
   
   - **Database Loading**:
     - Loads transformed data to staging tables
     - Uses batch inserts for performance
     - Logs execution to `pipeline_executions` table
   
   - **Result**: Real-time data in PostgreSQL (< 5 minute latency)

---

### 3. Data Visualization Process

**Component**: Streamlit Dashboard (`dashboard/app.py`)

#### Process Flow:

1. **Dashboard Initialization**
   - Connects to PostgreSQL database
   - Reads configuration from `config/config.yaml`

2. **Data Retrieval**
   - **Pipeline Metrics**:
     - Queries `pipeline_executions` table
     - Calculates success rate, average duration
     - Gets recent execution history
   
   - **Data Overview**:
     - Queries staging and warehouse tables
     - Counts records by source
     - Gets latest data timestamps
   
   - **Execution History**:
     - Retrieves recent pipeline runs
     - Shows status, duration, records processed

3. **Visualization**
   - Displays metrics in Streamlit widgets
   - Charts and graphs for trends
   - Auto-refresh capability (configurable interval)

4. **User Interaction**
   - Users can view:
     - Pipeline execution status
     - Data quality metrics
     - Recent logs
     - Data statistics

---

### 4. Monitoring & Alerting Process

**Components**: 
- Email Alerts (`pipelines/monitoring/email_alerts.py`)
- Health Checks (`pipelines/monitoring/health_checker.py`)
- Uptime Tracking (`pipelines/monitoring/uptime_tracker.py`)
- Prometheus & Grafana (configured)

#### Process Flow:

1. **Pipeline Execution Monitoring**
   - Each pipeline execution logs to database
   - Status tracked: SUCCESS, FAILED, RUNNING
   - Metrics recorded: duration, records processed, errors

2. **Email Alerts**
   - **On Failure**:
     - Pipeline failure detected
     - Email sent via `EmailAlertManager`
     - Includes error details and stack trace
   
   - **On Success** (optional):
     - Summary email with metrics
     - Execution statistics

3. **Health Checks**
   - Database connectivity checks
   - Service availability monitoring
   - Resource usage tracking

4. **Prometheus Metrics** (if configured)
   - Pipeline execution metrics
   - Database connection metrics
   - System resource metrics

5. **Grafana Dashboards**
   - Visualizes Prometheus metrics
   - Real-time monitoring dashboards
   - Alert visualization

---

## Data Flow Diagram

### Batch ETL Flow:
```
CSV Files (data/raw/) ──┐
                        ├──> CSVExtractor ──> DataFrames
API Endpoints ──────────┘
                        │
                        ▼
                  DataTransformer
                  (Clean, Validate, Enrich)
                        │
                        ▼
                  DataQualityChecker
                  (Quality Validation)
                        │
                        ▼
                  DataLoader
                  (Load to PostgreSQL)
                        │
                        ├──> staging.{table_name}
                        └──> warehouse.{table_name}
```

### Real-Time Stream Flow:
```
API Endpoints ──> KafkaProducer ──> Kafka Topic (data-stream)
                                                      │
                                                      ▼
                                            KafkaConsumer
                                                      │
                                                      ▼
                                            DataTransformer
                                                      │
                                                      ▼
                                            DataLoader ──> PostgreSQL
```

---

## Configuration

### Key Configuration Files:

1. **`config/config.yaml`**
   - Database connection settings
   - Data source paths and API endpoints
   - Logging configuration
   - Pipeline schedule settings

2. **`docker-compose-airflow.yml`**
   - Service definitions (Airflow, PostgreSQL, Kafka, Zookeeper)
   - Network configuration
   - Volume mounts
   - Environment variables

3. **Airflow DAGs** (`airflow/dags/`)
   - Schedule intervals
   - Task dependencies
   - Retry policies
   - Concurrency settings

---

## Database Schema

### Staging Layer:
- `staging.customers` - Raw customer data
- `staging.sales_data` - Raw sales data
- `staging.api_users` - API-sourced user data

### Warehouse Layer:
- Dimension tables (customers, products, etc.)
- Fact tables (sales, transactions, etc.)

### Metadata:
- `pipeline_executions` - Execution logs
  - Columns: id, pipeline_name, status, records_processed, start_time, end_time, error_message

---

## Concurrent Processing

The platform supports **10+ concurrent pipelines**:

- **Airflow Configuration**:
  - `parallelism`: 20 (total concurrent tasks)
  - `dag_concurrency`: 10 (per DAG)
  - `max_active_runs`: 3 (per DAG)

- **Database Connection Pooling**:
  - Pool size: 20 base connections
  - Max overflow: 40 additional connections
  - Total: 60 concurrent connections

- **Kafka Parallelism**:
  - Multiple consumer groups supported
  - Partition-based parallelism
  - Batch processing for efficiency

---

## Security & Encryption

1. **TLS/SSL in Transit**:
   - PostgreSQL connections encrypted
   - SSL certificates configured
   - SSL mode: require/verify-ca/verify-full

2. **Encryption at Rest**:
   - AES-256 encryption via filesystem
   - Encrypted database volumes
   - Secure credential storage

---

## Error Handling & Recovery

1. **Pipeline Failures**:
   - Automatic retries (configurable: default 3)
   - Error logging to database
   - Email alerts on failure
   - Graceful degradation (continues on API failures)

2. **Kafka Failures**:
   - Consumer offset management
   - Message replay capability
   - Dead letter queue handling

3. **Database Failures**:
   - Connection retry logic
   - Transaction rollback on errors
   - Connection pooling for resilience

---

## Performance Characteristics

- **Batch ETL**: 
  - Runs daily (2 AM)
  - Processes all available data sources
  - Typical duration: varies by data volume

- **Real-Time Stream**:
  - Runs every 5 minutes
  - Latency: < 5 minutes end-to-end
  - Batch processing for efficiency

- **Scalability**:
  - Supports 100+ GB/day (with optimization)
  - 10+ concurrent pipelines
  - Connection pooling for high concurrency

---

## Monitoring Points

1. **Pipeline Execution**:
   - Success/failure rate
   - Average execution time
   - Records processed per run

2. **Data Quality**:
   - Validation failures
   - Duplicate detection
   - Missing value rates

3. **System Health**:
   - Database connectivity
   - Kafka broker status
   - Airflow scheduler health
   - Resource usage (CPU, memory, disk)

4. **Uptime**:
   - Service availability tracking
   - Target: 99.5% uptime
   - Automated alerting for downtime

---

## Summary

The Data Platform processes data through two main pipelines:

1. **Batch ETL** (Daily): Traditional extract-transform-load for bulk data processing
2. **Real-Time Stream** (Every 5 min): Kafka-based streaming for near-real-time data processing

Both pipelines:
- Extract from multiple sources (CSV, API)
- Transform and validate data
- Load to PostgreSQL database
- Log executions and send alerts
- Support concurrent processing

The platform provides:
- **Visualization**: Streamlit dashboard for metrics and data overview
- **Monitoring**: Prometheus/Grafana for system metrics
- **Security**: TLS encryption and data protection
- **Scalability**: Support for high-volume concurrent processing

---

*For detailed setup instructions, see:*
- `README.md` - Main project documentation
- `KAFKA_SETUP.md` - Kafka stream processing guide
- `DATABASE_ENCRYPTION.md` - Security configuration
- `CONCURRENT_PIPELINES.md` - Concurrency configuration

