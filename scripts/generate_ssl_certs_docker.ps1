# PowerShell script to generate SSL certificates using Docker
# This works on Windows without needing bash

Write-Host "Generating SSL certificates using Docker..." -ForegroundColor Green

# Create SSL directory
$sslDir = "postgres-ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir | Out-Null
    Write-Host "Created directory: $sslDir" -ForegroundColor Yellow
}

$dockerImage = "alpine/openssl:latest"
$currentDir = (Get-Location).Path

# Generate CA private key
Write-Host "Generating CA private key..." -ForegroundColor Cyan
docker run --rm -v "${currentDir}/${sslDir}:/ssl" $dockerImage `
    genrsa -out /ssl/ca.key 2048

# Generate CA certificate
Write-Host "Generating CA certificate..." -ForegroundColor Cyan
docker run --rm -v "${currentDir}/${sslDir}:/ssl" $dockerImage `
    req -new -x509 -days 3650 -key /ssl/ca.key -out /ssl/ca.crt `
    -subj "/CN=PostgreSQL-CA/O=DataPlatform/C=US"

# Generate server private key
Write-Host "Generating server private key..." -ForegroundColor Cyan
docker run --rm -v "${currentDir}/${sslDir}:/ssl" $dockerImage `
    genrsa -out /ssl/server.key 2048

# Generate server certificate signing request
Write-Host "Generating server certificate signing request..." -ForegroundColor Cyan
docker run --rm -v "${currentDir}/${sslDir}:/ssl" $dockerImage `
    req -new -key /ssl/server.key -out /ssl/server.csr `
    -subj "/CN=postgres/O=DataPlatform/C=US"

# Generate server certificate
Write-Host "Generating server certificate..." -ForegroundColor Cyan
docker run --rm -v "${currentDir}/${sslDir}:/ssl" $dockerImage `
    x509 -req -days 3650 -in /ssl/server.csr -CA /ssl/ca.crt `
    -CAkey /ssl/ca.key -CAcreateserial -out /ssl/server.crt

# Clean up CSR file
Remove-Item "$sslDir/server.csr" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "SSL certificates generated successfully!" -ForegroundColor Green
Write-Host "Files created in: $sslDir" -ForegroundColor Yellow
Write-Host "  - ca.crt (CA certificate)" -ForegroundColor White
Write-Host "  - ca.key (CA private key)" -ForegroundColor White
Write-Host "  - server.crt (Server certificate)" -ForegroundColor White
Write-Host "  - server.key (Server private key)" -ForegroundColor White

