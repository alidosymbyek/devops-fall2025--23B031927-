"""
Pipeline Health Monitor
Monitors pipeline execution times and detects delays/failures
Sends alerts within 2 minutes of detection
"""
from datetime import datetime, timedelta
from loguru import logger
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))
from db_connector import DatabaseConnector
from monitoring.email_alerts import EmailAlertManager
from monitoring.slack_alerts import SlackAlertManager


class PipelineMonitor:
    """Monitor pipeline health and detect delays/failures"""
    
    def __init__(self):
        self.db = DatabaseConnector()
        self.email_alerts = EmailAlertManager()
        self.slack_alerts = SlackAlertManager()
        
        # Pipeline performance thresholds (in seconds)
        # Can be configured per pipeline
        self.pipeline_thresholds = {
            'daily_etl': 300,  # 5 minutes
            'airflow_daily_etl': 300,
            'kafka_data_ingestion': 600,  # 10 minutes
            'stream_processing': 180,  # 3 minutes
            'default': 600  # 10 minutes default
        }
        
        # Delay threshold: alert if pipeline takes 150% of expected time
        self.delay_threshold_percent = 150
        
        # Alert window: check for failures/delays within last 2 minutes
        self.alert_check_window = timedelta(minutes=2)
    
    def get_pipeline_threshold(self, pipeline_name):
        """Get expected duration threshold for a pipeline"""
        return self.pipeline_thresholds.get(
            pipeline_name.lower(),
            self.pipeline_thresholds['default']
        )
    
    def check_recent_failures(self):
        """Check for pipeline failures in the last 2 minutes and send alerts"""
        try:
            cutoff_time = datetime.now() - self.alert_check_window
            
            # Ensure alert columns exist first
            self._ensure_alert_columns()
            
            query = text("""
                SELECT 
                    log_id,
                    pipeline_name,
                    status,
                    start_time,
                    end_time,
                    records_processed,
                    error_message,
                    created_at
                FROM warehouse.pipeline_logs
                WHERE status = 'FAILED'
                AND created_at >= :cutoff_time
                AND (alert_sent IS NULL OR alert_sent = FALSE)
                ORDER BY created_at DESC
            """)
            
            with self.db.get_engine().connect() as conn:
                results = conn.execute(query, {'cutoff_time': cutoff_time}).fetchall()
                
                for row in results:
                    log_id, pipeline_name, status, start_time, end_time, records, error, created_at = row
                    
                    execution_time = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Send alerts immediately
                    logger.warning(f"🚨 Pipeline failure detected: {pipeline_name} at {execution_time}")
                    
                    # Send email alert
                    self.email_alerts.send_pipeline_failure_alert(
                        pipeline_name,
                        error or "Unknown error",
                        execution_time
                    )
                    
                    # Send Slack alert
                    self.slack_alerts.send_pipeline_failure_alert(
                        pipeline_name,
                        error or "Unknown error",
                        execution_time
                    )
                    
                    # Mark alert as sent
                    self._mark_alert_sent(log_id)
                    
                    logger.info(f"✓ Alerts sent for failed pipeline: {pipeline_name}")
        
        except Exception as e:
            logger.error(f"Error checking for failures: {e}")
    
    def check_pipeline_delays(self):
        """Check for pipeline delays and send alerts"""
        try:
            # Ensure alert columns exist first
            self._ensure_alert_columns()
            
            # Get recent successful pipeline executions
            cutoff_time = datetime.now() - timedelta(hours=24)  # Check last 24 hours
            
            query = text("""
                SELECT 
                    log_id,
                    pipeline_name,
                    start_time,
                    end_time,
                    EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds,
                    created_at
                FROM warehouse.pipeline_logs
                WHERE status = 'SUCCESS'
                AND created_at >= :cutoff_time
                AND (delay_alert_sent IS NULL OR delay_alert_sent = FALSE)
                ORDER BY created_at DESC
            """)
            
            with self.db.get_engine().connect() as conn:
                results = conn.execute(query, {'cutoff_time': cutoff_time}).fetchall()
                
                for row in results:
                    log_id, pipeline_name, start_time, end_time, duration, created_at = row
                    
                    if duration is None:
                        continue
                    
                    expected_duration = self.get_pipeline_threshold(pipeline_name)
                    delay_threshold = expected_duration * (self.delay_threshold_percent / 100)
                    
                    # Check if pipeline exceeded delay threshold
                    if duration > delay_threshold:
                        logger.warning(
                            f"⏱️ Pipeline delay detected: {pipeline_name} "
                            f"took {duration:.2f}s (expected: {expected_duration}s)"
                        )
                        
                        # Send alerts
                        self.email_alerts.send_pipeline_delay_alert(
                            pipeline_name,
                            expected_duration,
                            duration,
                            self.delay_threshold_percent
                        )
                        
                        self.slack_alerts.send_pipeline_delay_alert(
                            pipeline_name,
                            expected_duration,
                            duration,
                            self.delay_threshold_percent
                        )
                        
                        # Mark delay alert as sent
                        self._mark_delay_alert_sent(log_id)
                        
                        logger.info(f"✓ Delay alerts sent for pipeline: {pipeline_name}")
        
        except Exception as e:
            logger.error(f"Error checking for delays: {e}")
    
    def _mark_alert_sent(self, log_id):
        """Mark that an alert has been sent for a log entry"""
        try:
            # First, ensure the column exists
            self._ensure_alert_columns()
            
            update_query = text("""
                UPDATE warehouse.pipeline_logs
                SET alert_sent = TRUE,
                    alert_sent_at = :alert_time
                WHERE log_id = :log_id
            """)
            
            with self.db.get_engine().begin() as conn:
                conn.execute(update_query, {
                    'log_id': log_id,
                    'alert_time': datetime.now()
                })
        except Exception as e:
            logger.warning(f"Could not mark alert as sent: {e}")
    
    def _mark_delay_alert_sent(self, log_id):
        """Mark that a delay alert has been sent"""
        try:
            self._ensure_alert_columns()
            
            update_query = text("""
                UPDATE warehouse.pipeline_logs
                SET delay_alert_sent = TRUE,
                    delay_alert_sent_at = :alert_time
                WHERE log_id = :log_id
            """)
            
            with self.db.get_engine().begin() as conn:
                conn.execute(update_query, {
                    'log_id': log_id,
                    'alert_time': datetime.now()
                })
        except Exception as e:
            logger.warning(f"Could not mark delay alert as sent: {e}")
    
    def _ensure_alert_columns(self):
        """Ensure alert tracking columns exist in pipeline_logs table"""
        try:
            alter_queries = [
                "ALTER TABLE warehouse.pipeline_logs ADD COLUMN IF NOT EXISTS alert_sent BOOLEAN DEFAULT FALSE",
                "ALTER TABLE warehouse.pipeline_logs ADD COLUMN IF NOT EXISTS alert_sent_at TIMESTAMP",
                "ALTER TABLE warehouse.pipeline_logs ADD COLUMN IF NOT EXISTS delay_alert_sent BOOLEAN DEFAULT FALSE",
                "ALTER TABLE warehouse.pipeline_logs ADD COLUMN IF NOT EXISTS delay_alert_sent_at TIMESTAMP"
            ]
            
            with self.db.get_engine().begin() as conn:
                for query in alter_queries:
                    try:
                        conn.execute(text(query))
                    except Exception as e:
                        # Column might already exist, ignore
                        logger.debug(f"Column may already exist: {e}")
        except Exception as e:
            logger.warning(f"Could not ensure alert columns exist: {e}")
    
    def monitor_pipelines(self):
        """Main monitoring function - checks for failures and delays"""
        logger.info("Starting pipeline health monitoring...")
        
        # Check for failures (within 2 minutes)
        self.check_recent_failures()
        
        # Check for delays
        self.check_pipeline_delays()
        
        logger.info("Pipeline health monitoring complete")


def main():
    """Run pipeline monitoring"""
    monitor = PipelineMonitor()
    monitor.monitor_pipelines()


if __name__ == "__main__":
    main()

