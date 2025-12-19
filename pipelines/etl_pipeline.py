import sys
import yaml
from pathlib import Path
from datetime import datetime
from loguru import logger
from monitoring.email_alerts import EmailAlertManager

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from extract.csv_extractor import CSVExtractor
from extract.api_extractor import APIExtractor
from transform.data_transformer import DataTransformer
from load.data_loader import DataLoader

class ETLPipeline:
    def __init__(self, pipeline_name='main_etl'):
        self.pipeline_name = pipeline_name
        
        # Load config to check if file writing is enabled
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        write_files = False
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    write_files = config.get('pipeline', {}).get('write_intermediate_files', False)
                    logger.info(f"File writing enabled: {write_files}")
        except Exception as e:
            logger.warning(f"Could not read config for file writing setting: {e}")
        
        self.csv_extractor = CSVExtractor()
        self.api_extractor = APIExtractor()
        self.transformer = DataTransformer(write_files=write_files)
        self.loader = DataLoader(write_files=write_files)
        self.alert_manager = EmailAlertManager()
        
        # Setup logging
        log_path = Path(__file__).parent.parent / 'logs'
        log_path.mkdir(exist_ok=True)
        logger.add(
            log_path / f"{pipeline_name}_{datetime.now().strftime('%Y%m%d')}.log",
            rotation="1 day",
            retention="30 days"
        )
    
    def run(self):
        """Execute the complete ETL pipeline"""
        start_time = datetime.now()
        total_records = 0
        status = 'SUCCESS'
        error_message = None
        
        try:
            logger.info(f"{'='*60}")
            logger.info(f"Starting {self.pipeline_name} pipeline")
            logger.info(f"{'='*60}")
            
            # EXTRACT
            logger.info("\n[1/3] EXTRACT Phase")
            logger.info("-" * 40)
            
            # Extract from CSV
            csv_data = self.csv_extractor.extract_all_csvs()
            
            # Extract from API
            try:
                api_data = self.api_extractor.extract_sample_data()
                csv_data['api_users'] = api_data
            except Exception as e:
                logger.warning(f"API extraction failed: {e}")
            
            if not csv_data:
                logger.warning("No data extracted!")
                return
            
            # TRANSFORM
            logger.info("\n[2/3] TRANSFORM Phase")
            logger.info("-" * 40)
            
            transformed_data = {}
            for source_name, df in csv_data.items():
                transformed_df = self.transformer.transform(df, source_name)
                transformed_data[source_name] = transformed_df
                total_records += len(transformed_df)
            
            # LOAD
            logger.info("\n[3/3] LOAD Phase")
            logger.info("-" * 40)
            
            for source_name, df in transformed_data.items():
                # Create safe table name
                table_name = source_name.lower().replace('-', '_')
                self.loader.load_to_staging(df, table_name)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Pipeline completed successfully!")
            logger.info(f"  Total records processed: {total_records}")
            logger.info(f"  Duration: {duration:.2f} seconds")
            logger.info(f"{'='*60}\n")
            self.alert_manager.send_pipeline_success_alert(
                self.pipeline_name, 
                total_records, 
                duration
            )
            
        except Exception as e:
            status = 'FAILED'
            error_message = str(e)
            end_time = datetime.now()
            logger.error(f"\n{'='*60}")
            logger.error(f"✗ Pipeline failed: {e}")
            logger.error(f"{'='*60}\n")
            
            # Send alerts immediately on failure (within seconds, well under 2 minutes)
            execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Send email alert
            try:
                self.alert_manager.send_pipeline_failure_alert(
                    self.pipeline_name,
                    str(e),
                    execution_time
                )
            except Exception as alert_error:
                logger.error(f"Failed to send email alert: {alert_error}")
            
            # Send Slack alert if configured
            try:
                from monitoring.slack_alerts import SlackAlertManager
                slack_alerts = SlackAlertManager()
                slack_alerts.send_pipeline_failure_alert(
                    self.pipeline_name,
                    str(e),
                    execution_time
                )
            except Exception as slack_error:
                logger.debug(f"Slack alert not sent (may not be configured): {slack_error}")
            
            raise
        
        finally:
            # Log execution
            self.loader.log_pipeline_execution(
                pipeline_name=self.pipeline_name,
                status=status,
                records_processed=total_records,
                start_time=start_time,
                end_time=end_time,
                error_message=error_message
            )

def main():
    pipeline = ETLPipeline('daily_etl')
    pipeline.run()

if __name__ == "__main__":
    main()