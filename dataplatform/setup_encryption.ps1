# PowerShell script to set up database encryption
# This script generates SSL certificates and configures encryption

Write-Host "Setting up Database Encryption..." -ForegroundColor Green
Write-Host ""

# Step 1: Generate SSL certificates
Write-Host "Step 1: Generating SSL certificates..." -ForegroundColor Cyan
if (Test-Path "scripts\generate_ssl_certs.ps1") {
    & "scripts\generate_ssl_certs.ps1"
} elseif (Test-Path "scripts\generate_ssl_certs_docker.sh") {
    Write-Host "Using Docker method to generate certificates..." -ForegroundColor Yellow
    bash scripts/generate_ssl_certs_docker.sh
} else {
    Write-Host "Warning: Certificate generation scripts not found." -ForegroundColor Yellow
    Write-Host "Please run one of the certificate generation scripts manually:" -ForegroundColor Yellow
    Write-Host "  - scripts\generate_ssl_certs.ps1" -ForegroundColor White
    Write-Host "  - scripts\generate_ssl_certs_docker.sh" -ForegroundColor White
}

# Step 2: Check if certificates were created
Write-Host ""
Write-Host "Step 2: Verifying certificates..." -ForegroundColor Cyan
$sslDir = "postgres-ssl"
$requiredFiles = @("ca.crt", "ca.key", "server.crt", "server.key")

$allExist = $true
foreach ($file in $requiredFiles) {
    $path = Join-Path $sslDir $file
    if (Test-Path $path) {
        Write-Host "  ✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file missing" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host ""
    Write-Host "Error: Not all required certificates were generated." -ForegroundColor Red
    Write-Host "Please run the certificate generation script manually." -ForegroundColor Yellow
    exit 1
}

# Step 3: Update .env file
Write-Host ""
Write-Host "Step 3: Updating environment configuration..." -ForegroundColor Cyan
$envFile = ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# Database connection
DB_HOST=localhost
DB_PORT=5433
DB_NAME=dataplatform
DB_USER=datauser
DB_PASSWORD=mypassword

# SSL/TLS Configuration
DB_SSL_MODE=require
DB_SSL_CA_PATH=./postgres-ssl/ca.crt
"@ | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "  ✓ Created .env file with SSL configuration" -ForegroundColor Green
} else {
    Write-Host "  .env file already exists" -ForegroundColor Yellow
    Write-Host "  Please add these SSL settings manually:" -ForegroundColor Yellow
    Write-Host "    DB_SSL_MODE=require" -ForegroundColor White
    Write-Host "    DB_SSL_CA_PATH=./postgres-ssl/ca.crt" -ForegroundColor White
}

# Step 4: Instructions
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart Docker services:" -ForegroundColor White
Write-Host "   docker-compose -f docker-compose-airflow.yml restart postgres" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test SSL connection:" -ForegroundColor White
Write-Host "   python tests\test_ssl_connection.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. For encryption at rest, see DATABASE_ENCRYPTION.md" -ForegroundColor White
Write-Host ""

