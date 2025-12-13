# PowerShell Script to Apply Table Partitioning
# This script applies partitioning to the database via Docker

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Applying Table Partitioning" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker is not running or not accessible" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
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

Write-Host "Step 1: Creating partitioned tables..." -ForegroundColor Green
Get-Content sql/create_partitioned_tables.sql | docker exec -i $postgresContainer psql -U datauser -d dataplatform

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Partitioned tables created successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create partitioned tables" -ForegroundColor Red
    Write-Host "Check the error messages above for details" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Partitioning Applied Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: If you have existing data, run:" -ForegroundColor Yellow
Write-Host "  .\migrate_existing_data.ps1" -ForegroundColor Yellow
Write-Host ""
