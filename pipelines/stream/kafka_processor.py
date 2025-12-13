"""
Kafka Stream Processor for Real-Time Data Processing
Processes messages from Kafka topics and loads them to the database
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from loguru import logger
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from transform.data_transformer import DataTransformer
from load.data_loader import DataLoader


class KafkaStreamProcessor:
    """Process real-time data streams from Kafka"""
    
    def __init__(self, 
                 bootstrap_servers: str = 'localhost:9092',
                 consumer_group_id: str = 'dataplatform-etl-group',
                 topic: str = 'data-stream'):
        """
        Initialize Kafka Stream Processor
        
        Args:
            bootstrap_servers: Kafka broker addresses
            consumer_group_id: Consumer group ID for Kafka
            topic: Kafka topic to consume from
        """
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group_id = consumer_group_id
        self.topic = topic
        self.transformer = DataTransformer()
        self.loader = DataLoader()
        self.consumer = None
        self.producer = None
        
        # Setup logging
        log_path = Path(__file__).parent.parent.parent / 'logs'
        log_path.mkdir(exist_ok=True)
        logger.add(
            log_path / f"kafka_stream_{datetime.now().strftime('%Y%m%d')}.log",
            rotation="1 day",
            retention="30 days"
        )
    
    def create_consumer(self, auto_offset_reset: str = 'latest'):
        """Create Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                consumer_timeout_ms=5000  # 5 second timeout for batch processing
            )
            logger.info(f"✓ Kafka consumer created for topic: {self.topic}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create Kafka consumer: {e}")
            return False
    
    def create_producer(self):
        """Create Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3
            )
            logger.info(f"✓ Kafka producer created")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create Kafka producer: {e}")
            return False
    
    def process_message(self, message_value: Dict) -> bool:
        """
        Process a single message from Kafka
        
        Args:
            message_value: Decoded message value (dict)
            
        Returns:
            bool: True if processing succeeded
        """
        try:
            # Extract data from message
            source_name = message_value.get('source', 'kafka_stream')
            data = message_value.get('data', {})
            timestamp = message_value.get('timestamp', datetime.now().isoformat())
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                logger.warning(f"Unexpected data type: {type(data)}")
                return False
            
            if df.empty:
                logger.warning("Empty DataFrame from message")
                return False
            
            logger.info(f"Processing {len(df)} records from {source_name}")
            
            # Transform data
            transformed_df = self.transformer.transform(df, source_name)
            
            # Load to staging
            table_name = source_name.lower().replace('-', '_').replace(' ', '_')
            self.loader.load_to_staging(transformed_df, table_name)
            
            logger.info(f"✓ Successfully processed message from {source_name}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to process message: {e}")
            return False
    
    def process_stream_batch(self, max_messages: int = 100, timeout_ms: int = 5000) -> Dict:
        """
        Process a batch of messages from Kafka stream
        
        Args:
            max_messages: Maximum number of messages to process in one batch
            timeout_ms: Timeout in milliseconds for waiting for messages
            
        Returns:
            Dict with processing statistics
        """
        if not self.consumer:
            if not self.create_consumer():
                return {'status': 'error', 'message': 'Failed to create consumer'}
        
        start_time = datetime.now()
        processed_count = 0
        failed_count = 0
        total_records = 0
        
        try:
            logger.info(f"Starting stream batch processing (max: {max_messages} messages)")
            
            # Consume messages
            messages = self.consumer.poll(timeout_ms=timeout_ms)
            
            if not messages:
                logger.info("No messages available in stream")
                return {
                    'status': 'success',
                    'processed': 0,
                    'failed': 0,
                    'total_records': 0,
                    'duration_seconds': 0
                }
            
            # Process each partition's messages
            for topic_partition, partition_messages in messages.items():
                logger.info(f"Processing {len(partition_messages)} messages from partition {topic_partition.partition}")
                
                for message in partition_messages:
                    try:
                        if processed_count >= max_messages:
                            break
                        
                        # Process message
                        success = self.process_message(message.value)
                        
                        if success:
                            processed_count += 1
                            # Count records (approximate)
                            if isinstance(message.value.get('data'), list):
                                total_records += len(message.value.get('data', []))
                            else:
                                total_records += 1
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        failed_count += 1
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Stream Batch Processing Complete")
            logger.info(f"  Messages processed: {processed_count}")
            logger.info(f"  Messages failed: {failed_count}")
            logger.info(f"  Total records: {total_records}")
            logger.info(f"  Duration: {duration:.2f} seconds")
            logger.info(f"{'='*60}\n")
            
            # Log to database
            self.loader.log_pipeline_execution(
                pipeline_name='kafka_stream_processor',
                status='SUCCESS' if failed_count == 0 else 'PARTIAL',
                records_processed=total_records,
                start_time=start_time,
                end_time=end_time,
                error_message=None if failed_count == 0 else f"{failed_count} messages failed"
            )
            
            return {
                'status': 'success',
                'processed': processed_count,
                'failed': failed_count,
                'total_records': total_records,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"✗ Stream processing error: {e}")
            end_time = datetime.now()
            self.loader.log_pipeline_execution(
                pipeline_name='kafka_stream_processor',
                status='FAILED',
                records_processed=total_records,
                start_time=start_time,
                end_time=end_time,
                error_message=str(e)
            )
            return {
                'status': 'error',
                'message': str(e),
                'processed': processed_count,
                'failed': failed_count
            }
    
    def send_message(self, topic: str, data: Dict, source: str = 'api') -> bool:
        """
        Send a message to Kafka topic
        
        Args:
            topic: Kafka topic name
            data: Data to send (dict or list)
            source: Source identifier
            
        Returns:
            bool: True if sent successfully
        """
        if not self.producer:
            if not self.create_producer():
                return False
        
        try:
            message = {
                'source': source,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'processed': False
            }
            
            future = self.producer.send(topic, value=message)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"✓ Message sent to topic {topic}, partition {record_metadata.partition}, offset {record_metadata.offset}")
            return True
            
        except KafkaError as e:
            logger.error(f"✗ Kafka error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Failed to send message: {e}")
            return False
    
    def close(self):
        """Close consumer and producer connections"""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


def process_kafka_stream():
    """Main function for processing Kafka stream (called by Airflow)"""
    processor = KafkaStreamProcessor(
        bootstrap_servers='kafka:29092',  # Internal Docker network
        topic='data-stream'
    )
    
    try:
        result = processor.process_stream_batch(max_messages=100, timeout_ms=5000)
        return result
    finally:
        processor.close()


if __name__ == "__main__":
    # Test the processor
    processor = KafkaStreamProcessor()
    result = processor.process_stream_batch()
    print(f"Processing result: {result}")

