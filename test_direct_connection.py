from sqlalchemy import create_engine, text

# Direct connection string - no .env
conn_string = "postgresql://datauser:mypassword@localhost:5432/dataplatform"

try:
    engine = create_engine(conn_string)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✓ Direct connection works!")
except Exception as e:
    print(f"✗ Failed: {e}")