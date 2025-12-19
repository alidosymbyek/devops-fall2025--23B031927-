"""
Pipeline Monitoring DAG
Monitors pipeline health and sends alerts for failures/delays within 2 minutes
Runs every minute to ensure timely alerting
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add pipelines to path
sys.path.insert(0, '/opt/airflow/pipelines')

from monitoring.pipeline_monitor import PipelineMonitor

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

def monitor_pipeline_health():
    """Monitor pipeline health and send alerts"""
    from loguru import logger
    
    logger.info("Starting pipeline health monitoring...")
    monitor = PipelineMonitor()
    monitor.monitor_pipelines()
    logger.info("Pipeline monitoring complete")

# Create DAG that runs every minute
dag = DAG(
    'pipeline_health_monitoring',
    default_args=default_args,
    description='Monitor pipeline health and send alerts for failures/delays',
    schedule_interval=timedelta(minutes=1),  # Run every minute
    catchup=False,
    tags=['monitoring', 'alerts'],
)

# Task to monitor pipelines
monitor_task = PythonOperator(
    task_id='monitor_pipeline_health',
    python_callable=monitor_pipeline_health,
    dag=dag,
)

monitor_task

