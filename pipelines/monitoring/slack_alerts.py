"""
Slack Alert Manager for Data Platform
Sends alerts to Slack webhook when pipelines fail or have delays
"""
import requests
import json
from loguru import logger
import os
from datetime import datetime


class SlackAlertManager:
    """Send alerts to Slack via webhook"""
    
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.channel = os.getenv('SLACK_CHANNEL', '#data-platform-alerts')
        self.enabled = bool(self.webhook_url)
        
        if not self.enabled:
            logger.warning("Slack webhook URL not configured. Slack alerts disabled.")
    
    def send_slack_message(self, message, color='danger'):
        """Send message to Slack"""
        if not self.enabled:
            logger.debug("Slack alerts disabled, skipping message")
            return False
        
        try:
            payload = {
                "channel": self.channel,
                "username": "Data Platform Monitor",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": color,
                        "text": message,
                        "footer": "Data Platform",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✓ Slack alert sent successfully")
                return True
            else:
                logger.error(f"✗ Failed to send Slack alert: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Failed to send Slack alert: {e}")
            return False
    
    def send_pipeline_failure_alert(self, pipeline_name, error_message, execution_time):
        """Send alert for pipeline failure"""
        message = f"""
🚨 *Pipeline Failure Alert*

*Pipeline:* {pipeline_name}
*Status:* FAILED
*Time:* {execution_time}
*Error:*
```
{error_message[:500]}  # Truncate long errors
```

*Action Required:* Please check the logs and investigate the issue.
<http://localhost:8080|View in Airflow>
"""
        return self.send_slack_message(message, color='danger')
    
    def send_pipeline_delay_alert(self, pipeline_name, expected_duration, actual_duration, threshold_percent=150):
        """Send alert for pipeline delay"""
        delay_percent = ((actual_duration - expected_duration) / expected_duration) * 100
        
        message = f"""
⏱️ *Pipeline Delay Alert*

*Pipeline:* {pipeline_name}
*Status:* DELAYED
*Expected Duration:* {expected_duration:.2f} seconds
*Actual Duration:* {actual_duration:.2f} seconds
*Delay:* {delay_percent:.1f}% over expected time

*Action Required:* Pipeline is taking longer than expected. Please investigate.
<http://localhost:8080|View in Airflow>
"""
        return self.send_slack_message(message, color='warning')
    
    def send_pipeline_success_alert(self, pipeline_name, records_processed, duration):
        """Send success notification (optional, can be disabled)"""
        # Only send success alerts if explicitly enabled
        if os.getenv('SLACK_SEND_SUCCESS_ALERTS', 'false').lower() == 'true':
            message = f"""
✅ *Pipeline Success*

*Pipeline:* {pipeline_name}
*Status:* SUCCESS
*Records Processed:* {records_processed:,}
*Duration:* {duration:.2f} seconds
*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<http://localhost:8501|View Dashboard>
"""
            return self.send_slack_message(message, color='good')
        return True

