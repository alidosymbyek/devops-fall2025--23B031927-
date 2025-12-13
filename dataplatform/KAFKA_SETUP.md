# Kafka Real-Time Stream Processing Setup Guide

## Overview

This guide explains how to set up and use the Kafka-based real-time stream processing system.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Data Source │────▶│ Kafka Topic  │────▶│ Stream      │────▶│ PostgreSQL   │
│ (API/CSV)   │     │ (data-stream)│     │ Processor   │     │ Database     │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
     │                     │                     │
     │                     │                     │
     └─────────────────────┴─────────────────────┘
                    Airflow DAGs
          (Every 5 minutes)
```

## Components

### 1. Kafka Infrastructure
- **Zookeeper**: Coordinates Kafka brokers
- **Kafka**: Message broker for streaming data
- **Topic**: `data-stream` (auto-created)

### 2. Producer (`kafka_producer.py`)
- Ingests data from APIs/CSV
- Sends data to Kafka topic
- Runs via `kafka_data_ingestion_dag` (every 5 minutes)

### 3. Consumer (`kafka_processor.py`)
- Consumes messages from Kafka
- Transforms and loads data to database
- Runs via `stream_processing_dag` (every 5 minutes)

## Setup Instructions

### Step 1: Start Services

```bash
# Start all services including Kafka
docker-compose -f docker-compose-airflow.yml up -d

# Check Kafka is running
docker ps | grep kafka
```

### Step 2: Verify Kafka

```bash
# Check Kafka logs
docker logs kafka

# List Kafka topics (from inside container)
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Step 3: Enable DAGs in Airflow

1. Open Airflow UI: http://localhost:8080
2. Login: admin/admin123
3. Enable these DAGs:
   - `kafka_data_ingestion` - Ingests data to Kafka
   - `stream_processing_pipeline` - Processes Kafka streams

### Step 4: Test the System

```bash
# Run test script
python tests/test_kafka_stream.py
```

## Usage

### Manual Testing

#### Send Data to Kafka

```python
from pipelines.stream.kafka_producer import KafkaDataProducer

producer = KafkaDataProducer(
    bootstrap_servers='localhost:9092',
    topic='data-stream'
)

# Send sample data
count = producer.send_sample_data()
print(f"Sent {count} records")

producer.close()
```

#### Process Kafka Stream

```python
from pipelines.stream.kafka_processor import KafkaStreamProcessor

processor = KafkaStreamProcessor(
    bootstrap_servers='localhost:9092',
    topic='data-stream'
)

# Process batch of messages
result = processor.process_stream_batch(max_messages=100, timeout_ms=5000)
print(result)

processor.close()
```

### Automated Processing

The system runs automatically via Airflow:

1. **Every 5 minutes**: `kafka_data_ingestion` DAG ingests data from APIs
2. **Every 5 minutes**: `stream_processing_pipeline` DAG processes Kafka messages

## Configuration

### Kafka Connection

- **External (from host)**: `localhost:9092`
- **Internal (Docker)**: `kafka:29092`

### Topic Configuration

- **Topic Name**: `data-stream`
- **Auto-creation**: Enabled
- **Replication Factor**: 1 (single broker)
- **Partitions**: Default (1)

### Message Format

```json
{
  "source": "api_users",
  "data": [
    {"id": 1, "name": "John", ...},
    {"id": 2, "name": "Jane", ...}
  ],
  "timestamp": "2025-12-13T10:30:00",
  "batch_size": 2,
  "processed": false
}
```

## Monitoring

### Check Kafka Topics

```bash
# List topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Describe topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
  --describe --topic data-stream

# Check consumer groups
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list
```

### Check Message Count

```bash
# Get topic offset (message count)
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic data-stream
```

### View Logs

```bash
# Kafka logs
docker logs kafka

# Stream processor logs
tail -f logs/kafka_stream_*.log

# Producer logs
tail -f logs/kafka_producer_*.log
```

## Troubleshooting

### Kafka Not Starting

```bash
# Check Zookeeper is running
docker ps | grep zookeeper

# Check Kafka logs
docker logs kafka

# Restart Kafka
docker restart kafka
```

### No Messages Being Processed

1. Check DAGs are enabled in Airflow
2. Check DAG runs are successful
3. Verify Kafka topic has messages:
   ```bash
   docker exec kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic data-stream \
     --from-beginning
   ```

### Connection Errors

- **From host**: Use `localhost:9092`
- **From Docker**: Use `kafka:29092`
- Check firewall/network settings

## Performance Tuning

### Batch Size

Adjust in `kafka_processor.py`:
```python
result = processor.process_stream_batch(
    max_messages=100,  # Increase for more throughput
    timeout_ms=5000    # Increase for longer wait
)
```

### Consumer Settings

Modify in `kafka_processor.py`:
```python
self.consumer = KafkaConsumer(
    ...
    fetch_min_bytes=1024,      # Wait for at least 1KB
    fetch_max_wait_ms=500,     # Max wait time
    max_poll_records=100        # Max records per poll
)
```

## Latency Requirements

- **Target**: < 5 minutes data refresh latency
- **Current**: 5-minute DAG schedule
- **Actual**: Messages processed within 5 minutes of ingestion

## Next Steps

1. ✅ Kafka infrastructure set up
2. ✅ Producer and consumer implemented
3. ✅ Airflow DAGs created
4. ⏭️ Add more data sources
5. ⏭️ Implement error handling and retries
6. ⏭️ Add monitoring dashboards

---

*Last Updated: 2025-12-13*

