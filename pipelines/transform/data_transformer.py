import pandas as pd
from loguru import logger
from datetime import datetime
import json
import sys
import yaml
from pathlib import Path

# Add quality checker to path
sys.path.append(str(Path(__file__).parent.parent))
from quality.data_quality_checker import DataQualityChecker

class DataTransformer:
    def __init__(self, write_files=False):
        self.quality_report = {}
        self.quality_checker = DataQualityChecker()
        self.write_files = write_files
        # Setup staging directory if file writing is enabled
        if self.write_files:
            self.staging_dir = Path(__file__).parent.parent.parent / 'data' / 'staging'
            self.staging_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Intermediate file writing enabled: {self.staging_dir}")
    
    def flatten_dict_columns(self, df):
        """Flatten columns that contain dictionaries"""
        for col in df.columns:
            # Check if column contains dicts
            if df[col].apply(lambda x: isinstance(x, dict)).any():
                logger.info(f"Flattening dictionary column: {col}")
                # Convert dicts to JSON strings
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
        return df
    
    def clean_data(self, df, required_columns=None):
        """Clean and validate data"""
        logger.info(f"Starting data cleaning. Input shape: {df.shape}")
        
        original_count = len(df)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Flatten any dict columns before removing duplicates
        df = self.flatten_dict_columns(df)
        
        # Check required columns
        if required_columns:
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Remove duplicates (now safe after flattening dicts)
        df = df.drop_duplicates()
        
        duplicates_removed = original_count - len(df)
        logger.info(f"Removed {duplicates_removed} duplicate/empty rows")
        
        return df
    
    def add_metadata(self, df, source_name):
        """Add metadata columns"""
        df = df.copy()
        df['source'] = source_name
        df['processed_at'] = datetime.now()
        
        return df
    
    def transform(self, df, source_name, config=None):
        """Main transformation pipeline with quality checks"""
        logger.info(f"Transforming data from {source_name}")
        
        # Clean
        df = self.clean_data(df)
        
        # Add metadata
        df = self.add_metadata(df, source_name)
        
        # Run quality checks
        logger.info(f"Running quality checks for {source_name}")
        checks = {
            'min_row_count': lambda d: self.quality_checker.check_row_count(d, min_rows=1),
            'has_source_column': lambda d: 'source' in d.columns,
            'has_processed_at': lambda d: 'processed_at' in d.columns,
        }
        
        quality_results = self.quality_checker.run_quality_checks(df, checks)
        self.quality_report[source_name] = quality_results
        
        if self.quality_checker.has_failures():
            logger.warning(f"Some quality checks failed for {source_name}")
        else:
            logger.info(f"All quality checks passed for {source_name}")
        
        # Optionally write transformed data to staging directory
        if self.write_files:
            self._write_staging_file(df, source_name)
        
        logger.info(f"✓ Transformation complete. Output shape: {df.shape}")
        return df
    
    def _write_staging_file(self, df, source_name):
        """Write transformed data to staging directory as CSV"""
        try:
            # Create safe filename
            safe_name = source_name.lower().replace('-', '_').replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{safe_name}_{timestamp}.csv"
            filepath = self.staging_dir / filename
            
            df.to_csv(filepath, index=False)
            logger.info(f"✓ Written staging file: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to write staging file: {e}")
    
    def get_quality_report(self):
        """Get the complete quality report for all sources"""
        return self.quality_report

# Test it
if __name__ == "__main__":
    # Create sample data with a dict column
    sample_data = pd.DataFrame({
        'id': [1, 2, 2, 3],
        'name': ['Alice', 'Bob', 'Bob', 'Charlie'],
        'address': [
            {'city': 'NYC', 'zip': '10001'},
            {'city': 'LA', 'zip': '90001'},
            {'city': 'LA', 'zip': '90001'},
            {'city': 'SF', 'zip': '94102'}
        ]
    })
    
    transformer = DataTransformer()
    cleaned = transformer.transform(sample_data, 'test_source')
    print(cleaned)
    print("\nQuality Report:")
    print(transformer.get_quality_report())