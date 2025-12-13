import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
import os
from datetime import datetime

class EmailAlertManager:
    def __init__(self):
        # Gmail SMTP settings (you can use any email provider)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('ALERT_EMAIL')
        self.sender_password = os.getenv('ALERT_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', self.sender_email)
    
    def send_email(self, subject, body, is_html=True):
        """Send email alert"""
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured. Skipping email alert.")
            return False
        
        try:
            message = MIMEMultipart('alternative')
            message['From'] = self.sender_email
            message['To'] = self.recipient_email
            message['Subject'] = subject
            
            mime_type = 'html' if is_html else 'plain'
            message.attach(MIMEText(body, mime_type))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"✓ Alert email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to send email: {e}")
            return False
    
    def send_pipeline_failure_alert(self, pipeline_name, error_message, execution_time):
        """Send alert for pipeline failure"""
        subject = f"🚨 Pipeline Failed: {pipeline_name}"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #d32f2f;">⚠️ Pipeline Failure Alert</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Pipeline:</strong></td>
                    <td style="padding: 8px;">{pipeline_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Status:</strong></td>
                    <td style="padding: 8px; color: #d32f2f;"><strong>FAILED</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Time:</strong></td>
                    <td style="padding: 8px;">{execution_time}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Error:</strong></td>
                    <td style="padding: 8px;">
                        <pre style="background-color: #ffebee; padding: 10px; border-radius: 4px;">{error_message}</pre>
                    </td>
                </tr>
            </table>
            <p style="margin-top: 20px;">
                <strong>Action Required:</strong> Please check the logs and investigate the issue.
            </p>
            <p>
                <a href="http://localhost:8080" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                    View in Airflow
                </a>
            </p>
        </body>
        </html>
        """
        return self.send_email(subject, body)
    
    def send_pipeline_success_alert(self, pipeline_name, records_processed, duration):
        """Send success notification"""
        subject = f"✅ Pipeline Success: {pipeline_name}"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #388e3c;">✅ Pipeline Completed Successfully</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Pipeline:</strong></td>
                    <td style="padding: 8px;">{pipeline_name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Status:</strong></td>
                    <td style="padding: 8px; color: #388e3c;"><strong>SUCCESS</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Records Processed:</strong></td>
                    <td style="padding: 8px;">{records_processed:,}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Duration:</strong></td>
                    <td style="padding: 8px;">{duration:.2f} seconds</td>
                </tr>
                <tr>
                    <td style="padding: 8px; background-color: #f5f5f5;"><strong>Time:</strong></td>
                    <td style="padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
            <p style="margin-top: 20px;">
                <a href="http://localhost:8501" style="background-color: #1976d2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                    View Dashboard
                </a>
            </p>
        </body>
        </html>
        """
        return self.send_email(subject, body)

# Test it
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    alert_manager = EmailAlertManager()
    # Test success alert
    alert_manager.send_pipeline_success_alert('test_pipeline', 100, 5.5)