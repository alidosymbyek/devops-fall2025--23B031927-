# Quick Diagnostic Script for Grafana "No Data" Issue (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Grafana Dashboard Diagnostic Check" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Finding PostgreSQL container name..." -ForegroundColor Yellow
$containerName = docker ps --format "{{.Names}}" | Select-String "postgres" | Select-Object -First 1
if ($containerName) {
    $containerName = $containerName.ToString().Trim()
    Write-Host "✅ Found container: $containerName" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL container NOT found" -ForegroundColor Red
    Write-Host "Available containers:" -ForegroundColor Yellow
    docker ps --format "table {{.Names}}\t{{.Image}}"
    exit 1
}
Write-Host ""

Write-Host "2. Checking if monitoring schema exists..." -ForegroundColor Yellow
$schema = docker exec $containerName psql -U datauser -d dataplatform -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'monitoring';" 2>$null
if ($schema -match "monitoring") {
    Write-Host "✅ Monitoring schema exists" -ForegroundColor Green
} else {
    Write-Host "⚠️  Monitoring schema does NOT exist" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "3. Checking if monitoring tables exist..." -ForegroundColor Yellow
docker exec $containerName psql -U datauser -d dataplatform -c "\dt monitoring.*" 2>$null
Write-Host ""

Write-Host "4. Checking uptime_log table data..." -ForegroundColor Yellow
$count = docker exec $containerName psql -U datauser -d dataplatform -t -c "SELECT COUNT(*) FROM monitoring.uptime_log;" 2>$null
$count = $count.Trim()
if ($count -and [int]$count -gt 0) {
    Write-Host "✅ uptime_log has $count rows" -ForegroundColor Green
} else {
    Write-Host "⚠️  uptime_log has no data (or table doesn't exist)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "5. Checking uptime_summary table data..." -ForegroundColor Yellow
docker exec $containerName psql -U datauser -d dataplatform -c "SELECT * FROM monitoring.uptime_summary ORDER BY date DESC LIMIT 3;" 2>$null
Write-Host ""

Write-Host "6. Checking recent uptime_log entries..." -ForegroundColor Yellow
docker exec $containerName psql -U datauser -d dataplatform -c "SELECT timestamp, service_name, status FROM monitoring.uptime_log ORDER BY timestamp DESC LIMIT 5;" 2>$null
Write-Host ""

Write-Host "7. Checking Grafana datasource configuration..." -ForegroundColor Yellow
Write-Host "   (Check manually in Grafana UI: Connections → Data sources → PostgreSQL)" -ForegroundColor Gray
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Complete" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If tables don't exist, create them (see FIX_GRAFANA_NO_DATA.md)" -ForegroundColor White
Write-Host "2. If no data, trigger uptime_monitoring DAG in Airflow" -ForegroundColor White
Write-Host "3. If data exists but Grafana shows 'No data', check datasource connection" -ForegroundColor White

