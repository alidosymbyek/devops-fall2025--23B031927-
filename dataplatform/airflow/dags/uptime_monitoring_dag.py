"""
Uptime Monitoring DAG
Monitors platform health and tracks uptime (target: 99.5%)
Runs every 5 minutes to check service health
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add pipelines to path
sys.path.insert(0, '/opt/airflow/pipelines')

from monitoring.health_checker import HealthChecker
from monitoring.uptime_tracker import UptimeTracker
from monitoring.email_alerts import EmailAlertManager

default_args = {
    'owner': 'ali',
    'depends_on_past': False,
    'start_date': datetime(2025, 12, 1),
    'email': ['ali@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def check_platform_health():
    """Check health of all platform services"""
    from loguru import logger
    
    logger.info("Starting platform health check...")
    checker = HealthChecker()
    health_results = checker.get_overall_health()
    
    logger.info(f"Overall Status: {health_results['overall_status']}")
    logger.info(f"Uptime: {health_results['uptime_percentage']:.2f}%")
    logger.info(f"Healthy Services: {health_results['healthy_services']}/{health_results['total_services']}")
    
    return health_results

def track_uptime(**context):
    """Track uptime and log results"""
    from loguru import logger
    
    # Get health check results from previous task
    health_results = context['ti'].xcom_pull(task_ids='check_health')
    
    if health_results:
        logger.info("Logging health check results...")
        tracker = UptimeTracker()
        tracker.log_health_check(health_results)
        
        # Calculate daily uptime
        daily_stats = tracker.calculate_daily_uptime()
        
        if daily_stats:
            uptime_pct = daily_stats.get('uptime_percentage', 0)
            logger.info(f"Daily Uptime: {uptime_pct:.2f}%")
        else:
            logger.warning("No uptime data available yet (first run or no data)")
            daily_stats = {
                'date': str(datetime.now().date()),
                'total_checks': 0,
                'uptime_percentage': 0,
                'status': 'no_data'
            }
        
        return daily_stats
    else:
        logger.warning("No health check results available")
        return None

def check_uptime_target(**context):
    """Check if uptime meets 99.5% target and send alerts if needed"""
    from loguru import logger
    
    daily_stats = context['ti'].xcom_pull(task_ids='track_uptime')
    
    if daily_stats and daily_stats.get('status') != 'no_data':
        uptime_pct = daily_stats.get('uptime_percentage', 0)
        target = daily_stats.get('target_uptime', 99.5)
        
        if uptime_pct < target:
            logger.warning(f"⚠️ Uptime below target: {uptime_pct:.2f}% < {target}%")
            
            # Send alert if configured
            try:
                alert_manager = EmailAlertManager()
                subject = f"⚠️ Uptime Alert: {uptime_pct:.2f}% (Target: {target}%)"
                body = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #ff9800;">⚠️ Uptime Below Target</h2>
                    <table style="border-collapse: collapse; width: 100%;">
                        <tr>
                            <td style="padding: 8px; background-color: #f5f5f5;"><strong>Current Uptime:</strong></td>
                            <td style="padding: 8px; color: #ff9800;"><strong>{uptime_pct:.2f}%</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; background-color: #f5f5f5;"><strong>Target Uptime:</strong></td>
                            <td style="padding: 8px;">{target}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; background-color: #f5f5f5;"><strong>Gap:</strong></td>
                            <td style="padding: 8px; color: #d32f2f;">{target - uptime_pct:.2f}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; background-color: #f5f5f5;"><strong>Date:</strong></td>
                            <td style="padding: 8px;">{daily_stats.get('date', 'N/A')}</td>
                        </tr>
                    </table>
                    <p style="margin-top: 20px;">
                        <strong>Action Required:</strong> Investigate service health issues.
                    </p>
                </body>
                </html>
                """
                alert_manager.send_email(subject, body)
            except Exception as e:
                logger.warning(f"Failed to send uptime alert: {e}")
        else:
            logger.info(f"✅ Uptime meets target: {uptime_pct:.2f}% >= {target}%")
    
    return daily_stats

with DAG(
    'uptime_monitoring',
    default_args=default_args,
    description='Monitor platform uptime and health (target: 99.5%)',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    catchup=False,
    tags=['monitoring', 'uptime', 'health'],
    max_active_runs=1,
) as dag:
    
    # Task 1: Check platform health
    check_health = PythonOperator(
        task_id='check_health',
        python_callable=check_platform_health,
    )
    
    # Task 2: Track uptime
    track_uptime_task = PythonOperator(
        task_id='track_uptime',
        python_callable=track_uptime,
    )
    
    # Task 3: Check if target is met
    check_target = PythonOperator(
        task_id='check_uptime_target',
        python_callable=check_uptime_target,
    )
    
    # Set task dependencies
    check_health >> track_uptime_task >> check_target

