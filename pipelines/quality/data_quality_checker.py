import pandas as pd
from loguru import logger
from datetime import datetime
from typing import Dict, List, Callable

class DataQualityChecker:
    def __init__(self):
        self.quality_report = {}
        self.failed_checks = []
    
    def check_null_values(self, df: pd.DataFrame, columns: List[str]) -> bool:
        """Check if specified columns have null values"""
        for col in columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    logger.warning(f"Found {null_count} null values in {col}")
                    return False
        return True
    
    def check_duplicates(self, df: pd.DataFrame, columns: List[str]) -> bool:
        """Check for duplicate rows based on specified columns"""
        duplicate_count = df.duplicated(subset=columns).sum()
        if duplicate_count > 0:
            logger.warning(f"Found {duplicate_count} duplicate rows")
            return False
        return True
    
    def check_data_types(self, df: pd.DataFrame, type_mapping: Dict[str, str]) -> bool:
        """Validate column data types"""
        for col, expected_type in type_mapping.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if expected_type not in actual_type:
                    logger.warning(f"Column {col} has type {actual_type}, expected {expected_type}")
                    return False
        return True
    
    def check_value_range(self, df: pd.DataFrame, column: str, min_val=None, max_val=None) -> bool:
        """Check if values are within expected range"""
        if column not in df.columns:
            return True
        
        if min_val is not None:
            below_min = (df[column] < min_val).sum()
            if below_min > 0:
                logger.warning(f"{below_min} values in {column} below minimum {min_val}")
                return False
        
        if max_val is not None:
            above_max = (df[column] > max_val).sum()
            if above_max > 0:
                logger.warning(f"{above_max} values in {column} above maximum {max_val}")
                return False
        
        return True
    
    def check_row_count(self, df: pd.DataFrame, min_rows: int = 1) -> bool:
        """Check if dataframe has minimum number of rows"""
        row_count = len(df)
        if row_count < min_rows:
            logger.warning(f"Only {row_count} rows found, expected at least {min_rows}")
            return False
        return True
    
    def check_unique_values(self, df: pd.DataFrame, column: str) -> bool:
        """Check if column has unique values"""
        if column not in df.columns:
            return True
        
        duplicate_count = df[column].duplicated().sum()
        if duplicate_count > 0:
            logger.warning(f"Column {column} has {duplicate_count} duplicate values")
            return False
        return True
    
    def check_date_range(self, df: pd.DataFrame, date_column: str, 
                         start_date=None, end_date=None) -> bool:
        """Check if dates are within expected range"""
        if date_column not in df.columns:
            return True
        
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        if start_date:
            before_start = (df[date_column] < pd.to_datetime(start_date)).sum()
            if before_start > 0:
                logger.warning(f"{before_start} dates before {start_date}")
                return False
        
        if end_date:
            after_end = (df[date_column] > pd.to_datetime(end_date)).sum()
            if after_end > 0:
                logger.warning(f"{after_end} dates after {end_date}")
                return False
        
        return True
    
    def run_quality_checks(self, df: pd.DataFrame, checks: Dict[str, Callable]) -> Dict:
        """Run all quality checks and generate report"""
        logger.info(f"Running {len(checks)} quality checks...")
        
        results = {
            'timestamp': datetime.now(),
            'total_checks': len(checks),
            'passed': 0,
            'failed': 0,
            'checks': {}
        }
        
        for check_name, check_func in checks.items():
            try:
                passed = check_func(df)
                results['checks'][check_name] = {
                    'passed': passed,
                    'timestamp': datetime.now()
                }
                
                if passed:
                    results['passed'] += 1
                    logger.info(f"✓ {check_name}: PASSED")
                else:
                    results['failed'] += 1
                    logger.error(f"✗ {check_name}: FAILED")
                    self.failed_checks.append(check_name)
                    
            except Exception as e:
                logger.error(f"✗ {check_name}: ERROR - {e}")
                results['checks'][check_name] = {
                    'passed': False,
                    'error': str(e)
                }
                results['failed'] += 1
                self.failed_checks.append(check_name)
        
        # Summary
        pass_rate = (results['passed'] / results['total_checks']) * 100
        logger.info(f"\n{'='*60}")
        logger.info(f"Quality Check Summary:")
        logger.info(f"  Total Checks: {results['total_checks']}")
        logger.info(f"  Passed: {results['passed']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info(f"  Pass Rate: {pass_rate:.1f}%")
        logger.info(f"{'='*60}\n")
        
        self.quality_report = results
        return results
    
    def get_report(self) -> Dict:
        """Get the quality check report"""
        return self.quality_report
    
    def has_failures(self) -> bool:
        """Check if any quality checks failed"""
        return len(self.failed_checks) > 0

# Test it
if __name__ == "__main__":
    # Create sample data
    sample_data = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com', 'e@test.com'],
        'created_date': pd.date_range('2025-01-01', periods=5)
    })
    
    checker = DataQualityChecker()
    
    # Define checks
    checks = {
        'no_nulls_in_id': lambda df: checker.check_null_values(df, ['id']),
        'unique_ids': lambda df: checker.check_unique_values(df, 'id'),
        'age_range': lambda df: checker.check_value_range(df, 'age', min_val=0, max_val=120),
        'min_row_count': lambda df: checker.check_row_count(df, min_rows=1),
        'valid_dates': lambda df: checker.check_date_range(df, 'created_date', start_date='2020-01-01')
    }
    
    results = checker.run_quality_checks(sample_data, checks)
    print(f"\nFinal Report: {results}")