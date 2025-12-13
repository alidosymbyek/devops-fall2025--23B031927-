#!/bin/bash
# Bash script to generate SSL certificates for PostgreSQL
# This script creates a self-signed certificate for development/testing

echo "Generating SSL certificates for PostgreSQL..."

# Create SSL directory
SSL_DIR="postgres-ssl"
mkdir -p "$SSL_DIR"

# Generate CA private key
echo "Generating CA private key..."
openssl genrsa -out "$SSL_DIR/ca.key" 2048

# Generate CA certificate
echo "Generating CA certificate..."
openssl req -new -x509 -days 3650 -key "$SSL_DIR/ca.key" -out "$SSL_DIR/ca.crt" \
    -subj "/CN=PostgreSQL-CA/O=DataPlatform/C=US"

# Generate server private key
echo "Generating server private key..."
openssl genrsa -out "$SSL_DIR/server.key" 2048

# Generate server certificate signing request
echo "Generating server certificate signing request..."
openssl req -new -key "$SSL_DIR/server.key" -out "$SSL_DIR/server.csr" \
    -subj "/CN=postgres/O=DataPlatform/C=US"

# Generate server certificate
echo "Generating server certificate..."
openssl x509 -req -days 3650 -in "$SSL_DIR/server.csr" -CA "$SSL_DIR/ca.crt" \
    -CAkey "$SSL_DIR/ca.key" -CAcreateserial -out "$SSL_DIR/server.crt"

# Set proper permissions
echo "Setting file permissions..."
chmod 600 "$SSL_DIR"/*.key
chmod 644 "$SSL_DIR"/*.crt

# Clean up CSR file
rm -f "$SSL_DIR/server.csr"

echo ""
echo "SSL certificates generated successfully!"
echo "Files created in: $SSL_DIR"
echo "  - ca.crt (CA certificate)"
echo "  - ca.key (CA private key)"
echo "  - server.crt (Server certificate)"
echo "  - server.key (Server private key)"

