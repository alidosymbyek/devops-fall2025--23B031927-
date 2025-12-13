#!/bin/bash
# Generate SSL certificates using Docker (works on all platforms)
# This is the recommended method for Windows users

echo "Generating SSL certificates using Docker..."

# Create SSL directory
SSL_DIR="postgres-ssl"
mkdir -p "$SSL_DIR"

# Use Docker to run OpenSSL commands
DOCKER_IMAGE="alpine/openssl:latest"

# Generate CA private key
echo "Generating CA private key..."
docker run --rm -v "$(pwd)/$SSL_DIR:/ssl" $DOCKER_IMAGE \
    genrsa -out /ssl/ca.key 2048

# Generate CA certificate
echo "Generating CA certificate..."
docker run --rm -v "$(pwd)/$SSL_DIR:/ssl" $DOCKER_IMAGE \
    req -new -x509 -days 3650 -key /ssl/ca.key -out /ssl/ca.crt \
    -subj "/CN=PostgreSQL-CA/O=DataPlatform/C=US"

# Generate server private key
echo "Generating server private key..."
docker run --rm -v "$(pwd)/$SSL_DIR:/ssl" $DOCKER_IMAGE \
    genrsa -out /ssl/server.key 2048

# Generate server certificate signing request
echo "Generating server certificate signing request..."
docker run --rm -v "$(pwd)/$SSL_DIR:/ssl" $DOCKER_IMAGE \
    req -new -key /ssl/server.key -out /ssl/server.csr \
    -subj "/CN=postgres/O=DataPlatform/C=US"

# Generate server certificate
echo "Generating server certificate..."
docker run --rm -v "$(pwd)/$SSL_DIR:/ssl" $DOCKER_IMAGE \
    x509 -req -days 3650 -in /ssl/server.csr -CA /ssl/ca.crt \
    -CAkey /ssl/ca.key -CAcreateserial -out /ssl/server.crt

# Set proper permissions (on Linux/Mac)
if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
    chmod 600 "$SSL_DIR"/*.key
    chmod 644 "$SSL_DIR"/*.crt
fi

# Clean up CSR file
rm -f "$SSL_DIR/server.csr"

echo ""
echo "SSL certificates generated successfully!"
echo "Files created in: $SSL_DIR"
echo "  - ca.crt (CA certificate)"
echo "  - ca.key (CA private key)"
echo "  - server.crt (Server certificate)"
echo "  - server.key (Server private key)"

