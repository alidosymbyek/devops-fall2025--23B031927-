"""
Test SSL/TLS connection to PostgreSQL database
"""
import sys
import os
from pathlib import Path

# Add pipelines to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'pipelines'))

from db_connector import DatabaseConnector


def test_ssl_connection():
    """Test SSL connection to database"""
    print("=" * 60)
    print("Testing SSL/TLS Database Connection")
    print("=" * 60)
    
    # Set SSL configuration
    os.environ['DB_SSL_MODE'] = 'require'
    
    # Set CA certificate path if it exists
    ca_path = Path(__file__).parent.parent / 'postgres-ssl' / 'ca.crt'
    if ca_path.exists():
        os.environ['DB_SSL_CA_PATH'] = str(ca_path)
        print(f"Using CA certificate: {ca_path}")
    else:
        print("Warning: CA certificate not found. Using default SSL mode.")
    
    try:
        db = DatabaseConnector()
        print(f"\nConnection details:")
        print(f"  Host: {db.host}")
        print(f"  Port: {db.port}")
        print(f"  Database: {db.database}")
        print(f"  SSL Mode: {db.ssl_mode}")
        print(f"  CA Path: {db.ssl_ca_path or 'Not set'}")
        
        print("\nAttempting connection...")
        if db.test_connection():
            print("\n✓ SUCCESS: SSL connection established!")
            return True
        else:
            print("\n✗ FAILED: Could not establish connection")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False


def test_non_ssl_connection():
    """Test that non-SSL connections are rejected (if SSL is required)"""
    print("\n" + "=" * 60)
    print("Testing Non-SSL Connection (should fail if SSL required)")
    print("=" * 60)
    
    # Try without SSL
    os.environ['DB_SSL_MODE'] = 'disable'
    
    try:
        db = DatabaseConnector()
        if db.test_connection():
            print("⚠ WARNING: Non-SSL connection succeeded (SSL may not be enforced)")
            return False
        else:
            print("✓ SUCCESS: Non-SSL connection rejected (SSL is enforced)")
            return True
    except Exception as e:
        print(f"✓ SUCCESS: Non-SSL connection rejected: {e}")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Database SSL/TLS Connection Test Suite")
    print("=" * 60 + "\n")
    
    # Test 1: SSL connection
    ssl_test = test_ssl_connection()
    
    # Test 2: Non-SSL connection (should fail)
    non_ssl_test = test_non_ssl_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"SSL Connection: {'PASSED' if ssl_test else 'FAILED'}")
    print(f"SSL Enforcement: {'PASSED' if non_ssl_test else 'FAILED'}")
    
    if ssl_test and non_ssl_test:
        print("\n✓ All SSL tests passed!")
    else:
        print("\n⚠ Some tests failed. Check your SSL configuration.")

