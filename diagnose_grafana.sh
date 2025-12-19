#!/bin/bash
# Quick Diagnostic Script for Grafana "No Data" Issue

echo "=========================================="
echo "Grafana Dashboard Diagnostic Check"
echo "=========================================="
echo ""

echo "1. Checking if PostgreSQL is running..."
docker ps | grep postgres
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is NOT running"
    exit 1
fi
echo ""

echo "2. Checking if monitoring schema exists..."
docker exec postgres psql -U datauser -d dataplatform -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'monitoring';" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Can connect to database"
else
    echo "❌ Cannot connect to database"
    exit 1
fi
echo ""

echo "3. Checking if monitoring tables exist..."
docker exec postgres psql -U datauser -d dataplatform -c "\dt monitoring.*" 2>/dev/null
echo ""

echo "4. Checking uptime_log table data..."
COUNT=$(docker exec postgres psql -U datauser -d dataplatform -t -c "SELECT COUNT(*) FROM monitoring.uptime_log;" 2>/dev/null | tr -d ' ')
if [ -n "$COUNT" ] && [ "$COUNT" -gt 0 ]; then
    echo "✅ uptime_log has $COUNT rows"
else
    echo "⚠️  uptime_log has no data (or table doesn't exist)"
fi
echo ""

echo "5. Checking uptime_summary table data..."
docker exec postgres psql -U datauser -d dataplatform -c "SELECT * FROM monitoring.uptime_summary ORDER BY date DESC LIMIT 3;" 2>/dev/null
echo ""

echo "6. Checking recent uptime_log entries..."
docker exec postgres psql -U datauser -d dataplatform -c "SELECT timestamp, service_name, status FROM monitoring.uptime_log ORDER BY timestamp DESC LIMIT 5;" 2>/dev/null
echo ""

echo "7. Checking Grafana datasource configuration..."
echo "   (Check manually in Grafana UI: Connections → Data sources → PostgreSQL)"
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If tables don't exist, create them (see FIX_GRAFANA_NO_DATA.md)"
echo "2. If no data, trigger uptime_monitoring DAG in Airflow"
echo "3. If data exists but Grafana shows 'No data', check datasource connection"

