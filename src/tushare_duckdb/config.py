import os
import yaml
import tushare as ts
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ENV_PATH = os.getenv('ENV_PATH', '/Users/robert/.env')
load_dotenv(dotenv_path=ENV_PATH)

# Get Tushare Token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')
if not TUSHARE_TOKEN:
    # Warning instead of raise to allow importing config without token (e.g. during pydoc or tests)
    print("Warning: TUSHARE_TOKEN not found in environment variables.")
    PRO_API = None
else:
    ts.set_token(TUSHARE_TOKEN)
    PRO_API = ts.pro_api()

# Database Root Path
DB_ROOT = os.getenv('DB_ROOT', '/Users/robert/Developer/DuckDB')

def load_config():
    """Load configuration from settings.yaml"""
    # Find settings.yaml relative to project root or this file
    # Assuming this file is in src/tushare_duckdb/config.py
    # and settings.yaml is in project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    config_path = project_root / 'settings.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return config_data

def interpolate_config(config, db_root):
    """Recursively replace ${DB_ROOT} in configuration values"""
    if isinstance(config, dict):
        return {k: interpolate_config(v, db_root) for k, v in config.items()}
    elif isinstance(config, list):
        return [interpolate_config(i, db_root) for i in config]
    elif isinstance(config, str):
        return config.replace('${DB_ROOT}', db_root)
    else:
        return config

# Load and process configuration
_raw_config = load_config()
API_CONFIG = interpolate_config(_raw_config, DB_ROOT)

# Export Database Paths for backward compatibility
# These are derived from the loaded config to ensure consistency
try:
    BASIC_DB_PATH = API_CONFIG.get('stock_list', {}).get('db_path') or API_CONFIG.get('stock_info', {}).get('db_path')
    STOCK_DB_PATH = API_CONFIG.get('stock', {}).get('db_path')
    MARGIN_DB_PATH = API_CONFIG.get('margin', {}).get('db_path')
    MONEYFLOW_DB_PATH = API_CONFIG.get('moneyflow', {}).get('db_path')
    REF_DB_PATH = API_CONFIG.get('reference', {}).get('db_path')
    FINANCE_DB_PATH = API_CONFIG.get('finance', {}).get('db_path')
    INDEX_DB_PATH = API_CONFIG.get('index_info', {}).get('db_path') # Note: key is index_info in yaml
    INDEX_WEIGHT_DB_PATH = API_CONFIG.get('index_weight', {}).get('db_path')
    FUND_DB_PATH = API_CONFIG.get('fund', {}).get('db_path')
    BOND_DB_PATH = API_CONFIG.get('bond', {}).get('db_path')
    OPT_DB_PATH = API_CONFIG.get('option', {}).get('db_path')
    FUTURE_DB_PATH = API_CONFIG.get('future', {}).get('db_path')
    MARCO_DB_PATH = API_CONFIG.get('marco', {}).get('db_path')
    # HK_DB_PATH seemed unused in original config or was commented out/not in a group, 
    # but we define it if needed or leave it out if it wasn't in API_CONFIG keys.
    # Checking original file, HK_DB_PATH was defined but not used in API_CONFIG keys shown in view.
except KeyError as e:
    print(f"Warning: Could not load some database paths from config: {e}")