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

# Page Configuration
st.set_page_config(
    page_title="📊 Tushare Data Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Anthropic-style design system
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ===== Global Typography ===== */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.6;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    h1 { font-size: 2rem; }
    h2 { font-size: 1.5rem; }
    h3 { font-size: 1.25rem; }
    
    /* ===== Sidebar Styling ===== */
    [data-testid="stSidebar"] {
        background-color: #FAF5F0;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.9rem;
        color: #5C5653;
    }
    
    /* Sidebar title */
    [data-testid="stSidebar"] h1 {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1A1A1A;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #E8E0D8;
        margin-bottom: 1rem;
    }
    
    /* Radio buttons - Anthropic style */
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #5C5653;
        margin-bottom: 0.25rem;
    }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] {
        gap: 0.25rem;
    }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
        padding: 0.5rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.9rem;
        font-weight: 400;
        transition: all 0.15s ease;
    }
    
    [data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {
        background-color: #F0E8E0;
    }
    
    /* ===== Main Content Area ===== */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    /* Cards / Containers */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1.5rem;
        background: white;
        border-radius: 0.75rem;
        border: 1px solid #E8E0D8;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: #FDFBF9;
        border: 1px solid #E8E0D8;
        border-radius: 0.75rem;
        padding: 1rem;
    }
    
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        font-weight: 500;
        color: #5C5653;
    }
    
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1A1A1A;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        border-radius: 0.75rem;
        border: none;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 500;
        border: 1px solid #E8E0D8;
        transition: all 0.15s ease;
    }
    
    .stButton > button:hover {
        border-color: #D97757;
        color: #D97757;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border-radius: 0.75rem;
        overflow: hidden;
        border: 1px solid #E8E0D8;
    }
    
    /* Selectbox */
    .stSelectbox [data-baseweb="select"] {
        border-radius: 0.5rem;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #E8E0D8;
        margin: 1.5rem 0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid #E8E0D8;
        padding-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem 0.5rem 0 0;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* Caption text */
    .stCaption {
        color: #8C8580;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ================================
# Navigation Structure with Lucide-style icons (SVG)
# ================================
# SVG icons inspired by Lucide (similar to Anthropic's icon set)
ICONS = {
    "home": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>''',
    "macro": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>''',
    "index": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>''',
    "pmi": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>''',
    "money": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 18V6"/></svg>''',
    "social": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>''',
    "list": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>''',
    "detail": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>''',
    "calendar": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>''',
    "filter": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>''',
    "stock": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/><line x1="7" x2="7" y1="10" y2="17"/><line x1="17" x2="17" y1="10" y2="17"/></svg>''',
    "listing": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>''',
    "heatmap": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="7" width="3" height="3"/><rect x="11" y="7" width="3" height="3"/><rect x="15" y="7" width="3" height="3"/><rect x="7" y="11" width="3" height="3"/><rect x="11" y="11" width="3" height="3"/><rect x="15" y="11" width="3" height="3"/><rect x="7" y="15" width="3" height="3"/><rect x="11" y="15" width="3" height="3"/><rect x="15" y="15" width="3" height="3"/></svg>'''
}

NAVIGATION = {
    "Home": {"key": "home", "icon": "home", "subcategories": {}},
    "Macro Data": {
        "key": "macro", 
        "icon": "macro",
        "subcategories": {
            "PMI Index": {"key": "pmi", "icon": "pmi"},
            "Money Supply": {"key": "money_supply", "icon": "money"},
            "Social Financing": {"key": "social_financing", "icon": "social"}
        }
    },
    "Index Data": {
        "key": "index",
        "icon": "index", 
        "subcategories": {
            "Index List": {"key": "index_list", "icon": "list"},
            "Index Heatmap": {"key": "index_heatmap", "icon": "heatmap"},
            "Constituents": {"key": "index_details", "icon": "detail"}
        }
    },
    "Market Data": {
        "key": "stock",
        "icon": "stock",
        "subcategories": {
            "Listing Statistics": {"key": "listing_stats", "icon": "listing"}
        }
    }
}

# ================================
# Sidebar Navigation - Anthropic Style (HTML/CSS + Query Param)
# ================================

# Helper to get current page from query params
# Support both new st.query_params and old st.experimental_get_query_params
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

# Helper to get subcategory
def get_current_sub():
    try:
        return st.query_params.get("sub", "")
    except:
        try:
            params = st.experimental_get_query_params()
            return params.get("sub", [""])[0]
        except:
            return ""

# Get current state
current_page = get_current_page()
current_sub = get_current_sub()

# Determine active top-level category
active_category_key = "home" # Default
active_category_config = NAVIGATION["Home"]

# Find which category owns the current page or is the current page
# Structure of NAVIGATION: Name -> {key, icon, subcategories: {Name -> {key, icon}}}
for cat_name, cat_config in NAVIGATION.items():
    if cat_config["key"] == current_page:
        active_category_key = cat_name
        active_category_config = cat_config
        break
    
    # Check subcategories
    for sub_name, sub_config in cat_config["subcategories"].items():
        if sub_config["key"] == current_page:
            active_category_key = cat_name
            active_category_config = cat_config
            break

# Custom CSS for the navigation
st.markdown("""
<style>
    /* Hide default streamlit sidebar styling if needed to minimize clutter */
    
    /* Navigation Link Styles */
    a.nav-link {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        margin-bottom: 4px;
        border-radius: 6px;
        text-decoration: none !important;
        color: #5C5653 !important;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    a.nav-link:hover {
        background-color: #F0E8E0;
        color: #1A1A1A !important;
    }
    
    a.nav-link.active {
        background-color: #F0E8E0;
        color: #D97757 !important;
        font-weight: 600;
    }
    
    a.nav-link svg {
        width: 18px;
        height: 18px;
        stroke-width: 2px;
        opacity: 0.7;
    }
    
    a.nav-link.active svg {
        opacity: 1;
        stroke: #D97757;
    }
    
    .nav-header {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8C8580;
        margin-top: 24px;
        margin-bottom: 8px;
        padding-left: 12px;
    }
    
    .nav-divider {
        height: 1px;
        background-color: #E8E0D8;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

# Generate HTML for sidebar - single line to avoid markdown code block issues
sidebar_html = '<div class="nav-section"><div class="nav-header">Navigation</div>'
# Level 1 Links
for cat_name, cat_config in NAVIGATION.items():
    key = cat_config["key"]
    icon = ICONS.get(cat_config["icon"], "")
    
    # Check if this category is active (either directly or via children)
    is_active = (cat_name == active_category_key)
    active_class = "active" if is_active and not current_sub else ""
    
    # If it has subcategories, clicking it should probably go to the first subcategory or stays as container?
    # For this app model, clicking the Category Name opens that section.
    # If we are strictly following the previous logic, "macro" was a key itself.
    # We will target the main key.
    
    # URL construction
    # Using window.parent.location logic via target="_self" usually works in Streamlit
    target_url = f"?page={key}"
    
    # SVG Icon injection - ONE LINE to prevent Markdown code block issues
    sidebar_html += f'<a href="{target_url}" target="_self" class="nav-link {active_class}">{icon}<span>{cat_name}</span></a>'

# Level 2 Links (if active category has subcategories)
subcategories = active_category_config.get("subcategories", {})
if subcategories:
    sidebar_html += '<div class="nav-divider"></div><div class="nav-header">Sub-category</div>'
    
    for sub_name, sub_config in subcategories.items():
        sub_key = sub_config["key"]
        icon = ICONS.get(sub_config["icon"], "")
        
        target_url = f"?page={active_category_config['key']}&sub={sub_key}"
        is_sub_active = (sub_key == current_sub) or (active_category_config["key"] == current_page and sub_key == current_sub)
        
        active_class = "active" if is_sub_active else ""
        
        sidebar_html += f'<a href="{target_url}" target="_self" class="nav-link {active_class}">{icon}<span>{sub_name}</span></a>'

sidebar_html += "</div>"


# Render Sidebar
st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)
st.sidebar.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)

# Helper to render sidebar section header with SVG icon
def render_sidebar_header(title, icon_name=None):
    icon_html = ""
    if icon_name and icon_name in ICONS:
        icon_svg = ICONS[icon_name]
        # Adjust size for sidebar header
        icon_svg = icon_svg.replace('width="16"', 'width="14"').replace('height="16"', 'height="14"')
        icon_svg = icon_svg.replace('width="18"', 'width="14"').replace('height="18"', 'height="14"')
        icon_html = f'<span style="display: inline-flex; align-items: center; margin-right: 6px; opacity: 0.8;">{icon_svg}</span>'
    
    st.sidebar.markdown(f"""
    <div style="
        font-size: 0.75rem; 
        font-weight: 700; 
        text-transform: uppercase; 
        letter-spacing: 0.05em; 
        color: #8C8580; 
        margin-top: 1rem; 
        margin-bottom: 0.5rem; 
        display: flex; 
        align-items: center;
    ">
        {icon_html}
        <span>{title}</span>
    </div>
    """, unsafe_allow_html=True)

# ================================
# State Synchronization for Main Content
# ================================
# Update the variables used by the rest of the script based on URL params
category_config = active_category_config
subcategory_key = current_sub

# If we are in a category with subs but no sub selected, default to first?
# The previous logic had `if not st.session_state.nav_subcategory: ... attributes[0]`
# We replicate that safety check.
if subcategories and not subcategory_key:
    # Default to first subcategory
    first_sub_name = list(subcategories.keys())[0]
    subcategory_key = subcategories[first_sub_name]["key"]


# ================================
# Main Content Area
# ================================

# Helper for consistent page headers with SVG icons
def render_header(title, icon_name=None):
    icon_html = ""
    if icon_name and icon_name in ICONS:
        # Get icon SVG and add custom styling for header
        icon_svg = ICONS[icon_name]
        # Inject style into SVG string simply by string replacement (a bit hacky but works without XML parsing)
        icon_svg = icon_svg.replace('width="16"', 'width="28"').replace('height="16"', 'height="28"')
        icon_svg = icon_svg.replace('width="18"', 'width="28"').replace('height="18"', 'height="28"')
        icon_html = f'<span style="display: inline-block; vertical-align: middle; margin-right: 12px; color: #D97757;">{icon_svg}</span>'
        
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
        {icon_html}
        <h2 style="margin: 0; font-size: 1.75rem; font-weight: 600; color: #1A1A1A;">{title}</h2>
    </div>
    """, unsafe_allow_html=True)

# --- HOME PAGE ---
if category_config["key"] == "home":
    # Decorative banner with Anthropic-inspired gradient
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #D97757 0%, #C4694A 100%);
        padding: 3.5rem 2.5rem;
        border-radius: 1.25rem;
        margin-bottom: 2.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(217, 119, 87, 0.25);
    ">
        <h1 style="margin: 0; font-size: 2.25rem; font-weight: 600; letter-spacing: -0.02em;">Data Visualization Platform</h1>
        <p style="margin: 0.75rem 0 0 0; opacity: 0.9; font-size: 1rem; font-weight: 400;">Quantitative Investment Data Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Features")
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    # Get Icons for cards
    macro_icon = ICONS['macro'].replace('width="18"', 'width="32"').replace('height="18"', 'height="32"')
    index_icon = ICONS['index'].replace('width="18"', 'width="32"').replace('height="18"', 'height="32"')
    stock_icon = ICONS['stock'].replace('width="18"', 'width="32"').replace('height="18"', 'height="32"')
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #E8E0D8;
            height: 100%;
        ">
            <div style="margin-bottom: 1rem; color: #D97757; opacity: 0.9;">{macro_icon}</div>
            <h4 style="margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 600; color: #1A1A1A;">Macro Data</h4>
            <ul style="margin: 0; padding-left: 1.25rem; color: #5C5653; font-size: 0.85rem; line-height: 1.8;">
                <li>PMI Manufacturing Index</li>
                <li>Money Supply (M0/M1/M2)</li>
                <li>Social Financing</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #E8E0D8;
            height: 100%;
        ">
            <div style="margin-bottom: 1rem; color: #D97757; opacity: 0.9;">{index_icon}</div>
            <h4 style="margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 600; color: #1A1A1A;">Index Data</h4>
            <ul style="margin: 0; padding-left: 1.25rem; color: #5C5653; font-size: 0.85rem; line-height: 1.8;">
                <li>Index List & Filtering</li>
                <li>Constituent Weights</li>
                <li>Historical Changes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 0.75rem;
            border: 1px solid #E8E0D8;
            height: 100%;
        ">
            <div style="margin-bottom: 1rem; color: #D97757; opacity: 0.9;">{stock_icon}</div>
            <h4 style="margin: 0 0 0.75rem 0; font-size: 1rem; font-weight: 600; color: #1A1A1A;">Market Data</h4>
            <ul style="margin: 0; padding-left: 1.25rem; color: #5C5653; font-size: 0.85rem; line-height: 1.8;">
                <li>Listing Statistics</li>
                <li>Stock Basic Info</li>
                <li>Market Overview</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Use the sidebar to navigate between data categories")

# --- MACRO DATA ---
elif category_config["key"] == "macro":
    # Import macro data modules
    from data_loader import load_pmi_data, load_sf_data, load_m_data
    from charts import (plot_pmi_trend, plot_sub_indicators_bar, plot_heatmap, 
                        plot_sf_charts, plot_m_levels, plot_m_yoy, plot_m_mom)
    import pandas as pd
    
    # Load all macro data
    with st.spinner('Loading macro data...'):
        df_pmi = load_pmi_data()
        df_sf = load_sf_data()
        df_m = load_m_data()
    
    # Date filtering in sidebar
    all_dates = pd.concat([df_pmi['month'], df_sf['month'], df_m['month']]).dropna()
    if not all_dates.empty:
        min_date = all_dates.min().date()
        max_date = all_dates.max().date()
        
        render_sidebar_header("Date Filter", "calendar")
        start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
        
        # Filter helper
        def filter_df(df, start, end):
            if df.empty: return df
            mask = (df['month'].dt.date >= start) & (df['month'].dt.date <= end)
            return df.loc[mask]
        
        df_pmi_f = filter_df(df_pmi, start_date, end_date)
        df_sf_f = filter_df(df_sf, start_date, end_date)
        df_m_f = filter_df(df_m, start_date, end_date)
    else:
        df_pmi_f, df_sf_f, df_m_f = df_pmi, df_sf, df_m
    
    # --- PMI Sub-category ---
    if subcategory_key == "pmi":
        render_header("PMI Manufacturing Index", "pmi")
        
        if df_pmi_f.empty:
            st.warning("No PMI data available")
        else:
            tab1, tab2, tab3 = st.tabs(["Trend", "Heatmap Analysis", "Raw Data"])
            
            with tab1:
                fig_trend = plot_pmi_trend(df_pmi_f)
                if fig_trend:
                    st.plotly_chart(fig_trend, use_container_width=True)
            
            with tab2:
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.subheader("Sub-indicators Heatmap")
                    fig_heatmap = plot_heatmap(df_pmi_f)
                    if fig_heatmap:
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                
                with col2:
                    st.subheader("Latest Month Breakdown")
                    if not df_pmi_f.empty:
                        latest = df_pmi_f['month'].max()
                        st.markdown(f"**Report Period:** {latest.strftime('%Y-%m')}")
                        df_latest = df_pmi_f[df_pmi_f['month'] == latest]
                        fig_bar = plot_sub_indicators_bar(df_latest)
                        if fig_bar:
                            st.plotly_chart(fig_bar, use_container_width=True)
            
            with tab3:
                st.dataframe(df_pmi_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Money Supply Sub-category ---
    elif subcategory_key == "money_supply":
        render_header("Money Supply (M0/M1/M2)", "money")
        
        if df_m_f.empty:
            st.warning("No money supply data available")
        else:
            tab1, tab2, tab3 = st.tabs(["Levels", "Growth Rates", "Raw Data"])
            
            with tab1:
                fig_levels = plot_m_levels(df_m_f)
                if fig_levels:
                    st.plotly_chart(fig_levels, use_container_width=True)
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Year-over-Year (YoY)")
                    fig_yoy = plot_m_yoy(df_m_f)
                    if fig_yoy:
                        st.plotly_chart(fig_yoy, use_container_width=True)
                with col2:
                    st.subheader("Month-over-Month (MoM)")
                    fig_mom = plot_m_mom(df_m_f)
                    if fig_mom:
                        st.plotly_chart(fig_mom, use_container_width=True)
            
            with tab3:
                st.dataframe(df_m_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Social Financing Sub-category ---
    elif subcategory_key == "social_financing":
        render_header("Social Financing", "social")
        
        if df_sf_f.empty:
            st.warning("No social financing data available")
        else:
            tab1, tab2 = st.tabs(["Charts", "Raw Data"])
            
            with tab1:
                fig_inc, fig_cum, fig_stk = plot_sf_charts(df_sf_f)
                if fig_inc:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Monthly Increment")
                        st.plotly_chart(fig_inc, use_container_width=True)
                        st.subheader("Cumulative Value")
                        st.plotly_chart(fig_cum, use_container_width=True)
                    with col2:
                        st.subheader("Stock End Value")
                        st.plotly_chart(fig_stk, use_container_width=True)
            
            with tab2:
                st.dataframe(df_sf_f.sort_values('month', ascending=False), use_container_width=True)

# --- INDEX DATA ---
elif category_config["key"] == "index":
    # Import index data modules
    from index_data_loader import (
        load_index_basic, get_indices_with_weight_data,
        get_constituent_count_per_date, get_available_trade_dates,
        get_constituents_for_date, load_major_indices_daily
    )
    from index_charts import plot_constituent_count_over_time, plot_index_heatmap
    
    # Load index data
    with st.spinner('Loading index data...'):
        df_indices = load_index_basic()
        indices_with_weight = get_indices_with_weight_data()
    
    if df_indices.empty:
        st.error("Unable to load index data. Please check database connection.")
        st.stop()
    
    # --- Index List Sub-category ---
    if subcategory_key == "index_list":
        render_header("Index List", "list")
        
        # Filters in sidebar
        render_sidebar_header("Filters", "filter")
        markets = ['All'] + sorted(df_indices['market'].dropna().unique().tolist())
        publishers = ['All'] + sorted(df_indices['publisher'].dropna().unique().tolist())
        
        sel_market = st.sidebar.selectbox("Market", markets)
        sel_publisher = st.sidebar.selectbox("Publisher", publishers)
        
        df_filtered = df_indices.copy()
        if sel_market != 'All':
            df_filtered = df_filtered[df_filtered['market'] == sel_market]
        if sel_publisher != 'All':
            df_filtered = df_filtered[df_filtered['publisher'] == sel_publisher]
        
        df_filtered['has_weight'] = df_filtered['ts_code'].isin(indices_with_weight)
        
        st.markdown(f"**Total {len(df_filtered)} indices, {df_filtered['has_weight'].sum()} with weight data**")
        
        display_cols = ['ts_code', 'name', 'market', 'publisher', 'index_type', 'category',
                        'base_date', 'base_point', 'list_date', 'has_weight']
        
        st.dataframe(
            df_filtered[display_cols],
            use_container_width=True,
            height=600,
            column_config={
                "ts_code": "Code",
                "name": "Name",
                "market": "Market",
                "publisher": "Publisher",
                "index_type": "Type",
                "category": "Category",
                "base_date": "Base Date",
                "base_point": st.column_config.NumberColumn("Base Point", format="%.2f"),
                "list_date": "List Date",
                "has_weight": st.column_config.CheckboxColumn("Has Weight")
            }
        )
    
    # --- Index Heatmap Sub-category ---
    elif subcategory_key == "index_heatmap":
        render_header("Major Indices Performance", "heatmap")
        
        # Sidebar filters for date range
        render_sidebar_header("Date Range", "calendar")
        
        # Default to last 60 days
        from datetime import datetime, timedelta
        default_end = datetime.now()
        default_start = default_end - timedelta(days=60)
        
        start_date = st.sidebar.date_input("Start Date", default_start)
        end_date = st.sidebar.date_input("End Date", default_end)
            
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        with st.spinner('Fetching performance data...'):
            df_heatmap = load_major_indices_daily(start_str, end_str)
            
        if df_heatmap.empty:
            st.warning(f"No performance data found between {start_str} and {end_str}")
        else:
            fig_heatmap = plot_index_heatmap(df_heatmap)
            if fig_heatmap:
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
            with st.expander("View Daily Change Data"):
                # Pivot for tabular display
                pivot_display = df_heatmap.pivot(index='trade_date', columns='ts_code', values='pct_chg').sort_index(ascending=False)
                st.dataframe(pivot_display, use_container_width=True)
    
    # --- Index Details Sub-category ---
    elif subcategory_key == "index_details":
        render_header("Index Constituents", "detail")
        
        if not indices_with_weight:
            st.warning("No index weight data available in database")
            st.stop()
        
        # Index selection filters - Cascading logic
        st.subheader("Filter Indices")
        
        # Initialize filtered dataframe with full dataset
        df_filter_step = df_indices.copy()
        
        col1, col2, col3, col4 = st.columns(4)
        
        # 1. Market Filter
        with col1:
            markets = ['All'] + sorted(df_filter_step['market'].dropna().unique().tolist())
            sel_market = st.selectbox("Market", markets, key="detail_market")
            
        # Apply Market filter immediately if selected
        if sel_market != 'All':
            df_filter_step = df_filter_step[df_filter_step['market'] == sel_market]
            
        # 2. Publisher Filter (Options depend on Market)
        with col2:
            publishers = ['All'] + sorted(df_filter_step['publisher'].dropna().unique().tolist())
            # Reset selection if previously selected option is no longer valid (handled by Streamlit usually, but good to be safe)
            sel_publisher = st.selectbox("Publisher", publishers, key="detail_publisher")
            
        # Apply Publisher filter
        if sel_publisher != 'All':
            df_filter_step = df_filter_step[df_filter_step['publisher'] == sel_publisher]
            
        # 3. Index Type Filter (Options depend on Market + Publisher)
        with col3:
            types = ['All'] + sorted(df_filter_step['index_type'].dropna().unique().tolist())
            sel_type = st.selectbox("Index Type", types, key="detail_type")
            
        # Apply Type filter
        if sel_type != 'All':
            df_filter_step = df_filter_step[df_filter_step['index_type'] == sel_type]
            
        # 4. Category Filter (Options depend on previous 3)
        with col4:
            categories = ['All'] + sorted(df_filter_step['category'].dropna().unique().tolist())
            sel_category = st.selectbox("Category", categories, key="detail_category")
            
        # Apply Category filter
        if sel_category != 'All':
            df_filter_step = df_filter_step[df_filter_step['category'] == sel_category]
            
        # Final filtered dataframe
        df_filtered = df_filter_step
            
        # Then maximize intersection with indices that actually have weight data
        filtered_indices_with_weight = [x for x in indices_with_weight if x in df_filtered['ts_code'].values]
        
        if not filtered_indices_with_weight:
            st.warning("No indices found matching filters that have weight data.")
            st.stop()

        # Index selection dropdown
        selected_index = st.selectbox(
            "Select Index",
            filtered_indices_with_weight,
            format_func=lambda x: f"{x} - {df_filtered[df_filtered['ts_code'] == x]['name'].values[0]}"
        )
        
        if selected_index:
            # Show index basic info
            idx_info = df_indices[df_indices['ts_code'] == selected_index]
            if not idx_info.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Index Code", selected_index)
                with col2:
                    st.metric("Name", idx_info['name'].values[0])
                with col3:
                    st.metric("Market", idx_info['market'].values[0])
                with col4:
                    st.metric("Base Point", idx_info['base_point'].values[0])
            
            st.divider()
            
            tab1, tab2 = st.tabs(["📈 Constituent Count Trend", "📋 Constituent Details"])
            
            with tab1:
                st.subheader("Constituent Count Over Time")
                st.caption("Use this chart to identify missing data (sudden drops in count)")
                
                df_counts = get_constituent_count_per_date(selected_index)
                if not df_counts.empty:
                    fig = plot_constituent_count_over_time(df_counts)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Trade Days Covered", len(df_counts))
                    with col2:
                        st.metric("Avg Constituents", f"{df_counts['constituent_count'].mean():.0f}")
                    with col3:
                        st.metric("Min/Max", f"{df_counts['constituent_count'].min()} / {df_counts['constituent_count'].max()}")
            
            with tab2:
                trade_dates = get_available_trade_dates(selected_index)
                if trade_dates:
                    selected_date = st.selectbox("Select Trade Date", trade_dates)
                    
                    if selected_date:
                        df_cons = get_constituents_for_date(selected_index, selected_date)
                        if not df_cons.empty:
                            st.markdown(f"**{len(df_cons)} constituents on {selected_date}**")
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.dataframe(
                                    df_cons,
                                    use_container_width=True,
                                    height=400,
                                    column_config={
                                        "con_code": "Constituent Code",
                                        "weight": st.column_config.NumberColumn("Weight (%)", format="%.4f")
                                    }
                                )
                            with col2:
                                st.markdown("**Weight Distribution (Top 10)**")
                                top10 = df_cons.head(10)
                                st.bar_chart(top10.set_index('con_code')['weight'])
                else:
                    st.info("No trade date data available for this index")

# --- MARKET DATA ---
elif category_config["key"] == "stock":
    # Import stock data modules
    from stock_data_loader import get_listing_delisting_stats, load_stock_basic_sample
    from stock_charts import plot_listing_delisting_trend, plot_listing_summary
    
    # --- Listing Statistics Sub-category ---
    if subcategory_key == "listing_stats":
        render_header("Listing Statistics", "listing")
        
        with st.spinner('Calculating statistics...'):
            df_stats = get_listing_delisting_stats()
            
        if df_stats.empty:
            st.warning("No stock basic data available to calculate statistics.")
        else:
            # Filters
            render_sidebar_header("Stats Filter", "filter")
            df_stats['year'] = df_stats['month'].dt.year
            years = sorted(df_stats['year'].unique().tolist(), reverse=True)
            sel_year = st.sidebar.multiselect("Select Year(s)", years, default=years[:10])
            
            df_f = df_stats[df_stats['year'].isin(sel_year)]
            
            # Key Metrics
            total_listings = df_f['listings'].sum()
            total_delistings = df_f['delistings'].sum()
            net_growth = total_listings - total_delistings
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Listings", int(total_listings))
            with col2:
                st.metric("Total Delistings", int(total_delistings))
            with col3:
                st.metric("Net Growth", int(net_growth))
                
            st.divider()
            
            tab1, tab2, tab3 = st.tabs(["📊 Trends", "📈 Growth", "📋 Monthly Data"])
            
            with tab1:
                fig_trend = plot_listing_delisting_trend(df_f)
                if fig_trend:
                    st.plotly_chart(fig_trend, use_container_width=True)
                    
            with tab2:
                fig_growth = plot_listing_summary(df_f)
                if fig_growth:
                    st.plotly_chart(fig_growth, use_container_width=True)
                    
            with tab3:
                st.markdown("**Monthly Statistics (Sorted by Date)**")
                st.dataframe(
                    df_f.sort_values('month', ascending=False),
                    use_container_width=True,
                    column_config={
                        "month": st.column_config.DatetimeColumn("Month", format="YYYY-MM"),
                        "listings": "New Listings",
                        "delistings": "Delistings",
                        "net_growth": "Net Growth",
                        "year": None # Hide year helper column
                    }
                )

# Sidebar footer
st.sidebar.divider()
st.sidebar.markdown(f"""
<div style="display: flex; align-items: center; gap: 8px; color: #8C8580; font-size: 0.75rem;">
    {ICONS["home"].replace('width="18"', 'width="14"').replace('height="18"', 'height="14"')}
    <span>Tushare Data Dashboard v1.1</span>
</div>
<div style="margin-left: 22px; color: #8C8580; font-size: 0.75rem;">Data Source: Tushare Pro</div>
""", unsafe_allow_html=True)
