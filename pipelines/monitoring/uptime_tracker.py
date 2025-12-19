"""
Uptime Tracker for Data Platform
Tracks and calculates uptime percentage (target: 99.5%)
"""
from datetime import datetime, timedelta
from loguru import logger
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from db_connector import DatabaseConnector


class UptimeTracker:
    """Track and calculate platform uptime"""
    
    def __init__(self):
        self.db = DatabaseConnector()
        self.target_uptime = 99.5  # Target uptime percentage
        self._ensure_uptime_table()
    
    def _ensure_uptime_table(self):
        """Create uptime tracking table if it doesn't exist"""
        from sqlalchemy import text
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS monitoring.uptime_log (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            service_name VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL,
            response_time_ms FLOAT,
            error_message TEXT,
            overall_health VARCHAR(20)
        );
        
        CREATE INDEX IF NOT EXISTS idx_uptime_timestamp ON monitoring.uptime_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_uptime_service ON monitoring.uptime_log(service_name);
        
        CREATE TABLE IF NOT EXISTS monitoring.uptime_summary (
            id SERIAL PRIMARY KEY,
            date DATE NOT NULL UNIQUE,
            total_checks INTEGER DEFAULT 0,
            healthy_checks INTEGER DEFAULT 0,
            unhealthy_checks INTEGER DEFAULT 0,
            uptime_percentage FLOAT,
            target_uptime FLOAT DEFAULT 99.5,
            status VARCHAR(20),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_summary_date ON monitoring.uptime_summary(date);
        """
        
        try:
            engine = self.db.get_engine()
            with engine.begin() as conn:
                # Ensure monitoring schema exists
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS monitoring"))
                
                # Create tables
                for statement in create_table_sql.strip().split(';'):
                    if statement.strip():
                        conn.execute(text(statement))
            
            logger.info("✓ Uptime tracking tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create uptime tables: {e}")
            raise
    
    def log_health_check(self, health_results):
        """Log health check results"""
        try:
            with self.db.get_engine().connect() as conn:
                overall_status = health_results.get('overall_status', 'unknown')
                
                # Log individual services
                for service_name, result in health_results.get('services', {}).items():
                    insert_sql = """
                    INSERT INTO monitoring.uptime_log 
                    (timestamp, service_name, status, response_time_ms, error_message, overall_health)
                    VALUES (:ts, :svc, :stat, :rt, :err, :overall)
                    """
                    
                    from sqlalchemy import text
                    conn.execute(text(insert_sql), {
                        'ts': datetime.now(),
                        'svc': service_name,
                        'stat': result.get('status', 'unknown'),
                        'rt': result.get('response_time_ms'),
                        'err': result.get('error'),
                        'overall': overall_status
                    })
                
                conn.commit()
                logger.debug(f"Logged health check: {overall_status}")
        except Exception as e:
            logger.error(f"Failed to log health check: {e}")
    
    def calculate_daily_uptime(self, date=None):
        """Calculate uptime percentage for a specific date"""
        if date is None:
            date = datetime.now().date()
        
        try:
            from sqlalchemy import text
            with self.db.get_engine().connect() as conn:
                # Get all checks for the date
                query = text("""
                SELECT 
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_checks,
                    SUM(CASE WHEN status != 'healthy' THEN 1 ELSE 0 END) as unhealthy_checks
                FROM monitoring.uptime_log
                WHERE timestamp::date = :check_date
                """)
                
                result = conn.execute(query, {'check_date': date}).fetchone()
                
                if result and result[0] > 0:
                    total = result[0]
                    healthy = result[1] or 0
                    uptime_pct = (healthy / total) * 100
                    
                    # Update summary
                    upsert_sql = """
                    INSERT INTO monitoring.uptime_summary 
                    (date, total_checks, healthy_checks, unhealthy_checks, uptime_percentage, status, last_updated)
                    VALUES (:check_date, :total, :healthy, :unhealthy, :uptime, :status_val, :updated)
                    ON CONFLICT (date) 
                    DO UPDATE SET
                        total_checks = EXCLUDED.total_checks,
                        healthy_checks = EXCLUDED.healthy_checks,
                        unhealthy_checks = EXCLUDED.unhealthy_checks,
                        uptime_percentage = EXCLUDED.uptime_percentage,
                        status = EXCLUDED.status,
                        last_updated = EXCLUDED.last_updated
                    """
                    
                    status = 'meeting_target' if uptime_pct >= self.target_uptime else 'below_target'
                    
                    from sqlalchemy import text
                    conn.execute(text(upsert_sql), {
                        'check_date': date, 
                        'total': total, 
                        'healthy': healthy, 
                        'unhealthy': result[2] or 0, 
                        'uptime': uptime_pct, 
                        'status_val': status, 
                        'updated': datetime.now()
                    })
                    conn.commit()
                    
                    return {
                        'date': str(date),
                        'total_checks': total,
                        'healthy_checks': healthy,
                        'unhealthy_checks': result[2] or 0,
                        'uptime_percentage': uptime_pct,
                        'target_uptime': self.target_uptime,
                        'status': status,
                        'meeting_target': uptime_pct >= self.target_uptime
                    }
                else:
                    # Return stats even if no data yet
                    return {
                        'date': str(date),
                        'total_checks': 0,
                        'healthy_checks': 0,
                        'unhealthy_checks': 0,
                        'uptime_percentage': 0,
                        'target_uptime': self.target_uptime,
                        'status': 'no_data',
                        'meeting_target': False
                    }
        except Exception as e:
            logger.error(f"Failed to calculate daily uptime: {e}")
            return None
    
    def get_uptime_stats(self, days=30):
        """Get uptime statistics for the last N days"""
        try:
            with self.db.get_engine().connect() as conn:
                from sqlalchemy import text
                query = text(f"""
                SELECT 
                    date,
                    total_checks,
                    healthy_checks,
                    unhealthy_checks,
                    uptime_percentage,
                    status
                FROM monitoring.uptime_summary
                WHERE date >= CURRENT_DATE - INTERVAL '{days} days'
                ORDER BY date DESC
                """)
                
                results = conn.execute(query).fetchall()
                
                stats = []
                for row in results:
                    stats.append({
                        'date': str(row[0]),
                        'total_checks': row[1],
                        'healthy_checks': row[2],
                        'unhealthy_checks': row[3],
                        'uptime_percentage': float(row[4]) if row[4] else 0,
                        'status': row[5]
                    })
                
                # Calculate overall stats
                if stats:
                    total_days = len(stats)
                    days_meeting_target = sum(1 for s in stats if s['status'] == 'meeting_target')
                    avg_uptime = sum(s['uptime_percentage'] for s in stats) / total_days
                    
                    return {
                        'period_days': days,
                        'total_days': total_days,
                        'days_meeting_target': days_meeting_target,
                        'days_below_target': total_days - days_meeting_target,
                        'average_uptime': avg_uptime,
                        'target_uptime': self.target_uptime,
                        'overall_status': 'meeting_target' if avg_uptime >= self.target_uptime else 'below_target',
                        'daily_stats': stats
                    }
                else:
                    return {
                        'period_days': days,
                        'total_days': 0,
                        'message': 'No data available'
                    }
        except Exception as e:
            logger.error(f"Failed to get uptime stats: {e}")
            return None


if __name__ == "__main__":
    tracker = UptimeTracker()
    
    # Calculate today's uptime
    today_stats = tracker.calculate_daily_uptime()
    print(f"\nToday's Uptime: {today_stats}")
    
    # Get 30-day stats
    stats = tracker.get_uptime_stats(30)
    print(f"\n30-Day Stats: {stats}")

