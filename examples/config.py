# ts_config.py
import os
from dotenv import load_dotenv
import logging
import pandas as pd
import duckdb
import tushare as ts
from datetime import datetime
from pathlib import Path
import json

# 加载 .env 文件
ENV_PATH = '/Users/robert/.env'
load_dotenv(dotenv_path=ENV_PATH)

# 获取 Tushare Token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')
if not TUSHARE_TOKEN:
    raise ValueError("Tushare Token 未在 .env 文件中找到，请检查配置")

# 配置 Tushare
ts.set_token(TUSHARE_TOKEN)
PRO_API = ts.pro_api()

def pagenation(api_name, limit=5000, **kwargs):
    offset = 0
    df = PRO_API.query(api_name, offset=offset, **kwargs)
    if df.empty:
        return df
    df_all = []
    df_all.append(df)

    while df.index.size == limit:
        offset += limit
        df = PRO_API.query(api_name, offset=offset, **kwargs)
        df_all.append(df)
        if df.index.size < limit:
            break

    return pd.concat(df_all)