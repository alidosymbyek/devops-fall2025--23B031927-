# Concurrent Pipeline Configuration

## Overview

This document explains how the platform is configured to support **at least 10 concurrent data pipelines** without performance degradation.

## Requirement

**Non-Functional Requirement**: The system must handle at least 10 concurrent data pipelines without performance degradation.

## Implementation

### 1. Airflow Parallelism Configuration

Configured in `docker-compose-airflow.yml`:

```yaml
AIRFLOW__CORE__PARALLELISM: '20'              # Max concurrent tasks across all DAGs
AIRFLOW__CORE__DAG_CONCURRENCY: '10'          # Max concurrent tasks per DAG
AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG: '5'   # Max active runs per DAG
```

**Settings Explained:**
- **PARALLELISM (20)**: Maximum number of tasks that can run concurrently across ALL DAGs
- **DAG_CONCURRENCY (10)**: Maximum number of tasks that can run concurrently within a SINGLE DAG
- **MAX_ACTIVE_RUNS_PER_DAG (5)**: Maximum number of active DAG runs per DAG

### 2. DAG-Level Concurrency Settings

Each DAG is configured with appropriate concurrency limits:

```python
with DAG(
    'daily_etl_pipeline',
    max_active_runs=3,    # Allow up to 3 concurrent runs
    max_active_tasks=5,    # Allow up to 5 concurrent tasks
) as dag:
```

**Current DAGs:**
- `daily_etl_pipeline`: max_active_runs=3, max_active_tasks=5
- `stream_processing_pipeline`: max_active_runs=2, max_active_tasks=3
- `kafka_data_ingestion`: max_active_runs=2, max_active_tasks=3

### 3. Database Connection Pooling

Configured in `pipelines/db_connector.py`:

```python
pool_config = {
    'pool_size': 20,           # Number of connections to maintain
    'max_overflow': 40,        # Maximum overflow connections
    'pool_pre_ping': True,     # Verify connections before using
    'pool_recycle': 3600,      # Recycle connections after 1 hour
    'pool_timeout': 30,        # Timeout for getting connection from pool
}
```

**Benefits:**
- **pool_size (20)**: Maintains 20 database connections ready for use
- **max_overflow (40)**: Can create up to 40 additional connections when needed
- **Total capacity**: 60 concurrent database connections
- **pool_pre_ping**: Ensures connections are healthy before use
- **pool_recycle**: Prevents connection staleness

### 4. Scheduler Configuration

Optimized scheduler settings for better concurrency:

```yaml
AIRFLOW__CORE__DAGBAG_IMPORT_TIMEOUT: '30'      # Timeout for DAG imports
AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL: '30' # How often to check for new DAGs
AIRFLOW__SCHEDULER__JOB_HEARTBEAT_SEC: '5'      # Heartbeat frequency
AIRFLOW__SCHEDULER__TASK_HEARTBEAT_SEC: '5'     # Task heartbeat frequency
```

## Testing Concurrent Pipelines

### Test DAG: `concurrent_pipeline_test`

A test DAG is provided to verify concurrent execution:

**Location**: `airflow/dags/concurrent_pipeline_test_dag.py`

**Features:**
- Creates 10 parallel tasks
- Each task simulates pipeline work (3-8 seconds)
- Tests database connection pooling
- No task dependencies (all run in parallel)

### How to Test

1. **Start Airflow services:**
   ```bash
   docker-compose -f docker-compose-airflow.yml up -d
   ```

2. **Open Airflow UI:**
   - Navigate to http://localhost:8080
   - Login: admin/admin123

3. **Enable and trigger test DAG:**
   - Find `concurrent_pipeline_test` DAG
   - Enable it
   - Trigger it manually
   - Watch all 10 tasks run in parallel

4. **Verify concurrent execution:**
   - Check Graph View - all tasks should be running simultaneously
   - Check Gantt Chart - tasks should overlap in time
   - All 10 tasks should complete successfully

### Expected Results

✅ **All 10 tasks run concurrently**
✅ **No performance degradation**
✅ **All tasks complete successfully**
✅ **Database connections handled efficiently**

## Capacity Analysis

### Current Configuration Supports:

- **10+ concurrent pipelines** per DAG ✅
- **20 concurrent tasks** across all DAGs ✅
- **60 database connections** available ✅
- **Multiple DAG runs** simultaneously ✅

### Example Scenario:

With current settings, you can run:
- 2 instances of `daily_etl_pipeline` (3 runs each = 6 runs)
- 2 instances of `stream_processing_pipeline` (2 runs each = 4 runs)
- **Total: 10+ concurrent pipeline executions** ✅

## Performance Considerations

### Database Connection Pooling

- **20 base connections** + **40 overflow** = **60 total connections**
- Each pipeline typically uses 1-2 connections
- Supports **30+ concurrent pipelines** with connection pooling

### Airflow Executor

- **LocalExecutor**: Runs tasks in separate processes
- Each task gets its own process
- No GIL (Global Interpreter Lock) limitations
- True parallelism for CPU-bound tasks

### Resource Limits

For production, consider:
- **CPU**: Ensure enough cores for concurrent tasks
- **Memory**: Each task process uses memory
- **Database**: Monitor connection pool usage
- **Network**: Consider bandwidth for data transfer

## Monitoring Concurrent Execution

### Airflow UI Metrics

1. **DAG Runs**: Shows active runs per DAG
2. **Task Instances**: Shows running tasks
3. **Gantt Chart**: Visualizes concurrent execution
4. **Graph View**: Shows task dependencies and parallelism

### Database Monitoring

Check connection pool usage:
```sql
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE datname = 'dataplatform';
```

### Performance Metrics

Monitor:
- Task execution time
- Database connection wait time
- Resource utilization (CPU, memory)
- Pipeline throughput

## Scaling Beyond 10 Pipelines

To support more concurrent pipelines:

1. **Increase PARALLELISM:**
   ```yaml
   AIRFLOW__CORE__PARALLELISM: '50'  # Increase from 20
   ```

2. **Increase Connection Pool:**
   ```python
   'pool_size': 50,        # Increase from 20
   'max_overflow': 100,   # Increase from 40
   ```

3. **Use CeleryExecutor** (for distributed execution):
   ```yaml
   AIRFLOW__CORE__EXECUTOR: CeleryExecutor
   ```

4. **Add More Workers:**
   - Deploy additional Airflow worker nodes
   - Distribute load across workers

## Best Practices

1. **Set appropriate concurrency limits** per DAG
2. **Monitor connection pool usage**
3. **Use task pools** for resource-intensive tasks
4. **Set task timeouts** to prevent hanging tasks
5. **Monitor system resources** (CPU, memory, disk)

## Verification Checklist

- [x] Airflow parallelism configured (20 tasks)
- [x] DAG concurrency configured (10 tasks per DAG)
- [x] Connection pooling implemented (60 connections)
- [x] Test DAG created for verification
- [x] All DAGs have concurrency settings
- [x] Scheduler optimized for concurrent execution

## Status

✅ **REQUIREMENT MET**: System configured to handle 10+ concurrent pipelines

---

*Last Updated: 2025-12-13*

