"""
Test DAG for Concurrent Pipeline Execution
This DAG creates multiple parallel tasks to test concurrent pipeline support
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import time
import random

default_args = {
    'owner': 'ali',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 1),
    'email': ['ali@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
}

def simulate_pipeline_task(task_id, duration=5):
    """Simulate a pipeline task that takes some time"""
    print(f"Starting task {task_id}...")
    print(f"Task {task_id} will run for {duration} seconds")
    
    # Simulate work
    for i in range(duration):
        time.sleep(1)
        print(f"Task {task_id}: Processing... {i+1}/{duration}")
    
    # Simulate some database operations
    import sys
    from pathlib import Path
    sys.path.insert(0, '/opt/airflow/pipelines')
    
    try:
        from db_connector import DatabaseConnector
        db = DatabaseConnector()
        # Just test connection, don't do heavy operations
        if db.test_connection():
            print(f"Task {task_id}: Database connection successful")
    except Exception as e:
        print(f"Task {task_id}: Database test skipped - {e}")
    
    print(f"Task {task_id} completed successfully!")
    return f"Task {task_id} result"

# Create tasks for 10 concurrent pipelines
tasks = []
for i in range(10):
    task = PythonOperator(
        task_id=f'pipeline_task_{i+1}',
        python_callable=simulate_pipeline_task,
        op_args=[f'Pipeline-{i+1}', random.randint(3, 8)],  # Random duration 3-8 seconds
        pool='default_pool',  # Use default pool
    )
    tasks.append(task)

with DAG(
    'concurrent_pipeline_test',
    default_args=default_args,
    description='Test DAG for concurrent pipeline execution (10 parallel tasks)',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['test', 'concurrency', 'performance'],
    max_active_runs=1,  # Only one run at a time for testing
    max_active_tasks=10,  # Allow all 10 tasks to run concurrently
) as dag:
    
    # All tasks run in parallel (no dependencies)
    # This tests if Airflow can handle 10 concurrent tasks
    tasks

