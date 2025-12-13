"""
Health Checker for Data Platform Services
Monitors uptime and health of all services
"""
import requests
import psycopg2
from datetime import datetime, timedelta
from loguru import logger
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from db_connector import DatabaseConnector


class HealthChecker:
    """Check health status of all platform services"""
    
    def __init__(self):
        self.services = {
            'airflow_webserver': {
                'url': 'http://localhost:8080/health',
                'type': 'http',
                'timeout': 5
            },
            'postgres': {
                'host': os.getenv('DB_HOST', 'postgres'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'dataplatform'),
                'user': os.getenv('DB_USER', 'datauser'),
                'password': os.getenv('DB_PASSWORD', 'mypassword'),
                'type': 'database',
                'timeout': 5
            },
            'kafka': {
                'host': 'kafka',
                'port': 9092,
                'type': 'kafka',
                'timeout': 5
            }
        }
    
    def check_http_service(self, service_name, config):
        """Check HTTP service health"""
        try:
            response = requests.get(
                config['url'],
                timeout=config['timeout'],
                allow_redirects=True
            )
            is_healthy = response.status_code == 200
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_database_service(self, service_name, config):
        """Check database service health"""
        try:
            db = DatabaseConnector()
            start_time = datetime.now()
            result = db.test_connection()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy' if result else 'unhealthy',
                'response_time_ms': response_time,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Database health check failed for {service_name}: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_kafka_service(self, service_name, config):
        """Check Kafka service health"""
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=f"{config['host']}:{config['port']}",
                request_timeout_ms=config['timeout'] * 1000
            )
            # Try to get metadata
            metadata = producer.list_topics(timeout=config['timeout'])
            producer.close()
            
            return {
                'status': 'healthy',
                'topics_count': len(metadata),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Kafka health check failed for {service_name}: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def check_all_services(self):
        """Check health of all services"""
        results = {}
        
        for service_name, config in self.services.items():
            logger.info(f"Checking health of {service_name}...")
            
            if config['type'] == 'http':
                results[service_name] = self.check_http_service(service_name, config)
            elif config['type'] == 'database':
                results[service_name] = self.check_database_service(service_name, config)
            elif config['type'] == 'kafka':
                results[service_name] = self.check_kafka_service(service_name, config)
            
            logger.info(f"{service_name}: {results[service_name]['status']}")
        
        return results
    
    def get_overall_health(self, results=None):
        """Get overall platform health status"""
        if results is None:
            results = self.check_all_services()
        
        healthy_count = sum(1 for r in results.values() if r.get('status') == 'healthy')
        total_count = len(results)
        
        overall_status = 'healthy' if healthy_count == total_count else 'degraded'
        if healthy_count == 0:
            overall_status = 'down'
        
        return {
            'overall_status': overall_status,
            'healthy_services': healthy_count,
            'total_services': total_count,
            'uptime_percentage': (healthy_count / total_count * 100) if total_count > 0 else 0,
            'services': results,
            'timestamp': datetime.now().isoformat()
        }


def check_health():
    """Main health check function"""
    checker = HealthChecker()
    return checker.get_overall_health()


if __name__ == "__main__":
    checker = HealthChecker()
    results = checker.check_all_services()
    overall = checker.get_overall_health(results)
    
    print(f"\nOverall Status: {overall['overall_status']}")
    print(f"Uptime: {overall['uptime_percentage']:.2f}%")
    print(f"Healthy Services: {overall['healthy_services']}/{overall['total_services']}\n")
    
    for service, result in results.items():
        status_icon = "✅" if result['status'] == 'healthy' else "❌"
        print(f"{status_icon} {service}: {result['status']}")

