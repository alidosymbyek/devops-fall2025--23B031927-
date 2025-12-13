"""
Real-Time Stream Processing DAG
Processes data from Kafka streams every 5 minutes
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add pipelines to path
sys.path.insert(0, '/opt/airflow/pipelines')

from stream.kafka_processor import process_kafka_stream

default_args = {
    'owner': 'ali',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 1),
    'email': ['ali@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    'max_active_runs': 1,  # Only one run at a time for stream processing
}

def run_stream_processing():
    """Execute Kafka stream processing"""
    print("Starting real-time stream processing...")
    result = process_kafka_stream()
    print(f"Stream processing completed: {result}")
    
    if result.get('status') == 'error':
        raise Exception(f"Stream processing failed: {result.get('message')}")
    
    return result

with DAG(
    'stream_processing_pipeline',
    default_args=default_args,
    description='Real-time stream processing from Kafka (5-minute intervals)',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    catchup=False,
    tags=['streaming', 'kafka', 'real-time', 'production'],
    max_active_runs=2,  # Allow 2 concurrent runs for stream processing
    max_active_tasks=3,  # Allow 3 concurrent tasks
) as dag:
    
    # Task: Process Kafka stream
    process_stream = PythonOperator(
        task_id='process_kafka_stream',
        python_callable=run_stream_processing,
        pool='stream_processing_pool',  # Optional: use pool to limit concurrency
    )
    
    # Single task DAG for stream processing
    process_stream

