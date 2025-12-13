# PowerShell script to generate SSL certificates for PostgreSQL
# This script creates a self-signed certificate for development/testing

Write-Host "Generating SSL certificates for PostgreSQL..." -ForegroundColor Green

# Create SSL directory
$sslDir = "postgres-ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir | Out-Null
    Write-Host "Created directory: $sslDir" -ForegroundColor Yellow
}

# Check if OpenSSL is available
$opensslPath = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $opensslPath) {
    Write-Host "OpenSSL not found. Please install OpenSSL or use the provided Docker-based method." -ForegroundColor Red
    Write-Host "Alternative: Use the generate_ssl_certs.sh script in a Linux/WSL environment" -ForegroundColor Yellow
    exit 1
}

# Generate CA private key
Write-Host "Generating CA private key..." -ForegroundColor Cyan
openssl genrsa -out "$sslDir/ca.key" 2048

# Generate CA certificate
Write-Host "Generating CA certificate..." -ForegroundColor Cyan
openssl req -new -x509 -days 3650 -key "$sslDir/ca.key" -out "$sslDir/ca.crt" `
    -subj "/CN=PostgreSQL-CA/O=DataPlatform/C=US"

# Generate server private key
Write-Host "Generating server private key..." -ForegroundColor Cyan
openssl genrsa -out "$sslDir/server.key" 2048

# Generate server certificate signing request
Write-Host "Generating server certificate signing request..." -ForegroundColor Cyan
openssl req -new -key "$sslDir/server.key" -out "$sslDir/server.csr" `
    -subj "/CN=postgres/O=DataPlatform/C=US"

# Generate server certificate
Write-Host "Generating server certificate..." -ForegroundColor Cyan
openssl x509 -req -days 3650 -in "$sslDir/server.csr" -CA "$sslDir/ca.crt" `
    -CAkey "$sslDir/ca.key" -CAcreateserial -out "$sslDir/server.crt"

# Set proper permissions (on Linux/WSL)
Write-Host "Setting file permissions..." -ForegroundColor Cyan
# On Windows, we'll note the permissions needed
Write-Host "Note: On Linux, run: chmod 600 $sslDir/*.key" -ForegroundColor Yellow

# Clean up CSR file
Remove-Item "$sslDir/server.csr" -ErrorAction SilentlyContinue

Write-Host "`nSSL certificates generated successfully!" -ForegroundColor Green
Write-Host "Files created in: $sslDir" -ForegroundColor Yellow
Write-Host "  - ca.crt (CA certificate)" -ForegroundColor White
Write-Host "  - ca.key (CA private key)" -ForegroundColor White
Write-Host "  - server.crt (Server certificate)" -ForegroundColor White
Write-Host "  - server.key (Server private key)" -ForegroundColor White

