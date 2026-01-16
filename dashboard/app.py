"""
Unified Dashboard Entry Point
============================
This is the main entry point for all visualizations.
Navigation hierarchy:
- Level 1: Data Category (Macro, Index, etc.)
- Level 2: Sub-category (PMI, Money Supply, etc.)
- Level 3: Specific content/charts
"""
import streamlit as st
import datetime
import sys
import os
import textwrap

# Add project root to sys.path so that 'dashboard' module can be imported
# This allows absolute imports like 'from dashboard.components import ...' to work
# when running streamlit from within the dashboard directory or outside it.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Page Configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="Tushare Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Components
from dashboard.components.styles import CUSTOM_CSS, NAV_CSS, ICONS
from dashboard.components.headers import render_header

# Import Pages
from dashboard.pages.home_page import render_home_page
from dashboard.pages.macro_page import render_macro_page
from dashboard.pages.index_page import render_index_page
from dashboard.pages.market_page import render_market_page
from dashboard.pages.vix_page import render_vix_page
from dashboard.pages.fx_page import render_fx_edu_page
from dashboard.pages.stock_page import render_stock_edu_page
from dashboard.pages.market_insights_page import render_market_insights_page
from dashboard.pages.finance_page import render_finance_page

# Apply Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(NAV_CSS, unsafe_allow_html=True)

# Helper function
def get_current_page():
    try:
        # Streamlit 1.30+
        return st.query_params.get("page", "home")
    except:
        try:
            # Older versions
            params = st.experimental_get_query_params()
            return params.get("page", ["home"])[0]
        except:
            return "home"

# ================================
# Navigation Configuration
# ================================
NAVIGATION = {
    "Home": {"key": "home", "icon": "home", "subcategories": {}},
    "Macro Data": {
        "key": "macro",
        "icon": "macro",
        "subcategories": {
            "GDP Data": {"key": "gdp", "icon": "gdp"},
            "PMI Index": {"key": "pmi", "icon": "pmi"},
            "Money Supply": {"key": "money_supply", "icon": "money"},
            "Social Financing": {"key": "social_financing", "icon": "social"},
            "Price Index": {"key": "price_index", "icon": "price"}
        }
    },
    "Index Data": {
        "key": "index",
        "icon": "index",
        "subcategories": {
            "Index List": {"key": "index_list", "icon": "list"},
            "Index Heatmap": {"key": "index_map", "icon": "heatmap"},
            "Shenwan Index": {"key": "sw_index", "icon": "industry"},
            "Market Width": {"key": "market_width", "icon": "bar"},
            "Index Constituents": {"key": "index_const", "icon": "pie"}
        }
    },
    "Market Data": {
        "key": "market",
        "icon": "market",
        "subcategories": {
            "Listing Stats": {"key": "listing_stats", "icon": "stats"},
            "Equity Pledge": {"key": "pledge_data", "icon": "pulse"},
            "Block Trade": {"key": "block_trade", "icon": "chart"},
            "Risk Radar": {"key": "risk_radar", "icon": "alert"}
        }
    },
    "Financial Data": {
        "key": "finance",
        "icon": "finance",
        "subcategories": {
            "Financial Analysis": {"key": "fin_analysis", "icon": "finance"}
        }
    },
    "Market Insights": {
        "key": "market_insights",
        "icon": "chart",
        "subcategories": {
            "Market Valuation": {"key": "mkt_valuation", "icon": "gauge"},
            "Market Sentiment": {"key": "mkt_sentiment", "icon": "pulse"},
            "Global Markets": {"key": "mkt_global", "icon": "globe"},
            "Market Trading Data": {"key": "mkt_trading", "icon": "exchange"},
            "Options Data": {"key": "mkt_option", "icon": "layers"}
        }
    },
    "VIX Calculator": {
        "key": "vix",
        "icon": "volatility",
        "subcategories": {
            "VIX Calculator": {"key": "vix_calc", "icon": "calc"},
            "Uplift Detection": {"key": "uplift_detect", "icon": "trend"}
        }
    },
    "A-Share Education": {
        "key": "stock_edu",
        "icon": "stock",
        "subcategories": {
            "1. Market Overview": {"key": "stock_overview", "icon": "market"},
            "2. Price Dynamics": {"key": "stock_price", "icon": "chart"},
            "3. Valuation Analysis": {"key": "stock_valuation", "icon": "valuation"},
            "4. Industry Analysis": {"key": "stock_industry", "icon": "industry"}
        }
    },
    "FX Education": {
        "key": "fx_edu",
        "icon": "fx",
        "subcategories": {
            "1. Asset Overview": {"key": "fx_assets", "icon": "asset"},
            "2. Price Dynamics": {"key": "fx_price", "icon": "chart"},
            "3. Correlations": {"key": "fx_corr", "icon": "correlation"},
            "4. Advanced Analysis": {"key": "fx_advanced", "icon": "analysis"}
        }
    }
}

# ================================
# Sidebar Generation
# ================================
with st.sidebar:

    
    # Get current page from URL or state
    current_key = get_current_page()
    
    # Determine the current active category based on the key
    active_category = None
    active_subcategory = None
    
    # Check if we are on home
    if current_key == "home":
        active_category = "Home"
    else:
        # Loop to find the category containing the key
        found = False
        for cat_name, cat_data in NAVIGATION.items():
            if cat_data["key"] == current_key:
                active_category = cat_name
                found = True
                break
            # Check subcategories
            for sub_name, sub_data in cat_data["subcategories"].items():
                if sub_data["key"] == current_key:
                    active_category = cat_name
                    active_subcategory = sub_name
                    found = True
                    break
            if found:
                break
    
    def mk_nav_item(link, text, active=False, is_sub=False):
        # Style calculation
        bg_color = "#EBE3DC" if active else "transparent"
        text_color = "#D97757" if active else "#5C5653"
        font_weight = "600" if active else ( "400" if is_sub else "500" )
        
        # Padding adjustment
        padding = "6px 12px 6px 12px" if is_sub else "8px 12px" # Added indent for sub-items conceptually via container, but let's keep it simple
        margin = "2px" if is_sub else "4px"
        
        # HTML template - Simple text link
        html = f"""<a href="{link}" target="_self" style="text-decoration: none; display: block; width: 100%;"><div style="display: flex; flex-direction: row; align-items: center; padding: {padding}; margin-bottom: {margin}; background-color: {bg_color}; border-radius: 6px; transition: background-color 0.2s;"><span style="color: {text_color}; font-weight: {font_weight}; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{text}</span></div></a>"""
        return html

    # Render Navigation
    for category, config in NAVIGATION.items():
        # Render category header/link
        is_active_cat = (category == active_category)
        
        # Create clickable category
        if not config["subcategories"]:
            # Single item (Home)
            nav_html = mk_nav_item(f"?page={config['key']}", category, active=is_active_cat)
            st.markdown(nav_html, unsafe_allow_html=True)
        else:
            # Category with subcategories - USE EXPANDER
            
            # Logic: If active category, expand by default
            expanded_state = is_active_cat
            
            # We use st.expander for the collapsible effect
            with st.expander(category, expanded=expanded_state):
                # Inside expander, we render the sub-links
                sub_nav_html = ""
                for sub_name, sub_config in config["subcategories"].items():
                    is_active_sub = (sub_name == active_subcategory) and (category == active_category)
                    
                    sub_nav_html += mk_nav_item(f"?page={sub_config['key']}", sub_name, active=is_active_sub, is_sub=True)
                
                st.markdown(sub_nav_html, unsafe_allow_html=True)

    # Footer
    st.divider()
    st.markdown(textwrap.dedent(f"""
    <div style="display: flex; align-items: center; gap: 8px; color: #8C8580; font-size: 0.75rem;">
        {ICONS["home"].replace('width="18"', 'width="14"').replace('height="18"', 'height="14"')}
        <span>Tushare Data Dashboard v1.1</span>
    </div>
    <div style="margin-left: 22px; color: #8C8580; font-size: 0.75rem;">Data Source: Tushare Pro</div>
    """), unsafe_allow_html=True)

# ================================
# Main Content Routing
# ================================

# Determine configuration for rendering
if active_category and active_category in NAVIGATION:
    category_config = NAVIGATION[active_category]
    category_key = category_config["key"]
    
    # If using subcategories, the key comes from the subcategory
    subcategory_key = None
    if active_subcategory:
         subcategory_key = category_config["subcategories"][active_subcategory]["key"]
    
    # --- ROUTER ---
    
    if category_key == "home":
        render_home_page()
        
    elif category_key == "macro":
        render_macro_page(subcategory_key)
        
    elif category_key == "index":
        render_index_page(subcategory_key)
        
    elif category_key == "market":
        render_market_page(subcategory_key)
        
    elif category_key == "vix":
        render_vix_page(subcategory_key)
        
    elif category_key == "stock_edu":
        render_stock_edu_page(subcategory_key)
        
    elif category_key == "fx_edu":
        render_fx_edu_page(subcategory_key)

    elif category_key == "finance":
        render_finance_page(subcategory_key)
        
    elif category_key == "market_insights":
        render_market_insights_page(subcategory_key)
        
    else:
        st.error(f"Unknown category: {category_key}")

else:
    # Default fallback (should not happen if logic is correct)
    render_home_page()
