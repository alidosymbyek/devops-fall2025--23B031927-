from sqlalchemy import create_engine, text
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to database
conn_string = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(conn_string)

print("=" * 60)
print("DATABASE CONTENT VERIFICATION")
print("=" * 60)

# Check staging tables
with engine.connect() as conn:
    # List all tables in staging schema
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'staging'
        ORDER BY table_name
    """))
    
    staging_tables = [row[0] for row in result]
    
    print("\n📊 STAGING TABLES:")
    print("-" * 60)
    for table in staging_tables:
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM staging.{table}"))
        count = count_result.scalar()
        print(f"  ✓ staging.{table}: {count} rows")
        
        # Show first 3 rows
        df = pd.read_sql(f"SELECT * FROM staging.{table} LIMIT 3", conn)
        print(f"\n    Sample data from {table}:")
        print(df.to_string(index=False))
        print()

# Check warehouse tables
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'warehouse'
        ORDER BY table_name
    """))
    
    warehouse_tables = [row[0] for row in result]
    
    print("\n📦 WAREHOUSE TABLES:")
    print("-" * 60)
    for table in warehouse_tables:
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM warehouse.{table}"))
        count = count_result.scalar()
        print(f"  ✓ warehouse.{table}: {count} rows")

# Check pipeline logs
print("\n📝 RECENT PIPELINE EXECUTIONS:")
print("-" * 60)
df = pd.read_sql("""
    SELECT 
        pipeline_name,
        status,
        records_processed,
        EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds,
        created_at
    FROM warehouse.pipeline_logs
    ORDER BY created_at DESC
    LIMIT 5
""", engine)
print(df.to_string(index=False))

print("\n" + "=" * 60)
print("✓ Verification complete!")
print("=" * 60)