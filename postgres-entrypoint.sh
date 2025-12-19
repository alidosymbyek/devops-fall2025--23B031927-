#!/bin/bash
set -e

# Set permissions for SSL certificates
if [ -d "/var/lib/postgresql/ssl" ]; then
    chmod 600 /var/lib/postgresql/ssl/*.key 2>/dev/null || true
    chmod 644 /var/lib/postgresql/ssl/*.crt 2>/dev/null || true
fi

# Execute the original entrypoint
exec docker-entrypoint.sh "$@"

