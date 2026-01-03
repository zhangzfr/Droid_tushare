import sys
import os

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), 'src'))

print("Beginning import verifications...")

try:
    print("1. Testing config import...")
    from tushare_duckdb.config import API_CONFIG, DB_ROOT
    print(f"   Config loaded. DB_ROOT: {DB_ROOT}")
    
    print("2. Testing logger import...")
    from tushare_duckdb.logger import logger
    logger.info("   Logger verification message.")
    
    print("3. Testing modules import...")
    from tushare_duckdb.fetcher import TushareFetcher
    from tushare_duckdb.storage import DuckDBStorage
    from tushare_duckdb.processor import DataProcessor
    print("   Core modules imported successfully.")
    
    print("4. Testing main import...")
    from tushare_duckdb.main import main
    print("   Main module imported.")

    print("\nSUCCESS: All modules verified successfully.")
    
except Exception as e:
    print(f"\nFAILURE: Verification failed with error: {e}")
    sys.exit(1)
