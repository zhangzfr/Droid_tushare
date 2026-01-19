import pandas as pd
import plotly.graph_objects as go
from dashboard.finance_data_loader import load_income, load_mainbz
from dashboard.finance_charts import plot_income_sankey
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

TICKERS_TO_TEST = [
    ("000001.SZ", "Ping An Bank (Financial)"),
    ("300124.SZ", "Inovance (Manufacturing, Complex Products)"),
    ("600519.SH", "Kweichow Moutai (Consumer, High Margin)"),
    ("601857.SH", "PetroChina (Energy, Heavy Asset)"), 
    ("601318.SH", "Ping An Insurance (Insurance, Complex)")
]

def verify_sankey(ts_code, name):
    print(f"\nTesting {ts_code} - {name}...")
    try:
        # Load Data (Simulate UI load)
        df_inc = load_income(ts_code, limit_periods=60)
        df_bz = load_mainbz(ts_code, limit_periods=500)
        
        if df_inc.empty:
            print(f"❌ Abort: No Income Data for {ts_code}")
            return False
            
        # Generate Plot
        fig = plot_income_sankey(df_bz, df_inc)
        
        if fig is None:
            print(f"❌ Failed: plot_income_sankey returned None for {ts_code}")
            return False
            
        # Inspect Figure Data
        if not fig.data:
            print(f"❌ Failed: Figure has no data traces for {ts_code}")
            return False
            
        sankey_data = fig.data[0]
        nodes = sankey_data.node.label
        links = sankey_data.link
        
        print(f"✅ Success: Generated Sankey with {len(nodes)} nodes and {len(links.source)} links.")
        
        # Check for NaNs
        vals = pd.Series(links.value)
        if vals.isna().any():
             print(f"⚠️ Warning: NaN found in link values for {ts_code}!")
             
        # Check for Disconnected Nodes (Basic check: sum(source) vs sum(target)?)
        # Just printing specific checks
        has_net_profit = any("净利润" in label for label in nodes)
        print(f"   Contains 'Net Profit' node: {has_net_profit}")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

print("="*50)
print("Starting Universal Sankey Verification")
print("="*50)

success_count = 0
for ts_code, name in TICKERS_TO_TEST:
    if verify_sankey(ts_code, name):
        success_count += 1
        
print("="*50)
print(f"Test Complete. Success: {success_count}/{len(TICKERS_TO_TEST)}")
if success_count == len(TICKERS_TO_TEST):
    print("🚀 ALL SYSTEMS GO!")
else:
    print("💥 SOME TESTS FAILED")
