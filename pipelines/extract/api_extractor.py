import requests
import pandas as pd
from loguru import logger

class APIExtractor:
    def __init__(self):
        self.session = requests.Session()
    
    def extract_from_api(self, url, source_name):
        """Extract data from REST API"""
        try:
            logger.info(f"Fetching data from {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            df = pd.DataFrame(data)
            
            logger.info(f"✓ Extracted {len(df)} records from {source_name}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Failed to fetch from {url}: {e}")
            raise
    
    def extract_sample_data(self):
        """Extract from a free sample API"""
        url = "https://jsonplaceholder.typicode.com/users"
        return self.extract_from_api(url, "sample_users")

# Test it
if __name__ == "__main__":
    extractor = APIExtractor()
    df = extractor.extract_sample_data()
    print(df.head())
    print(f"\nShape: {df.shape}")
