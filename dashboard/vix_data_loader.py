"""
VIX Data Loader for Dashboard
==============================
Wraps the VIX calculation logic for use in the Streamlit dashboard.
"""
import sys
import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Add src to path for importing vix module
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from vix.data_loader import fetch_option_data, get_shibor_interpolated
from vix.calculator import calculate_vix_for_date
from vix.config import ETF_OPTIONS, INDEX_OPTIONS


def get_available_underlyings():
    """
    Get list of available underlying assets for VIX calculation.
    Returns a dict with code as key and display name as value.
    """
    result = {}
    for code, info in ETF_OPTIONS.items():
        result[code] = f"{code} - {info['name']}"
    for code, info in INDEX_OPTIONS.items():
        result[code] = f"{code} - {info['name']}"
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def calculate_vix_series(start_date: str, end_date: str, underlying: str = '510050.SH'):
    """
    Calculate VIX for a date range.
    
    Args:
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        underlying: Underlying ETF/Index code
        
    Returns:
        Tuple of (df_summary, df_details_near, df_details_next)
    """
    try:
        # Load option data
        options_all = fetch_option_data(start_date, end_date, underlying)
        if options_all.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Load Shibor data
        shibor_interp = get_shibor_interpolated(start_date, end_date)
        if shibor_interp.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
    except Exception as e:
        st.error(f"Data loading failed: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Calculate VIX for each trading day
    dates = sorted(options_all['date'].unique())
    
    results = []
    all_details = []
    
    for current_date in dates:
        # Filter options for this date
        daily_opts = options_all[options_all['date'] == current_date]
        
        # Get Shibor rate for this date
        try:
            daily_shibor = shibor_interp.loc[current_date]
        except KeyError:
            continue
        
        # Calculate VIX
        result_dict = calculate_vix_for_date(current_date, daily_opts, daily_shibor)
        
        if result_dict is not None:
            # Extract details
            details_df = result_dict.pop('details')
            
            # Summary Record
            result_record = {
                'date': current_date,
                'date_str': current_date.strftime('%Y%m%d')
            }
            result_record.update(result_dict)
            results.append(result_record)
            
            # Details Record
            all_details.append(details_df)
    
    if not results:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    df_summary = pd.DataFrame(results)
    
    # Process details
    df_details_near = pd.DataFrame()
    df_details_next = pd.DataFrame()
    
    if all_details:
        df_details = pd.concat(all_details)
        df_details_near = df_details[df_details['term_type'] == 'near'].copy()
        df_details_next = df_details[df_details['term_type'] == 'next'].copy()
    
    return df_summary, df_details_near, df_details_next


def get_default_date_range():
    """Get default date range for VIX calculation (last 30 trading days)."""
    today = datetime.now()
    # Adjust for weekend
    if today.weekday() >= 5:
        today = today - timedelta(days=today.weekday() - 4)
    
    end_date = today
    start_date = end_date - timedelta(days=45)  # ~30 trading days
    
    return start_date, end_date
