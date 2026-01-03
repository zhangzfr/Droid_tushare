import logging
import sys
import os
from datetime import datetime

# Ensuer logs directory exists
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name=__name__, log_file=None, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    
    if log_file is None:
        log_file = f"{datetime.now().strftime('%Y%m%d')}.log"
    
    log_path = os.path.join(LOG_DIR, log_file)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate logs if logger already has handlers
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler)

    return logger

# Default logger instance
logger = setup_logger("tushare_duckdb")
