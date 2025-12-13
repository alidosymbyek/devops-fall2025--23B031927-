"""
Test script for Kafka stream processing
Tests both producer and consumer functionality
"""
import sys
from pathlib import Path
import time

# Add pipelines to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'pipelines'))

from stream.kafka_producer import KafkaDataProducer
from stream.kafka_processor import KafkaStreamProcessor


def test_kafka_producer():
    """Test Kafka producer"""
    print("=" * 60)
    print("Testing Kafka Producer")
    print("=" * 60)
    
    producer = KafkaDataProducer(
        bootstrap_servers='localhost:9092',
        topic='data-stream'
    )
    
    try:
        # Send sample data
        count = producer.send_sample_data()
        print(f"✓ Sent {count} records to Kafka")
        return count > 0
    except Exception as e:
        print(f"✗ Producer test failed: {e}")
        return False
    finally:
        producer.close()


def test_kafka_consumer():
    """Test Kafka consumer"""
    print("=" * 60)
    print("Testing Kafka Consumer")
    print("=" * 60)
    
    processor = KafkaStreamProcessor(
        bootstrap_servers='localhost:9092',
        topic='data-stream'
    )
    
    try:
        # Process stream batch
        result = processor.process_stream_batch(max_messages=10, timeout_ms=10000)
        print(f"✓ Processing result: {result}")
        return result.get('status') == 'success'
    except Exception as e:
        print(f"✗ Consumer test failed: {e}")
        return False
    finally:
        processor.close()


def test_full_pipeline():
    """Test full producer -> consumer pipeline"""
    print("=" * 60)
    print("Testing Full Kafka Pipeline")
    print("=" * 60)
    
    # Step 1: Produce data
    print("\n[1/2] Producing data to Kafka...")
    producer = KafkaDataProducer(
        bootstrap_servers='localhost:9092',
        topic='data-stream'
    )
    
    try:
        count = producer.send_sample_data()
        print(f"✓ Produced {count} records")
    finally:
        producer.close()
    
    # Wait a bit for messages to be available
    print("\nWaiting 2 seconds for messages to be available...")
    time.sleep(2)
    
    # Step 2: Consume and process
    print("\n[2/2] Consuming and processing from Kafka...")
    processor = KafkaStreamProcessor(
        bootstrap_servers='localhost:9092',
        topic='data-stream'
    )
    
    try:
        result = processor.process_stream_batch(max_messages=10, timeout_ms=10000)
        print(f"✓ Processed {result.get('processed', 0)} messages")
        print(f"  Total records: {result.get('total_records', 0)}")
        return result.get('status') == 'success' and result.get('processed', 0) > 0
    finally:
        processor.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Kafka Stream Processing Test Suite")
    print("=" * 60 + "\n")
    
    # Check if Kafka is running
    print("Note: Make sure Kafka is running (docker-compose up)")
    print("Waiting 5 seconds before starting tests...\n")
    time.sleep(5)
    
    # Run tests
    tests = [
        ("Producer Test", test_kafka_producer),
        ("Consumer Test", test_kafka_consumer),
        ("Full Pipeline Test", test_full_pipeline),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{'✓' if result else '✗'} {test_name}: {'PASSED' if result else 'FAILED'}\n")
        except Exception as e:
            print(f"\n✗ {test_name}: ERROR - {e}\n")
            results.append((test_name, False))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{'✓' if result else '✗'} {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

