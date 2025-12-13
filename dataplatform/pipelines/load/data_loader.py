import pandas as pd
from sqlalchemy import text
from loguru import logger
import sys
import os
# Add pipelines directory to path for imports
pipelines_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pipelines_path not in sys.path:
    sys.path.insert(0, pipelines_path)
from db_connector import DatabaseConnector

class DataLoader:
    def __init__(self):
        self.db = DatabaseConnector()
        self.engine = self.db.get_engine()
    
    def _ensure_schema_exists(self, schema):
        """Create schema if it doesn't exist"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                conn.commit()
                logger.debug(f"Schema '{schema}' ensured to exist")
        except Exception as e:
            logger.warning(f"Could not ensure schema '{schema}' exists: {e}")
            # Don't raise - let the actual operation fail if schema is truly needed
    
    def load_to_staging(self, df, table_name, schema='staging'):
        """Load data to staging area"""
        try:
            # Ensure schema exists before trying to create table
            self._ensure_schema_exists(schema)
            
            full_table_name = f"{schema}.{table_name}"
            logger.info(f"Loading {len(df)} rows to {full_table_name}")
            
            df.to_sql(
                name=table_name,
                con=self.engine,
                schema=schema,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=10000  # Optimized for high-volume data (100 GB/day support)
            )
            
            logger.info(f"✓ Successfully loaded to {full_table_name}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to load to {full_table_name}: {e}")
            raise
    
    def load_to_warehouse(self, df, table_name, schema='warehouse'):
        """Load data to data warehouse"""
        return self.load_to_staging(df, table_name, schema)
    
    def log_pipeline_execution(self, pipeline_name, status, records_processed, 
                               start_time, end_time, error_message=None):
        """Log pipeline execution to database"""
        try:
            log_data = pd.DataFrame([{
                'pipeline_name': pipeline_name,
                'status': status,
                'start_time': start_time,
                'end_time': end_time,
                'records_processed': records_processed,
                'error_message': error_message
            }])
            
            self.load_to_warehouse(log_data, 'pipeline_logs')
            logger.info("✓ Pipeline execution logged")
            
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")