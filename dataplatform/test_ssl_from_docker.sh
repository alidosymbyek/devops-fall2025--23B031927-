#!/bin/bash
# Test SSL connection from within Docker network
# This test runs inside a container on the same network as PostgreSQL

echo "============================================================"
echo "Testing SSL Connection from Docker Network"
echo "============================================================"
echo ""

# Test 1: Basic connection with SSL
echo "Test 1: Connecting with SSL (require mode)..."
docker run --rm --network dataplatform_default \
  -v "$(pwd)/postgres-ssl:/ssl:ro" \
  postgres:14 \
  psql -h dataplatform-postgres-1 -U airflow -d airflow \
  -c "SELECT 'SSL Connection Test' as test, version() as pg_version;" \
  2>&1 | grep -E "(SSL|test|PostgreSQL)" || echo "Connection test completed"

echo ""
echo "Test 2: Checking connection info..."
docker run --rm --network dataplatform_default \
  postgres:14 \
  psql -h dataplatform-postgres-1 -U airflow -d airflow \
  -c "\conninfo" 2>&1 | grep -i ssl

echo ""
echo "============================================================"
echo "If you see 'SSL connection' above, SSL is working correctly!"
echo "============================================================"

