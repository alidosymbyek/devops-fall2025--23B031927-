"""
Kafka Data Ingestion DAG
Ingests data from APIs and sends to Kafka for real-time processing
Runs every 5 minutes to feed the stream
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add pipelines to path
sys.path.insert(0, '/opt/airflow/pipelines')

from stream.kafka_producer import KafkaDataProducer

default_args = {
    'owner': 'ali',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 1),
    'email': ['ali@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

def ingest_to_kafka():
    """Ingest data from APIs and send to Kafka"""
    print("Starting data ingestion to Kafka...")
    
    producer = KafkaDataProducer(
        bootstrap_servers='kafka:29092',  # Internal Docker network
        topic='data-stream'
    )
    
    try:
        # Ingest from sample API
        count = producer.send_sample_data()
        print(f"✓ Ingested {count} records to Kafka")
        return count
    finally:
        producer.close()

with DAG(
    'kafka_data_ingestion',
    default_args=default_args,
    description='Ingest data from APIs and send to Kafka stream (5-minute intervals)',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    catchup=False,
    tags=['ingestion', 'kafka', 'real-time', 'production'],
    max_active_runs=2,  # Allow 2 concurrent runs
    max_active_tasks=3,  # Allow 3 concurrent tasks
) as dag:
    
    # Task: Ingest data to Kafka
    ingest_data = PythonOperator(
        task_id='ingest_to_kafka',
        python_callable=ingest_to_kafka,
    )
    
    ingest_data

