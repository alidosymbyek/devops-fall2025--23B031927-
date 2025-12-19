# PowerShell Script to Migrate Existing Data to Partitioned Tables
# WARNING: This script migrates data from existing tables to partitioned tables
# Make sure to backup your database first!

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migrating Data to Partitioned Tables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker is not running or not accessible" -ForegroundColor Red
    exit 1
}

# Check if postgres container is running
$postgresContainer = docker ps --filter "name=postgres" --format "{{.Names}}" | Select-Object -First 1
if (-not $postgresContainer) {
    Write-Host "Error: PostgreSQL container is not running" -ForegroundColor Red
    Write-Host "Please start the containers first:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose-airflow.yml up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found PostgreSQL container: $postgresContainer" -ForegroundColor Cyan
Write-Host ""

# Warning about backup
Write-Host "WARNING: This will migrate existing data to partitioned tables." -ForegroundColor Yellow
Write-Host "Make sure you have a backup of your database!" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Do you want to continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Migration cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Creating backup..." -ForegroundColor Green
$backupFile = "backup_before_partitioning_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
docker exec $postgresContainer pg_dump -U datauser dataplatform | Out-File -FilePath $backupFile -Encoding utf8

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Backup created: $backupFile" -ForegroundColor Green
} else {
    Write-Host "✗ Backup failed. Aborting migration." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 1: Creating partitioned tables (if not exists)..." -ForegroundColor Green
Get-Content sql/create_partitioned_tables.sql | docker exec -i $postgresContainer psql -U datauser -d dataplatform

Write-Host ""
Write-Host "Step 2: Migrating existing data..." -ForegroundColor Green
Get-Content sql/migrate_to_partitioned_tables.sql | docker exec -i $postgresContainer psql -U datauser -d dataplatform

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migration completed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Migration failed. Check the error messages above." -ForegroundColor Red
    Write-Host "You can restore from backup: $backupFile" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 3: Verifying migration..." -ForegroundColor Green
docker exec $postgresContainer psql -U datauser -d dataplatform -c @"
SELECT 
    'pipeline_logs' as table_name,
    (SELECT COUNT(*) FROM warehouse.pipeline_logs) as new_count,
    (SELECT COUNT(*) FROM warehouse.pipeline_logs_old) as old_count
UNION ALL
SELECT 
    'raw_data',
    (SELECT COUNT(*) FROM staging.raw_data),
    (SELECT COUNT(*) FROM staging.raw_data_old)
UNION ALL
SELECT 
    'fact_data_metrics',
    (SELECT COUNT(*) FROM warehouse.fact_data_metrics),
    (SELECT COUNT(*) FROM warehouse.fact_data_metrics_old)
UNION ALL
SELECT 
    'uptime_log',
    (SELECT COUNT(*) FROM monitoring.uptime_log),
    (SELECT COUNT(*) FROM monitoring.uptime_log_old);
"@

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify the row counts match above" -ForegroundColor White
Write-Host "2. Test your application to ensure everything works" -ForegroundColor White
Write-Host "3. Once verified, you can drop old tables:" -ForegroundColor White
Write-Host "   docker exec $postgresContainer psql -U datauser -d dataplatform -c 'DROP TABLE IF EXISTS warehouse.pipeline_logs_old, staging.raw_data_old, warehouse.fact_data_metrics_old, monitoring.uptime_log_old;'" -ForegroundColor Gray
Write-Host ""
Write-Host "Backup saved at: $backupFile" -ForegroundColor Cyan

