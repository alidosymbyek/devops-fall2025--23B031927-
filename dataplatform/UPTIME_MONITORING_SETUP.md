# Uptime Monitoring Setup Guide

## Quick Start

### 1. Start Monitoring Services

```bash
# Start Prometheus and Grafana
docker-compose -f docker-compose-airflow.yml up -d prometheus grafana

# Verify they're running
docker ps | grep -E "prometheus|grafana"
```

### 2. Enable Monitoring DAG

1. Open Airflow UI: http://localhost:8080
2. Find `uptime_monitoring` DAG
3. Toggle it ON (unpause)
4. It will start running every 5 minutes

### 3. Access Dashboards

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin123`
  - Go to Dashboards → "Data Platform Uptime Monitoring"

- **Prometheus**: http://localhost:9090
  - View metrics and query data

## Verification

### Test Health Checker

```bash
docker exec dataplatform-airflow-scheduler-1 python -c "
import sys
sys.path.insert(0, '/opt/airflow/pipelines')
from monitoring.health_checker import HealthChecker
checker = HealthChecker()
results = checker.get_overall_health()
print(f\"Overall Status: {results['overall_status']}\")
print(f\"Uptime: {results['uptime_percentage']:.2f}%\")
print(f\"Healthy Services: {results['healthy_services']}/{results['total_services']}\")
"
```

### Check Database Tables

```bash
docker exec dataplatform-postgres-1 psql -U datauser -d dataplatform -c "
SELECT * FROM monitoring.uptime_log ORDER BY timestamp DESC LIMIT 5;
SELECT * FROM monitoring.uptime_summary ORDER BY date DESC LIMIT 7;
"
```

## What Gets Monitored

1. **Airflow Webserver** - HTTP health endpoint
2. **PostgreSQL** - Database connection
3. **Kafka** - Broker availability

## Uptime Calculation

- **Target**: 99.5%
- **Frequency**: Health check every 5 minutes
- **Calculation**: (Healthy Checks / Total Checks) × 100
- **Storage**: Daily summaries in `monitoring.uptime_summary`

## Troubleshooting

### Prometheus not starting
- Check if port 9090 is available
- Verify `monitoring/prometheus.yml` exists
- Check logs: `docker logs prometheus`

### Grafana not starting
- Check if port 3000 is available
- Verify dashboard files exist
- Check logs: `docker logs grafana`

### Health checks failing
- Verify services are running: `docker ps`
- Check service URLs are correct
- Review Airflow logs for errors

---

*Last Updated: 2025-12-13*

