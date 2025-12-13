import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from loguru import logger
from pathlib import Path

# Load environment variables (only if not already set - allows Docker env vars to take precedence)
# This ensures Docker environment variables override .env file
if not os.getenv('DB_HOST'):
    load_dotenv()

class DatabaseConnector:
    def __init__(self):
        # Read environment variables - use Docker network defaults for Airflow
        self.host = os.getenv('DB_HOST', 'postgres')  # Default to Docker network hostname
        self.port = os.getenv('DB_PORT', '5432')  # Default to internal port
        self.database = os.getenv('DB_NAME', 'dataplatform')
        self.user = os.getenv('DB_USER', 'datauser')
        self.password = os.getenv('DB_PASSWORD', 'mypassword')
        
        # SSL configuration - prefer mode for Docker network (SSL works there)
        self.ssl_mode = os.getenv('DB_SSL_MODE', 'prefer')  # prefer, require, verify-ca, verify-full
        self.ssl_cert_path = os.getenv('DB_SSL_CERT_PATH')
        self.ssl_key_path = os.getenv('DB_SSL_KEY_PATH')
        self.ssl_ca_path = os.getenv('DB_SSL_CA_PATH')
        
        self.engine = None
        self.connection_string = None
        
    def get_connection_string(self):
        """Create PostgreSQL connection string with SSL support"""
        if not self.connection_string:
            base_conn = (
                f"postgresql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.database}"
            )
            
            # Add SSL parameters to connection string
            ssl_params = []
            if self.ssl_mode:
                ssl_params.append(f"sslmode={self.ssl_mode}")
            
            # Note: sslcert, sslkey, sslrootcert are passed via connect_args
            # because they need file paths, not URLs
            
            if ssl_params:
                self.connection_string = f"{base_conn}?{'&'.join(ssl_params)}"
            else:
                self.connection_string = base_conn
                
        return self.connection_string
    
    def get_engine(self):
        """Get SQLAlchemy engine with SSL support"""
        if not self.engine:
            # Build connect_args for psycopg2 SSL parameters
            connect_args = {}
            
            if self.ssl_mode:
                connect_args['sslmode'] = self.ssl_mode
            
            if self.ssl_cert_path and Path(self.ssl_cert_path).exists():
                connect_args['sslcert'] = self.ssl_cert_path
            
            if self.ssl_key_path and Path(self.ssl_key_path).exists():
                connect_args['sslkey'] = self.ssl_key_path
            
            if self.ssl_ca_path and Path(self.ssl_ca_path).exists():
                connect_args['sslrootcert'] = self.ssl_ca_path
            
            # Create engine with SSL support and connection pooling for concurrent pipelines
            pool_config = {
                'pool_size': 20,           # Number of connections to maintain
                'max_overflow': 40,       # Maximum overflow connections
                'pool_pre_ping': True,     # Verify connections before using
                'pool_recycle': 3600,      # Recycle connections after 1 hour
                'pool_timeout': 30,        # Timeout for getting connection from pool
            }
            
            if connect_args:
                self.engine = create_engine(
                    self.get_connection_string(),
                    connect_args=connect_args,
                    **pool_config
                )
                logger.info(f"Database engine created with SSL (mode: {self.ssl_mode}) and connection pooling")
            else:
                self.engine = create_engine(
                    self.get_connection_string(),
                    **pool_config
                )
                logger.info("Database engine created with connection pooling")
                
        return self.engine
    
    def test_connection(self):
        """Test database connection"""
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✓ Database connection successful!")
                return True
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False

# Test it
if __name__ == "__main__":
    db = DatabaseConnector()
    db.test_connection()