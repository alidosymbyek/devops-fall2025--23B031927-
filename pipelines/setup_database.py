from db_connector import DatabaseConnector
from loguru import logger
from sqlalchemy import text

def setup_database():
    """Initialize database schema"""
    db = DatabaseConnector()
    engine = db.get_engine()
    
    # Read SQL file
    # Get the project root directory (parent of pipelines)
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sql_file = project_root / 'sql' / 'create_tables.sql'
    
    with open(sql_file, 'r') as f:
        sql_script = f.read()
    
    # Execute SQL
    try:
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = sql_script.split(';')
            for statement in statements:
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()
        logger.info("✓ Database schema created successfully!")
    except Exception as e:
        logger.error(f"✗ Failed to create schema: {e}")
        raise

if __name__ == "__main__":
    setup_database()