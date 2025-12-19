# How Email Alerts Work - Demonstration Guide

## Overview

This guide explains how the email alerting system works and how to demonstrate it to your teacher.

## System Architecture

```
Pipeline Execution
    ↓
Failure/Error Detected
    ↓
EmailAlertManager.send_pipeline_failure_alert()
    ↓
SMTP Connection (Gmail/Email Server)
    ↓
Email Sent to Recipient
    ↓
Alert Delivered (within seconds)
```

## Components

### 1. EmailAlertManager (`pipelines/monitoring/email_alerts.py`)

**Responsibilities:**
- Connects to SMTP server (Gmail, Outlook, etc.)
- Formats HTML email alerts
- Sends alerts via email

**Key Methods:**
- `send_pipeline_failure_alert()` - Sends failure alerts
- `send_pipeline_success_alert()` - Sends success notifications
- `send_pipeline_delay_alert()` - Sends delay alerts

### 2. Integration Points

**In ETL Pipeline (`pipelines/etl_pipeline.py`):**
```python
except Exception as e:
    # Send alert immediately on failure
    self.alert_manager.send_pipeline_failure_alert(
        self.pipeline_name,
        str(e),
        execution_time
    )
```

**In Pipeline Monitor (`pipelines/monitoring/pipeline_monitor.py`):**
```python
# Checks for failures every minute
# Sends alerts if issues detected
monitor.check_recent_failures()
```

## How to Demonstrate

### Step 1: Run the Test Script

```bash
python test_email_alerts.py
```

This will:
1. Check your email configuration
2. Send 3 test emails:
   - Pipeline Failure Alert
   - Pipeline Success Alert
   - Pipeline Delay Alert
3. Show you what was sent

### Step 2: Show the Email in Your Inbox

1. Open your email client (Gmail, Outlook, etc.)
2. Check the inbox for the recipient email
3. You should see 3 HTML-formatted emails

### Step 3: Explain to Your Teacher

**What to Show:**

1. **Email Content:**
   - HTML formatted with colors
   - Pipeline name and status
   - Error details (for failures)
   - Links to Airflow UI and Dashboard

2. **Timing:**
   - Alerts sent immediately (within seconds)
   - Well under 2-minute requirement

3. **Configuration:**
   - Show `.env` file with email settings
   - Explain SMTP configuration

4. **Integration:**
   - Show how it's called in `etl_pipeline.py`
   - Show the monitoring DAG in Airflow

## Email Alert Examples

### Failure Alert

**Subject:** 🚨 Pipeline Failed: daily_etl

**Content:**
- Pipeline name
- Status: FAILED (red)
- Error message
- Execution time
- Link to Airflow UI

### Success Alert

**Subject:** ✅ Pipeline Success: daily_etl

**Content:**
- Pipeline name
- Status: SUCCESS (green)
- Records processed
- Duration
- Link to Dashboard

### Delay Alert

**Subject:** ⏱️ Pipeline Delay: daily_etl

**Content:**
- Pipeline name
- Status: DELAYED (orange)
- Expected vs. actual duration
- Delay percentage
- Link to Airflow UI

## Configuration Required

### For Gmail:

1. **Enable 2-Factor Authentication**
2. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Generate app password for "Mail"
   - Copy the 16-character password

3. **Add to `.env`:**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL=your-email@gmail.com
ALERT_PASSWORD=your-16-char-app-password
RECIPIENT_EMAIL=recipient@example.com
```

## Testing Checklist

- [ ] Email credentials configured in `.env`
- [ ] Test script runs without errors
- [ ] Emails received in inbox
- [ ] HTML formatting displays correctly
- [ ] Links work (Airflow, Dashboard)
- [ ] All 3 alert types sent successfully

## Troubleshooting

### "Email credentials not configured"
- Check `.env` file exists
- Verify `ALERT_EMAIL` and `ALERT_PASSWORD` are set

### "Failed to send email"
- Check SMTP credentials
- For Gmail: Use App Password, not regular password
- Check internet connection
- Verify SMTP server and port

### "No emails received"
- Check spam/junk folder
- Verify recipient email address
- Check email server logs
- Test with a simple email client first

## Key Points to Explain

1. **Immediate Alerts:**
   - Alerts sent within seconds of failure
   - Well under 2-minute requirement

2. **Multiple Channels:**
   - Email alerts (HTML formatted)
   - Slack alerts (optional)

3. **Automated Monitoring:**
   - Airflow DAG checks every minute
   - Detects failures and delays automatically

4. **Rich Content:**
   - HTML formatted emails
   - Error details included
   - Links to monitoring tools

## Code Flow Example

```python
# 1. Pipeline fails
try:
    # ... pipeline code ...
except Exception as e:
    # 2. Alert sent immediately
    alert_manager.send_pipeline_failure_alert(
        pipeline_name="daily_etl",
        error_message=str(e),
        execution_time="2025-12-19 10:00:00"
    )
    # 3. Email sent via SMTP
    # 4. Recipient receives email within seconds
```

## Demonstration Script

Run this to show your teacher:

```bash
# 1. Show configuration
cat .env | grep -E "ALERT|SMTP|RECIPIENT"

# 2. Run test
python test_email_alerts.py

# 3. Show code
cat pipelines/etl_pipeline.py | grep -A 10 "send_pipeline_failure_alert"

# 4. Check Airflow DAG
# Open http://localhost:8080 and show pipeline_health_monitoring DAG
```

## Summary

The email alerting system:
- ✅ Sends alerts immediately on pipeline failures
- ✅ Sends alerts for pipeline delays
- ✅ HTML formatted with detailed information
- ✅ Includes links to monitoring tools
- ✅ Well under 2-minute requirement (sends in seconds)
- ✅ Integrated with ETL pipeline and monitoring system

