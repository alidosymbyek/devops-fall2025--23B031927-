import pandas as pd
import yaml
from pathlib import Path
from loguru import logger
from datetime import datetime

class CSVExtractor:
    def __init__(self, data_folder=None):
        # Use absolute path in Airflow container, or /tmp as fallback
        if data_folder is None:
            # Try to read from config file first
            config_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        csv_folder = config.get('data_sources', {}).get('csv_folder')
                        if csv_folder:
                            # Resolve relative path from config relative to project root
                            project_root = Path(__file__).parent.parent.parent
                            data_folder = str((project_root / csv_folder).resolve())
                            logger.info(f"Using CSV folder from config: {data_folder}")
                except Exception as e:
                    logger.warning(f"Could not read config for CSV folder: {e}")
            
            # Fallback to default logic if config not available
            if data_folder is None:
                # Check if running in Airflow container
                if Path('/opt/airflow').exists():
                    data_folder = '/opt/airflow/data/raw'
                else:
                    # Local development - use current directory
                    data_folder = Path(__file__).parent.parent.parent / 'data' / 'raw'
                    data_folder = str(data_folder.resolve())
        
        self.data_folder = Path(data_folder).resolve()  # Always use absolute path
        try:
            self.data_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using data folder: {self.data_folder}")
            logger.info(f"Data folder exists: {self.data_folder.exists()}")
        except (PermissionError, OSError) as e:
            # Fallback to /tmp if permission denied
            logger.warning(f"Permission denied for {data_folder}: {e}, using /tmp/data/raw")
            self.data_folder = Path('/tmp/data/raw').resolve()
            self.data_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using fallback data folder: {self.data_folder}")
        
    def extract_csv(self, file_path):
        """Extract data from CSV file"""
        try:
            logger.info(f"Extracting data from {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"✓ Extracted {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            logger.error(f"✗ Failed to extract {file_path}: {e}")
            raise
    
    def extract_all_csvs(self):
        """Extract all CSV files from raw folder"""
        logger.info(f"Looking for CSV files in: {self.data_folder}")
        csv_files = list(self.data_folder.glob('*.csv'))
        logger.info(f"Found {len(csv_files)} CSV file(s): {[f.name for f in csv_files]}")
        
        if not csv_files:
            logger.warning(f"No CSV files found in data/raw folder: {self.data_folder}")
            return {}
        
        datasets = {}
        for csv_file in csv_files:
            try:
                df = self.extract_csv(csv_file)
                datasets[csv_file.stem] = df
            except Exception as e:
                logger.error(f"Skipping {csv_file}: {e}")
        
        return datasets

# Test it
if __name__ == "__main__":
    extractor = CSVExtractor()
    data = extractor.extract_all_csvs()
    print(f"Extracted {len(data)} datasets")
    for name, df in data.items():
        print(f"  - {name}: {len(df)} rows")