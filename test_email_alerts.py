"""
Test Email Alert System
Demonstrates how email alerts work and sends a test email
"""
import os
from dotenv import load_dotenv
from datetime import datetime
import sys
from pathlib import Path

# Add pipelines to path
sys.path.append(str(Path(__file__).parent / 'pipelines'))

from monitoring.email_alerts import EmailAlertManager
from monitoring.slack_alerts import SlackAlertManager

# Load environment variables
load_dotenv()

def test_email_alerts():
    """Test and demonstrate email alert functionality"""
    
    print("=" * 60)
    print("EMAIL ALERT SYSTEM TEST")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Checking Configuration...")
    print("-" * 60)
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = os.getenv('SMTP_PORT', '587')
    alert_email = os.getenv('ALERT_EMAIL')
    recipient_email = os.getenv('RECIPIENT_EMAIL', alert_email)
    
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"Sender Email: {alert_email if alert_email else '❌ NOT CONFIGURED'}")
    print(f"Recipient Email: {recipient_email if recipient_email else '❌ NOT CONFIGURED'}")
    print()
    
    if not alert_email:
        print("❌ ERROR: ALERT_EMAIL not configured in .env file")
        print()
        print("To configure email alerts, add to your .env file:")
        print("  ALERT_EMAIL=your-email@gmail.com")
        print("  ALERT_PASSWORD=your-app-password")
        print("  RECIPIENT_EMAIL=recipient@example.com")
        print()
        print("For Gmail, use an App Password:")
        print("  https://support.google.com/accounts/answer/185833")
        return False
    
    # Initialize alert manager
    print("🔧 Initializing Email Alert Manager...")
    alert_manager = EmailAlertManager()
    print("✓ Email Alert Manager initialized")
    print()
    
    # Test 1: Pipeline Failure Alert
    print("📧 TEST 1: Sending Pipeline Failure Alert")
    print("-" * 60)
    
    test_pipeline_name = "daily_etl"
    test_error = "Connection timeout: Unable to connect to database after 30 seconds"
    test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Pipeline: {test_pipeline_name}")
    print(f"Error: {test_error}")
    print(f"Time: {test_time}")
    print()
    print("Sending email...")
    
    try:
        success = alert_manager.send_pipeline_failure_alert(
            test_pipeline_name,
            test_error,
            test_time
        )
        
        if success:
            print("✅ SUCCESS: Email alert sent successfully!")
            print(f"   Check your inbox: {recipient_email}")
        else:
            print("❌ FAILED: Could not send email alert")
            print("   Check your SMTP credentials and network connection")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("   Make sure your email credentials are correct")
    
    print()
    
    # Test 2: Pipeline Success Alert
    print("📧 TEST 2: Sending Pipeline Success Alert")
    print("-" * 60)
    
    test_records = 1523
    test_duration = 45.67
    
    print(f"Pipeline: {test_pipeline_name}")
    print(f"Records Processed: {test_records:,}")
    print(f"Duration: {test_duration:.2f} seconds")
    print()
    print("Sending email...")
    
    try:
        success = alert_manager.send_pipeline_success_alert(
            test_pipeline_name,
            test_records,
            test_duration
        )
        
        if success:
            print("✅ SUCCESS: Success email sent!")
            print(f"   Check your inbox: {recipient_email}")
        else:
            print("❌ FAILED: Could not send email")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print()
    
    # Test 3: Pipeline Delay Alert
    print("📧 TEST 3: Sending Pipeline Delay Alert")
    print("-" * 60)
    
    expected_duration = 300  # 5 minutes
    actual_duration = 525  # 8.75 minutes (75% delay)
    
    print(f"Pipeline: {test_pipeline_name}")
    print(f"Expected Duration: {expected_duration} seconds")
    print(f"Actual Duration: {actual_duration} seconds")
    print(f"Delay: {((actual_duration - expected_duration) / expected_duration) * 100:.1f}%")
    print()
    print("Sending email...")
    
    try:
        success = alert_manager.send_pipeline_delay_alert(
            test_pipeline_name,
            expected_duration,
            actual_duration
        )
        
        if success:
            print("✅ SUCCESS: Delay alert sent!")
            print(f"   Check your inbox: {recipient_email}")
        else:
            print("❌ FAILED: Could not send email")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print()
    print("📬 Check your email inbox for the test alerts!")
    print("   All emails should be HTML formatted with:")
    print("   - Pipeline information")
    print("   - Status and details")
    print("   - Links to Airflow/Dashboard")
    print()
    
    return True

def test_slack_alerts():
    """Test Slack alert functionality (optional)"""
    
    print()
    print("=" * 60)
    print("SLACK ALERT SYSTEM TEST (Optional)")
    print("=" * 60)
    print()
    
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    
    if not slack_webhook:
        print("ℹ️  Slack webhook not configured (optional)")
        print("   To enable Slack alerts, add to .env:")
        print("   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
        return
    
    print("📋 Slack Configuration:")
    print(f"   Webhook URL: {'✓ Configured' if slack_webhook else '❌ Not configured'}")
    print()
    
    slack_alerts = SlackAlertManager()
    
    if slack_alerts.enabled:
        print("📧 Sending test Slack alert...")
        success = slack_alerts.send_pipeline_failure_alert(
            "test_pipeline",
            "Test error message for demonstration",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        if success:
            print("✅ Slack alert sent successfully!")
        else:
            print("❌ Failed to send Slack alert")
    else:
        print("ℹ️  Slack alerts disabled (webhook not configured)")

if __name__ == "__main__":
    print()
    print("🚀 Starting Email Alert System Demonstration")
    print()
    
    # Test email alerts
    test_email_alerts()
    
    # Test Slack alerts (optional)
    test_slack_alerts()
    
    print()
    print("=" * 60)
    print("HOW IT WORKS")
    print("=" * 60)
    print()
    print("1. Pipeline Failure Detection:")
    print("   - When a pipeline fails, alerts are sent IMMEDIATELY")
    print("   - Both email and Slack notifications are sent")
    print("   - Alerts include error details and links")
    print()
    print("2. Automated Monitoring:")
    print("   - Airflow DAG runs every minute")
    print("   - Checks for failures in last 2 minutes")
    print("   - Sends alerts if issues detected")
    print()
    print("3. Delay Detection:")
    print("   - Monitors pipeline execution times")
    print("   - Alerts if pipeline exceeds 150% of expected time")
    print()
    print("4. Alert Content:")
    print("   - HTML formatted emails")
    print("   - Pipeline name and status")
    print("   - Error messages or metrics")
    print("   - Links to Airflow UI and Dashboard")
    print()

