# PowerShell script to update .env file with correct database settings

Write-Host "Updating .env file with correct database settings..." -ForegroundColor Green

$envFile = ".env"

if (-not (Test-Path $envFile)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# Database connection - Use Docker network for Airflow containers
DB_HOST=postgres
DB_PORT=5432
DB_NAME=dataplatform
DB_USER=datauser
DB_PASSWORD=mypassword

# SSL/TLS Configuration
DB_SSL_MODE=prefer
"@ | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "Created .env file with correct settings" -ForegroundColor Green
} else {
    Write-Host "Updating existing .env file..." -ForegroundColor Yellow
    
    # Read current content
    $content = Get-Content $envFile
    
    # Update or add DB_HOST
    if ($content -match "^DB_HOST=") {
        $content = $content -replace "^DB_HOST=.*", "DB_HOST=postgres"
    } else {
        $content += "DB_HOST=postgres"
    }
    
    # Update or add DB_PORT
    if ($content -match "^DB_PORT=") {
        $content = $content -replace "^DB_PORT=.*", "DB_PORT=5432"
    } else {
        $content += "DB_PORT=5432"
    }
    
    # Update or add DB_SSL_MODE
    if ($content -match "^DB_SSL_MODE=") {
        $content = $content -replace "^DB_SSL_MODE=.*", "DB_SSL_MODE=prefer"
    } else {
        $content += "DB_SSL_MODE=prefer"
    }
    
    # Ensure DB_NAME, DB_USER, DB_PASSWORD exist
    if (-not ($content -match "^DB_NAME=")) {
        $content += "DB_NAME=dataplatform"
    }
    if (-not ($content -match "^DB_USER=")) {
        $content += "DB_USER=datauser"
    }
    if (-not ($content -match "^DB_PASSWORD=")) {
        $content += "DB_PASSWORD=mypassword"
    }
    
    # Write updated content
    $content | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "Updated .env file" -ForegroundColor Green
}

Write-Host "`n.env file updated successfully!" -ForegroundColor Green
Write-Host "`nNew settings:" -ForegroundColor Cyan
Write-Host "  DB_HOST=postgres (Docker network)" -ForegroundColor White
Write-Host "  DB_PORT=5432 (internal port)" -ForegroundColor White
Write-Host "  DB_SSL_MODE=prefer" -ForegroundColor White
Write-Host "`nRestart Airflow services to apply changes:" -ForegroundColor Yellow
Write-Host "  docker-compose -f docker-compose-airflow.yml restart airflow-webserver airflow-scheduler" -ForegroundColor Gray
Write-Host ""

