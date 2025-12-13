"""
Kafka Producer for Real-Time Data Ingestion
Sends data from various sources to Kafka topics for stream processing
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from extract.api_extractor import APIExtractor
from extract.csv_extractor import CSVExtractor


class KafkaDataProducer:
    """Produce data to Kafka topics for real-time processing"""
    
    def __init__(self, 
                 bootstrap_servers: str = 'localhost:9092',
                 topic: str = 'data-stream'):
        """
        Initialize Kafka Data Producer
        
        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Kafka topic to produce to
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self.api_extractor = APIExtractor()
        self.csv_extractor = CSVExtractor()
        
        # Setup logging
        log_path = Path(__file__).parent.parent.parent / 'logs'
        log_path.mkdir(exist_ok=True)
        logger.add(
            log_path / f"kafka_producer_{datetime.now().strftime('%Y%m%d')}.log",
            rotation="1 day",
            retention="30 days"
        )
    
    def create_producer(self):
        """Create Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True
            )
            logger.info(f"✓ Kafka producer created for topic: {self.topic}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create Kafka producer: {e}")
            return False
    
    def send_dataframe(self, df: pd.DataFrame, source: str) -> int:
        """
        Send DataFrame to Kafka topic
        
        Args:
            df: DataFrame to send
            source: Source identifier
            
        Returns:
            int: Number of messages sent
        """
        if not self.producer:
            if not self.create_producer():
                return 0
        
        if df.empty:
            logger.warning(f"Empty DataFrame from {source}, skipping")
            return 0
        
        sent_count = 0
        try:
            # Convert DataFrame to records
            records = df.to_dict('records')
            
            # Send in batches
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                
                message = {
                    'source': source,
                    'data': batch,
                    'timestamp': datetime.now().isoformat(),
                    'batch_size': len(batch),
                    'processed': False
                }
                
                future = self.producer.send(self.topic, value=message)
                record_metadata = future.get(timeout=10)
                
                sent_count += len(batch)
                logger.info(f"✓ Sent batch of {len(batch)} records to topic {self.topic}, partition {record_metadata.partition}")
            
            # Flush to ensure all messages are sent
            self.producer.flush()
            logger.info(f"✓ Successfully sent {sent_count} records from {source} to Kafka")
            
            return sent_count
            
        except KafkaError as e:
            logger.error(f"✗ Kafka error sending data: {e}")
            return sent_count
        except Exception as e:
            logger.error(f"✗ Failed to send data: {e}")
            return sent_count
    
    def ingest_from_api(self, api_url: str, source_name: str) -> int:
        """
        Ingest data from API and send to Kafka
        
        Args:
            api_url: API endpoint URL
            source_name: Source identifier
            
        Returns:
            int: Number of records sent
        """
        try:
            logger.info(f"Ingesting data from API: {api_url}")
            df = self.api_extractor.extract_from_api(api_url, source_name)
            return self.send_dataframe(df, source_name)
        except Exception as e:
            logger.error(f"✗ Failed to ingest from API: {e}")
            return 0
    
    def ingest_from_csv(self, csv_path: str, source_name: Optional[str] = None) -> int:
        """
        Ingest data from CSV and send to Kafka
        
        Args:
            csv_path: Path to CSV file
            source_name: Source identifier (defaults to filename)
            
        Returns:
            int: Number of records sent
        """
        try:
            if source_name is None:
                source_name = Path(csv_path).stem
            
            logger.info(f"Ingesting data from CSV: {csv_path}")
            df = self.csv_extractor.extract_csv(csv_path)
            return self.send_dataframe(df, source_name)
        except Exception as e:
            logger.error(f"✗ Failed to ingest from CSV: {e}")
            return 0
    
    def send_sample_data(self) -> int:
        """Send sample data to Kafka for testing"""
        try:
            logger.info("Sending sample data to Kafka")
            df = self.api_extractor.extract_sample_data()
            return self.send_dataframe(df, 'sample_api_stream')
        except Exception as e:
            logger.error(f"✗ Failed to send sample data: {e}")
            return 0
    
    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


def produce_sample_data():
    """Main function for producing sample data (for testing)"""
    producer = KafkaDataProducer(
        bootstrap_servers='kafka:29092',  # Internal Docker network
        topic='data-stream'
    )
    
    try:
        count = producer.send_sample_data()
        logger.info(f"Sent {count} records to Kafka")
        return count
    finally:
        producer.close()


if __name__ == "__main__":
    # Test the producer
    producer = KafkaDataProducer()
    count = producer.send_sample_data()
    print(f"Sent {count} records to Kafka")

