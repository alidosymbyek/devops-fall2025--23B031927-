# 📧 Email Alerts Demonstration Guide

## Quick Start - Show Your Teacher

### Step 1: Run the Test

```bash
python test_email_alerts.py
```

This will send 3 test emails to demonstrate the system.

### Step 2: Check Your Email

Open your email inbox and show your teacher:
- ✅ Pipeline Failure Alert (red)
- ✅ Pipeline Success Alert (green)  
- ✅ Pipeline Delay Alert (orange)

## What the Email Looks Like

### Failure Alert Email

```
Subject: 🚨 Pipeline Failed: daily_etl

┌─────────────────────────────────────────┐
│  ⚠️ Pipeline Failure Alert              │
├─────────────────────────────────────────┤
│  Pipeline:     daily_etl               │
│  Status:        FAILED (red)            │
│  Time:          2025-12-19 10:00:00     │
│  Error:         Connection timeout...   │
│                                         │
│  Action Required: Check logs           │
│  [View in Airflow] button              │
└─────────────────────────────────────────┘
```

### Success Alert Email

```
Subject: ✅ Pipeline Success: daily_etl

┌─────────────────────────────────────────┐
│  ✅ Pipeline Completed Successfully     │
├─────────────────────────────────────────┤
│  Pipeline:     daily_etl               │
│  Status:        SUCCESS (green)         │
│  Records:       1,523                   │
│  Duration:      45.67 seconds          │
│                                         │
│  [View Dashboard] button               │
└─────────────────────────────────────────┘
```

## How It Works - Simple Explanation

1. **Pipeline Runs** → ETL process executes
2. **If Error Occurs** → Exception caught
3. **Alert Sent Immediately** → Email sent within seconds
4. **Email Received** → HTML formatted alert in inbox

## Code Flow

```python
# In etl_pipeline.py
try:
    # Run pipeline
    pipeline.run()
except Exception as e:
    # Send alert IMMEDIATELY (within seconds)
    alert_manager.send_pipeline_failure_alert(
        pipeline_name="daily_etl",
        error_message=str(e),
        execution_time="2025-12-19 10:00:00"
    )
```

## Key Points to Explain

1. ✅ **Immediate Alerts**: Sent within seconds (well under 2 minutes)
2. ✅ **HTML Formatted**: Professional-looking emails
3. ✅ **Detailed Information**: Error messages, timestamps, links
4. ✅ **Automatic**: No manual intervention needed
5. ✅ **Multiple Types**: Failure, Success, Delay alerts

## Configuration

Show your `.env` file:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL=your-email@gmail.com
ALERT_PASSWORD=your-app-password
RECIPIENT_EMAIL=recipient@example.com
```

## Testing Checklist

Before showing your teacher:

- [ ] Email credentials configured
- [ ] Test script runs successfully
- [ ] Emails received in inbox
- [ ] HTML formatting looks good
- [ ] Links work correctly

## Troubleshooting

**If emails don't send:**
1. Check `.env` file has correct credentials
2. For Gmail: Use App Password (not regular password)
3. Check internet connection
4. Verify SMTP settings

## What to Show Your Teacher

1. **Run the test**: `python test_email_alerts.py`
2. **Show the emails**: Open inbox and display
3. **Show the code**: `pipelines/monitoring/email_alerts.py`
4. **Show integration**: `pipelines/etl_pipeline.py` (line 117-121)
5. **Explain timing**: Alerts sent immediately (seconds, not minutes)

## Summary

The email alert system:
- ✅ Works automatically
- ✅ Sends alerts immediately
- ✅ Professional HTML formatting
- ✅ Includes all necessary information
- ✅ Meets 2-minute requirement (sends in seconds)

