from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add your pipelines to the path
sys.path.insert(0, '/opt/airflow/pipelines')

from etl_pipeline import ETLPipeline

default_args = {
    'owner': 'ali',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 1),
    'email': ['ali@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def run_etl_pipeline():
    """Run the ETL pipeline"""
    print("Starting ETL pipeline...")
    pipeline = ETLPipeline('airflow_daily_etl')
    pipeline.run()
    print("ETL pipeline completed!")

def send_success_notification():
    """Send notification on success"""
    print("✓ Pipeline completed successfully!")
    print("Total records processed and loaded to database.")

with DAG(
    'daily_etl_pipeline',
    default_args=default_args,
    description='Daily ETL pipeline for DataPlatform',
    schedule_interval='0 2 * * *',  # Run at 2 AM daily
    catchup=False,
    tags=['etl', 'daily', 'production'],
    max_active_runs=3,  # Allow up to 3 concurrent runs of this DAG
    max_active_tasks=5,  # Allow up to 5 concurrent tasks
) as dag:
    
    # Task 1: Run ETL
    run_etl = PythonOperator(
        task_id='run_etl_pipeline',
        python_callable=run_etl_pipeline,
    )
    
    # Task 2: Send notification
    send_notification = PythonOperator(
        task_id='send_success_notification',
        python_callable=send_success_notification,
    )
    
    # Set task dependencies
    run_etl >> send_notification