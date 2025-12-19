# Monitoring and Alerts Setup Guide

## Overview

The Data Platform includes comprehensive monitoring and alerting capabilities that:
- ✅ Monitor pipeline health automatically
- ✅ Detect pipeline failures and send alerts within 2 minutes
- ✅ Detect pipeline delays and send alerts
- ✅ Support both Email and Slack notifications

## Features

### 1. Automated Pipeline Monitoring
- **Pipeline Health Monitor**: Runs every minute via Airflow DAG
- **Failure Detection**: Checks for failed pipelines within the last 2 minutes
- **Delay Detection**: Monitors pipeline execution times and alerts if they exceed thresholds

### 2. Alert Channels

#### Email Alerts
- Configured via environment variables
- Sends HTML-formatted alerts with detailed information
- Includes links to Airflow UI and Dashboard

#### Slack Alerts
- Configured via Slack webhook URL
- Sends formatted messages to Slack channels
- Supports custom channels and formatting

### 3. Alert Timing
- **Failure Alerts**: Sent immediately when pipeline fails (within seconds)
- **Delay Alerts**: Sent when pipeline exceeds 150% of expected duration
- **Monitoring Frequency**: Checks every minute via Airflow DAG

## Configuration

### Email Configuration

Add to your `.env` file:

```bash
# Email Alert Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL=your-email@gmail.com
ALERT_PASSWORD=your-app-password
RECIPIENT_EMAIL=recipient@example.com
```

**Note**: For Gmail, you need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

### Slack Configuration

1. **Create a Slack Webhook**:
   - Go to https://api.slack.com/apps
   - Create a new app or use an existing one
   - Go to "Incoming Webhooks" and activate it
   - Create a webhook for your channel
   - Copy the webhook URL

2. **Add to `.env` file**:
```bash
# Slack Alert Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#data-platform-alerts
SLACK_SEND_SUCCESS_ALERTS=false  # Set to 'true' to also send success notifications
```

### Pipeline Thresholds

Pipeline execution time thresholds are configured in `pipelines/monitoring/pipeline_monitor.py`:

```python
self.pipeline_thresholds = {
    'daily_etl': 300,  # 5 minutes
    'airflow_daily_etl': 300,
    'kafka_data_ingestion': 600,  # 10 minutes
    'stream_processing': 180,  # 3 minutes
    'default': 600  # 10 minutes default
}
```

Alerts are sent when a pipeline exceeds **150%** of its threshold.

## How It Works

### 1. Immediate Failure Alerts

When a pipeline fails, alerts are sent immediately:

```python
# In etl_pipeline.py
except Exception as e:
    # Send email alert immediately
    self.alert_manager.send_pipeline_failure_alert(...)
    
    # Send Slack alert immediately
    slack_alerts.send_pipeline_failure_alert(...)
```

### 2. Automated Monitoring DAG

The `pipeline_health_monitoring` DAG runs every minute:

1. Checks for failures in the last 2 minutes
2. Checks for delays in successful pipelines
3. Sends alerts if issues are detected
4. Marks alerts as sent to prevent duplicates

### 3. Delay Detection

The monitor:
- Compares actual execution time vs. expected threshold
- Alerts if pipeline takes >150% of expected time
- Only alerts once per pipeline execution

## Testing

### Test Email Alerts

```python
from pipelines.monitoring.email_alerts import EmailAlertManager

alert_manager = EmailAlertManager()
alert_manager.send_pipeline_failure_alert(
    'test_pipeline',
    'Test error message',
    '2025-12-19 10:00:00'
)
```

### Test Slack Alerts

```python
from pipelines.monitoring.slack_alerts import SlackAlertManager

slack = SlackAlertManager()
slack.send_pipeline_failure_alert(
    'test_pipeline',
    'Test error message',
    '2025-12-19 10:00:00'
)
```

### Test Pipeline Monitor

```bash
cd pipelines
python -m monitoring.pipeline_monitor
```

## Airflow DAG

The monitoring DAG (`pipeline_health_monitoring`) is automatically loaded when Airflow starts. It:
- Runs every minute
- Checks for failures and delays
- Sends alerts as needed
- Logs all monitoring activities

## Alert Content

### Failure Alert Includes:
- Pipeline name
- Failure status
- Error message
- Execution time
- Link to Airflow UI

### Delay Alert Includes:
- Pipeline name
- Expected vs. actual duration
- Delay percentage
- Link to Airflow UI

## Troubleshooting

### Alerts Not Sending

1. **Check Environment Variables**:
   ```bash
   echo $ALERT_EMAIL
   echo $SLACK_WEBHOOK_URL
   ```

2. **Check Logs**:
   ```bash
   tail -f logs/daily_etl_*.log
   ```

3. **Test Connections**:
   - Email: Check SMTP credentials
   - Slack: Verify webhook URL is correct

### Monitoring DAG Not Running

1. Check Airflow UI: http://localhost:8080
2. Verify DAG is enabled
3. Check DAG logs for errors

## Acceptance Criteria Status

| Criteria | Status |
|----------|--------|
| Automated monitoring for pipeline health | ✅ Complete |
| Alerting on job failures | ✅ Complete (within seconds) |
| Alerting on job delays | ✅ Complete |
| Alerts sent via email | ✅ Complete |
| Alerts sent via Slack | ✅ Complete |
| Alerts sent within 2 minutes | ✅ Complete (sent immediately) |

## Next Steps

1. Configure email credentials in `.env`
2. Set up Slack webhook (optional)
3. Enable the `pipeline_health_monitoring` DAG in Airflow
4. Test with a sample pipeline failure
5. Monitor alert delivery

