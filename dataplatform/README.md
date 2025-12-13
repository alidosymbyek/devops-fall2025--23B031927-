# Data Platform Project

**Project ID**: 23B031927  
**Student**: ALI DOSYMBYEK  
**Mentor**: ROMAN SAVOSKIN  
**Topic**: DATA PLATFORM

## Project Overview

A comprehensive data platform that collects, processes, stores, and visualizes data from multiple sources. The platform includes automated ETL pipelines, real-time stream processing capabilities, and user-friendly dashboards for analytics.

## Architecture

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

## Project Structure

```
dataplatform/
├── airflow/                 # Apache Airflow orchestration
│   ├── dags/               # ETL DAG definitions
│   └── Dockerfile          # Airflow container setup
├── pipelines/              # Core ETL pipeline code
│   ├── extract/            # Data ingestion (CSV, API)
│   ├── transform/          # Data transformation & cleaning
│   ├── load/               # Data loading to database
│   ├── quality/            # Data quality checks
│   ├── stream/             # Real-time stream processing (Kafka)
│   └── monitoring/         # Alerts and monitoring
├── dashboard/              # Streamlit visualization dashboard
├── sql/                    # Database schema definitions
├── config/                 # Configuration files
├── data/                   # Data storage (raw, processed, staging)
└── docker-compose-airflow.yml  # Docker orchestration
```

## Features

### ✅ Implemented Features

1. **Data Ingestion**
   - CSV file extraction
   - REST API data extraction
   - Multiple source support

2. **Data Transformation**
   - Data cleaning and validation
   - Duplicate removal
   - Data quality checks
   - Metadata enrichment

3. **Data Storage**
   - PostgreSQL database
   - Staging and warehouse schemas
   - Dimension and fact tables
   - Pipeline execution logging

4. **Data Visualization**
   - Streamlit dashboard
   - Pipeline metrics
   - Data overview
   - Execution history

5. **Monitoring & Alerts**
   - Email notifications
   - Pipeline execution logging
   - Success/failure alerts

6. **Orchestration**
   - Apache Airflow integration
   - Scheduled ETL pipelines
   - Task dependencies

7. **Real-Time Stream Processing** ✅ **NEW**
   - Kafka-based streaming
   - 5-minute data refresh latency
   - Producer and consumer modules
   - Automated stream processing DAGs

## Requirements Status

### Functional Requirements ✅ (5/5 Complete)

- ✅ Data Ingestion Service
- ✅ Data Transformation and Cleaning
- ✅ Data Storage Layer
- ✅ Data Visualization Dashboard
- ✅ Monitoring and Alerts

### Non-Functional Requirements ✅ (5/5 Complete)

- ✅ **Concurrent Pipelines**: **IMPLEMENTED** (10+ concurrent pipelines supported)
- ✅ **Real-Time Streaming**: **IMPLEMENTED** (Kafka with 5-minute latency)
- ✅ **Availability (99.5%)**: **IMPLEMENTED** (Uptime monitoring with Prometheus/Grafana)
- ✅ **Security (TLS/AES-256)**: **IMPLEMENTED** (TLS for database, AES-256 at rest via filesystem)
- ✅ **Scalability (100 GB/day)**: **IMPLEMENTED** (Table partitioning, optimized batch sizes, resource limits)

**See [REQUIREMENTS_CHECKLIST.md](REQUIREMENTS_CHECKLIST.md) for detailed status.**

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- PostgreSQL (or use Docker)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/alidosymbyek/devops-fall2025--23B031927-.git
   cd devops-fall2025--23B031927-/dataplatform
   ```

2. **Set up environment variables**
   Create a `.env` file in the `dataplatform/` directory:
   ```env
   DB_HOST=localhost
   DB_PORT=5433
   DB_NAME=dataplatform
   DB_USER=datauser
   DB_PASSWORD=mypassword
   ```

3. **Start services**
   ```bash
   docker-compose -f docker-compose-airflow.yml up -d
   ```

4. **Initialize database**
   ```bash
   python pipelines/setup_database.py
   ```

5. **Access services**
   - Airflow UI: http://localhost:8080 (admin/admin123)
   - Grafana: http://localhost:3000 (admin/admin123)
   - Prometheus: http://localhost:9090
   - Dashboard: `streamlit run dashboard/app.py`

## Usage

### Running ETL Pipeline

**Via Airflow:**
1. Open Airflow UI at http://localhost:8080
2. Enable the `daily_etl_pipeline` DAG
3. Trigger manually or wait for scheduled run (2 AM daily)

**Via Command Line:**
```bash
python pipelines/etl_pipeline.py
```

### Viewing Dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard shows:
- Pipeline execution metrics
- Data overview
- Execution history
- Recent logs

## Configuration

### Data Sources

Edit `config/config.yaml`:
```yaml
data_sources:
  csv_folder: ./data/raw
  api_endpoints:
    - name: sample_api
      url: https://jsonplaceholder.typicode.com/users
```

### Pipeline Settings

```yaml
pipeline:
  schedule: daily
  retry_count: 3
```

## Real-Time Stream Processing ✅

**Status**: ✅ **IMPLEMENTED**

The platform now includes Kafka-based real-time stream processing:

- **Kafka Infrastructure**: Zookeeper and Kafka brokers
- **Producer**: Ingests data from APIs and sends to Kafka
- **Consumer**: Processes Kafka streams and loads to database
- **Latency**: < 5 minutes (runs every 5 minutes via Airflow)
- **DAGs**: 
  - `kafka_data_ingestion` - Ingests data to Kafka
  - `stream_processing_pipeline` - Processes Kafka streams

See [KAFKA_SETUP.md](KAFKA_SETUP.md) for detailed setup and usage instructions.

## Database Encryption ✅

**Status**: ✅ **IMPLEMENTED**

The platform now includes full database encryption:

- **TLS/SSL in Transit**: All database connections encrypted
- **AES-256 at Rest**: Data encrypted at rest via filesystem encryption
- **SSL Certificates**: Self-signed certificates for development (CA-signed for production)
- **Configurable SSL Modes**: Support for require, verify-ca, verify-full

See [DATABASE_ENCRYPTION.md](DATABASE_ENCRYPTION.md) for detailed setup and configuration.

## Concurrent Pipeline Support ✅

**Status**: ✅ **IMPLEMENTED**

The platform now supports **10+ concurrent data pipelines**:

- **Airflow Parallelism**: 20 concurrent tasks across all DAGs
- **DAG Concurrency**: 10 concurrent tasks per DAG
- **Connection Pooling**: 60 database connections (20 base + 40 overflow)
- **Test DAG**: `concurrent_pipeline_test` for verification

See [CONCURRENT_PIPELINES.md](CONCURRENT_PIPELINES.md) for detailed configuration and testing.

## All Requirements Complete ✅

All project requirements have been successfully implemented:

1. ✅ **Real-Time Stream Processing** - **COMPLETED** (Kafka with < 5 min latency)
2. ✅ **Database Encryption (TLS + AES-256)** - **COMPLETED**
3. ✅ **Concurrent Pipeline Configuration** - **COMPLETED** (10+ pipelines)
4. ✅ **Uptime Monitoring (99.5%)** - **COMPLETED** (Prometheus/Grafana)
5. ✅ **Scalability (100 GB/day)** - **COMPLETED** (Table partitioning, optimized batches)

## Documentation

- [KAFKA_SETUP.md](KAFKA_SETUP.md) - Kafka stream processing setup and usage
- [DATABASE_ENCRYPTION.md](DATABASE_ENCRYPTION.md) - Database encryption setup (TLS + AES-256)
- [CONCURRENT_PIPELINES.md](CONCURRENT_PIPELINES.md) - Concurrent pipeline configuration and testing
- [UPTIME_MONITORING_SETUP.md](UPTIME_MONITORING_SETUP.md) - Uptime monitoring setup and configuration
- [SCALABILITY_IMPLEMENTATION.md](SCALABILITY_IMPLEMENTATION.md) - Scalability optimizations (100 GB/day support)
- [REQUIREMENTS_STATUS.md](REQUIREMENTS_STATUS.md) - Complete requirements status (100% complete)
- [PROJECT_PROCESS.md](PROJECT_PROCESS.md) - Complete process flow documentation

## Technologies Used

- **Python 3.8+** - Core language
- **Apache Airflow** - Workflow orchestration
- **PostgreSQL** - Data storage
- **Kafka** - Real-time stream processing
- **Streamlit** - Dashboard visualization
- **Docker** - Containerization
- **Pandas** - Data processing
- **SQLAlchemy** - Database ORM
- **Loguru** - Logging
- **kafka-python** - Kafka client library

## Project Status

**Overall Completion: 100% ✅**

- ✅ All functional requirements implemented (5/5)
- ✅ All non-functional requirements implemented (5/5)
- ✅ Real-time streaming implemented (Kafka with < 5 min latency)
- ✅ Database encryption implemented (TLS + AES-256)
- ✅ Concurrent pipelines configured (10+ support)
- ✅ Uptime monitoring implemented (99.5% target with Prometheus/Grafana)
- ✅ Scalability optimizations implemented (100 GB/day support)

## Repository Structure

```
devops-fall2025--23B031927-/
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       └── basic-ci.yml
└── dataplatform/               # Project files
    ├── airflow/                # Airflow DAGs and configuration
    ├── pipelines/              # ETL pipeline code
    ├── monitoring/             # Prometheus & Grafana configs
    ├── sql/                    # Database scripts
    ├── dashboard/              # Streamlit dashboard
    └── ... (all project files)
```

## License

This project is part of an academic assignment.

## Contact

- **Student**: ALI DOSYMBYEK
- **Mentor**: ROMAN SAVOSKIN

---

*Last Updated: 2025-12-13*

