import os
import yaml
from pathlib import Path

# Database Root Path
# Try to get from env or default
DB_ROOT = os.getenv('DB_ROOT', '/Users/robert/Developer/DuckDB')

def load_config():
    """Load configuration from settings.yaml"""
    # Assuming this file is in src/vix/config.py
    # settings.yaml is in project root (../../settings.yaml)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    config_path = project_root / 'settings.yaml'
    
    if not config_path.exists():
        # Fallback if not found relative to here
        config_path = Path('/Users/robert/Developer/ProjectQuant/tushare/tushare_2_duckdb/Droid_tushare/settings.yaml')
        
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

_raw_config = load_config()
API_CONFIG = interpolate_config(_raw_config, DB_ROOT)

OPT_DB_PATH = API_CONFIG.get('option', {}).get('db_path')
MARCO_DB_PATH = API_CONFIG.get('marco', {}).get('db_path')
