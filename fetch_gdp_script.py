import sys
import os

# Add root directory to sys.path
sys.path.append(os.getcwd())

from src.tushare_duckdb.main import fetch_and_store_data
from datetime import datetime

msg = fetch_and_store_data(
    category='macro',
    start_date='1990Q1',
    end_date='2025Q4',
    selected_tables='cn_gdp',
    force_fetch=True
)

print(f"Stored {msg} records.")
