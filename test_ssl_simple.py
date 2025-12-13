"""Simple SSL test using psycopg2 directly"""
import psycopg2
import os
from pathlib import Path

# SSL configuration
ssl_ca = Path('postgres-ssl/ca.crt')

print("Testing SSL connection with psycopg2...")
print(f"CA Certificate: {ssl_ca.exists()}")

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='dataplatform',
        user='datauser',
        password='mypassword',
        sslmode='require',
        sslrootcert=str(ssl_ca) if ssl_ca.exists() else None
    )
    print("SUCCESS: SSL connection established!")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(f"PostgreSQL version: {cur.fetchone()[0]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
    print("\nTrying without SSL certificate...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            database='dataplatform',
            user='datauser',
            password='mypassword',
            sslmode='require'
        )
        print("SUCCESS: SSL connection works without CA cert!")
        conn.close()
    except Exception as e2:
        print(f"ERROR: {e2}")

