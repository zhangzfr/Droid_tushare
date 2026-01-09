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
    page_title="Tushare Data Dashboard",
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
    
    /* Cards / Containers - remove tab panel border */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1.5rem;
        background: white;
        border-radius: 0.75rem;
        border: none;
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
    
    /* Remove borders from Plotly chart containers */
    [data-testid="stPlotlyChart"] {
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Remove borders from all chart containers */
    .stPlotlyChart, .element-container {
        border: none !important;
    }
    
    /* Remove default iframe borders inside Plotly */
    .stPlotlyChart iframe {
        border: none !important;
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
    "heatmap": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="7" width="3" height="3"/><rect x="11" y="7" width="3" height="3"/><rect x="15" y="7" width="3" height="3"/><rect x="7" y="11" width="3" height="3"/><rect x="11" y="11" width="3" height="3"/><rect x="15" y="11" width="3" height="3"/><rect x="7" y="15" width="3" height="3"/><rect x="11" y="15" width="3" height="3"/><rect x="15" y="15" width="3" height="3"/></svg>''',
    "treemap": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/><path d="M15 9v12"/></svg>''',
    "chart": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/></svg>''',
    "vix": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>''',
    "volatility": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h2l3-9 6 18 3-9h2"/></svg>''',
    "fx": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><line x1="3" x2="6" y1="3" y2="6"/><line x1="21" x2="18" y1="3" y2="6"/><line x1="3" x2="6" y1="21" y2="18"/><line x1="21" x2="18" y1="21" y2="18"/></svg>''',
    "asset": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>''',
    "correlation": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>''',
    "analysis": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>''',
    "stock_edu": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>''',
    "market": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>''',
    "valuation": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>''',
    "industry": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/></svg>'''
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
            "SW Industries": {"key": "sw_index", "icon": "treemap"},
            "Market Width": {"key": "market_width", "icon": "chart"},
            "Constituents": {"key": "index_details", "icon": "detail"}
        }
    },
    "Market Data": {
        "key": "stock",
        "icon": "stock",
        "subcategories": {
            "Listing Statistics": {"key": "listing_stats", "icon": "listing"}
        }
    },
    "VIX Calculator": {
        "key": "vix",
        "icon": "vix",
        "subcategories": {
            "Calculate VIX": {"key": "vix_calc", "icon": "volatility"}
        }
    },
    "FX Education": {
        "key": "fx_edu",
        "icon": "fx",
        "subcategories": {
            "Asset Overview": {"key": "fx_assets", "icon": "asset"},
            "Price Dynamics": {"key": "fx_price", "icon": "chart"},
            "Correlations": {"key": "fx_corr", "icon": "correlation"},
            "Advanced Analysis": {"key": "fx_advanced", "icon": "analysis"}
        }
    },
    "A股教育": {
        "key": "stock_edu",
        "icon": "stock_edu",
        "subcategories": {
            "认识A股": {"key": "stock_overview", "icon": "market"},
            "理解价格": {"key": "stock_price", "icon": "chart"},
            "分析估值": {"key": "stock_valuation", "icon": "valuation"},
            "行业选股": {"key": "stock_industry", "icon": "industry"}
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
        <h2 style="margin: 0; font-size: 1.75rem; font-weight: 600; color: #4A4A4A;">{title}</h2>
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
    
    # Calculate date range
    all_dates = pd.concat([df_pmi['month'], df_sf['month'], df_m['month']]).dropna()
    if not all_dates.empty:
        min_date = all_dates.min().date()
        max_date = all_dates.max().date()
    else:
        from datetime import date
        min_date, max_date = date(2010, 1, 1), date.today()
    
    # Filter helper
    def filter_df(df, start, end):
        if df.empty: return df
        mask = (df['month'].dt.date >= start) & (df['month'].dt.date <= end)
        return df.loc[mask]
    
    # --- PMI Sub-category ---
    if subcategory_key == "pmi":
        render_header("PMI Manufacturing Index", "pmi")
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="pmi_start")
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="pmi_end")
        
        df_pmi_f = filter_df(df_pmi, start_date, end_date)
        
        with right_col:
            if df_pmi_f.empty:
                st.warning("No PMI data available")
            else:
                tab1, tab2, tab3 = st.tabs(["Trend", "Heatmap Analysis", "Raw Data"])
                
                with tab1:
                    fig_trend = plot_pmi_trend(df_pmi_f)
                    if fig_trend:
                        st.plotly_chart(fig_trend, use_container_width=True, key="pmi_trend")
                
                with tab2:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.subheader("Sub-indicators Heatmap")
                        fig_heatmap = plot_heatmap(df_pmi_f)
                        if fig_heatmap:
                            st.plotly_chart(fig_heatmap, use_container_width=True, key="pmi_heatmap")
                    
                    with col2:
                        st.subheader("Latest Month Breakdown")
                        if not df_pmi_f.empty:
                            latest = df_pmi_f['month'].max()
                            st.markdown(f"**Report Period:** {latest.strftime('%Y-%m')}")
                            df_latest = df_pmi_f[df_pmi_f['month'] == latest]
                            fig_bar = plot_sub_indicators_bar(df_latest)
                            if fig_bar:
                                st.plotly_chart(fig_bar, use_container_width=True, key="pmi_bar")
                
                with tab3:
                    st.dataframe(df_pmi_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Money Supply Sub-category ---
    elif subcategory_key == "money_supply":
        render_header("Money Supply (M0/M1/M2)", "money")
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="m_start")
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="m_end")
        
        df_m_f = filter_df(df_m, start_date, end_date)
        
        with right_col:
            if df_m_f.empty:
                st.warning("No money supply data available")
            else:
                tab1, tab2, tab3 = st.tabs(["Levels", "Growth Rates", "Raw Data"])
                
                with tab1:
                    fig_levels = plot_m_levels(df_m_f)
                    if fig_levels:
                        st.plotly_chart(fig_levels, use_container_width=True, key="m_levels")
                
                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Year-over-Year (YoY)")
                        fig_yoy = plot_m_yoy(df_m_f)
                        if fig_yoy:
                            st.plotly_chart(fig_yoy, use_container_width=True, key="m_yoy")
                    with col2:
                        st.subheader("Month-over-Month (MoM)")
                        fig_mom = plot_m_mom(df_m_f)
                        if fig_mom:
                            st.plotly_chart(fig_mom, use_container_width=True, key="m_mom")
                
                with tab3:
                    st.dataframe(df_m_f.sort_values('month', ascending=False), use_container_width=True)
    
    # --- Social Financing Sub-category ---
    elif subcategory_key == "social_financing":
        render_header("Social Financing", "social")
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", min_date, min_value=min_date, max_value=max_date, key="sf_start")
            end_date = st.date_input("End Date", max_date, min_value=min_date, max_value=max_date, key="sf_end")
        
        df_sf_f = filter_df(df_sf, start_date, end_date)
        
        with right_col:
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
                            st.plotly_chart(fig_inc, use_container_width=True, key="sf_inc")
                            st.subheader("Cumulative Value")
                            st.plotly_chart(fig_cum, use_container_width=True, key="sf_cum")
                        with col2:
                            st.subheader("Stock End Value")
                            st.plotly_chart(fig_stk, use_container_width=True, key="sf_stk")
                
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
    from index_charts import plot_constituent_count_over_time, plot_index_heatmap, plot_cumulative_returns
    
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
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Filters**")
            markets = ['All'] + sorted(df_indices['market'].dropna().unique().tolist())
            publishers = ['All'] + sorted(df_indices['publisher'].dropna().unique().tolist())
            
            sel_market = st.selectbox("Market", markets, key="idx_market")
            sel_publisher = st.selectbox("Publisher", publishers, key="idx_publisher")
        
        df_filtered = df_indices.copy()
        if sel_market != 'All':
            df_filtered = df_filtered[df_filtered['market'] == sel_market]
        if sel_publisher != 'All':
            df_filtered = df_filtered[df_filtered['publisher'] == sel_publisher]
        
        df_filtered['has_weight'] = df_filtered['ts_code'].isin(indices_with_weight)
        
        with right_col:
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
        
        from datetime import datetime, timedelta
        default_end = datetime.now()
        default_start = default_end - timedelta(days=60)
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", default_start, key="idx_start")
            end_date = st.date_input("End Date", default_end, key="idx_end")
            
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        with st.spinner('Fetching performance data...'):
            df_heatmap = load_major_indices_daily(start_str, end_str)
        
        with right_col:
            if df_heatmap.empty:
                st.warning(f"No performance data found between {start_str} and {end_str}")
            else:
                tab1, tab2, tab3 = st.tabs(["Heatmap Analysis", "Cumulative Returns", "Raw Data"])
                
                with tab1:
                    fig_heatmap = plot_index_heatmap(df_heatmap)
                    if fig_heatmap:
                        st.plotly_chart(fig_heatmap, use_container_width=True, key="idx_heatmap")
                
                with tab2:
                    all_indices = sorted(df_heatmap['ts_code'].unique().tolist())
                    default_selection = [x for x in ['000001.SH', '000300.SH', '000905.SH', '399006.SZ', '000688.SH'] if x in all_indices]
                    if not default_selection:
                        default_selection = all_indices[:5]
                    
                    selected_codes = st.multiselect("Select Indices to Compare:", all_indices, default=default_selection, key="idx_compare")
                    
                    if selected_codes:
                        df_line = df_heatmap[df_heatmap['ts_code'].isin(selected_codes)]
                        fig_line = plot_cumulative_returns(df_line)
                        if fig_line:
                            st.plotly_chart(fig_line, use_container_width=True, key="idx_returns")
                        
                        st.caption("Note: Cumulative returns are calculated from the first available date in the selected range, indexed to 100.")
                    else:
                        st.info("Please select at least one index to compare performance.")
                
                with tab3:
                    pivot_display = df_heatmap.pivot(index='trade_date', columns='ts_code', values='pct_chg').sort_index(ascending=False)
                    st.dataframe(pivot_display, use_container_width=True)

    # --- Shenwan Index Heatmap Sub-category ---
    elif subcategory_key == "sw_index":
        render_header("Shenwan Industry Heatmap", "treemap")
        
        from sw_index_data_loader import (
            get_sw_hierarchy, load_sw_daily_data, load_stocks_by_l3,
            load_top_stocks, load_stocks_by_l2, get_sw_members, load_stock_daily_data,
            load_stocks_by_l1
        )
        from sw_index_charts import plot_sw_treemap, plot_sw_stock_treemap, plot_l2_stock_treemap, plot_l1_stock_treemap
        from datetime import datetime, timedelta
        
        # Load Hierarchy
        df_hier = get_sw_hierarchy()
        if df_hier.empty:
            st.error("Failed to load Shenwan hierarchy data.")
            st.stop()
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Trading Date**")
            today = datetime.now()
            if today.weekday() >= 5:
                today = today - timedelta(days=today.weekday() - 4)
            selected_date = st.date_input("Select Date", today, key="sw_trade_date")
            date_str = selected_date.strftime('%Y%m%d')
            
            st.markdown("---")
            st.markdown("**View Mode**")
            view_mode = st.radio(
                "Select View",
                ["L1 Drill-down", "Full View", "Top 100 Hot Stocks"],
                index=0,
                key="sw_view_mode"
            )
        
        with right_col:
            # ==================== L1 Drill-down ====================
            if view_mode == "L1 Drill-down":
                st.caption("Default shows L1→L2→L3 indices. Select industry to drill down to stocks.")
                
                l1_options = df_hier[['l1_code', 'l1_name']].drop_duplicates().sort_values('l1_code')
                l1_dict = dict(zip(l1_options['l1_code'], l1_options['l1_name']))
                l1_choices = ['All (L1→L2→L3 Index View)'] + l1_options['l1_code'].tolist()
                
                selected_l1_drill = st.selectbox(
                    "Select L1 Industry to view stocks",
                    l1_choices,
                    format_func=lambda x: x if x.startswith('All') else f"{x} - {l1_dict.get(x, x)}",
                    key="l1_drill"
                )
                
                if selected_l1_drill.startswith('All'):
                    with st.spinner("Loading L3 index data..."):
                        target_codes = df_hier['l3_code'].unique().tolist()
                        df_sw_daily = load_sw_daily_data(date_str, target_codes)
                    
                    if df_sw_daily.empty:
                        st.warning(f"No trading data for {date_str}.")
                    else:
                        up_count = len(df_sw_daily[df_sw_daily['pct_change'] > 0])
                        down_count = len(df_sw_daily[df_sw_daily['pct_change'] < 0])
                        
                        c1, c2 = st.columns(2)
                        c1.metric("Rising Indices", up_count)
                        c2.metric("Falling Indices", down_count)
                        
                        fig = plot_sw_treemap(df_hier, df_sw_daily, level='L3')
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key="l1_tab_index_chart")
                else:
                    l1_name = l1_dict.get(selected_l1_drill, selected_l1_drill)
                    
                    with st.spinner(f"Loading stocks for {l1_name}..."):
                        df_l1_stocks = load_stocks_by_l1(date_str, selected_l1_drill)
                    
                    if df_l1_stocks.empty:
                        st.warning(f"No stock data for {l1_name} on {date_str}.")
                    else:
                        up_count = len(df_l1_stocks[df_l1_stocks['pct_change'] > 0])
                        down_count = len(df_l1_stocks[df_l1_stocks['pct_change'] < 0])
                        total_amt = df_l1_stocks['amount'].sum()
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Rising", up_count)
                        c2.metric("Falling", down_count)
                        c3.metric("Amount", f"{total_amt/100000000:.2f} B")
                        c4.metric("Stocks", len(df_l1_stocks))
                        
                        fig = plot_l1_stock_treemap(df_l1_stocks, l1_name)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key="l1_tab_stock_chart")
            
            # ==================== Original View ====================
            elif view_mode == "Full View":
                st.caption("Select level to view full data (Stock level might be slow)")
                
                level = st.radio("Select Level", ["L1", "L2", "L3", "Stock"], index=0, horizontal=True, key="opt_a_level")
                
                with st.spinner(f"Loading {level} data for {date_str}..."):
                    if level == 'Stock':
                        df_hier_full = get_sw_members()
                        target_codes = df_hier_full['ts_code'].unique().tolist()
                        df_sw_daily = load_stock_daily_data(date_str, target_codes)
                    else:
                        if level == 'L1':
                            target_codes = df_hier['l1_code'].unique().tolist()
                        elif level == 'L2':
                            target_codes = df_hier['l2_code'].unique().tolist()
                        elif level == 'L3':
                            target_codes = df_hier['l3_code'].unique().tolist()
                        df_sw_daily = load_sw_daily_data(date_str, target_codes)
                
                if df_sw_daily.empty:
                    st.warning(f"No trading data for {date_str}.")
                else:
                    up_count = len(df_sw_daily[df_sw_daily['pct_change'] > 0])
                    down_count = len(df_sw_daily[df_sw_daily['pct_change'] < 0])
                    total_amt = df_sw_daily['amount'].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"Rising {level}", up_count)
                    c2.metric(f"Falling {level}", down_count)
                    c3.metric("Amount", f"{total_amt/100000000:.2f} B")
                    
                    if level == 'Stock':
                        df_hier_full = get_sw_members()
                        fig = plot_sw_treemap(df_hier_full, df_sw_daily, level='Stock')
                    else:
                        fig = plot_sw_treemap(df_hier, df_sw_daily, level=level)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key="opt_a_chart")
            
            # ==================== Top N Stocks ====================
            elif view_mode == "Top 100 Hot Stocks":
                st.caption("Show top stocks by amount (fast loading)")
                
                top_n = st.slider("Display Count", 50, 300, 100, step=50, key="top_n_slider")
                
                with st.spinner(f"Loading Top {top_n} stocks..."):
                    df_top = load_top_stocks(date_str, top_n)
                
                if df_top.empty:
                    st.warning(f"No stock data for {date_str}.")
                else:
                    up_count = len(df_top[df_top['pct_change'] > 0])
                    down_count = len(df_top[df_top['pct_change'] < 0])
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Rising", up_count)
                    c2.metric("Falling", down_count)
                    c3.metric("Display Count", len(df_top))
                    
                    fig_top = plot_sw_stock_treemap(df_top, f"Top {top_n} Stocks by Amount")
                    if fig_top:
                        st.plotly_chart(fig_top, use_container_width=True, key="top_n_chart")
    

    # --- Market Width Sub-category ---
    elif subcategory_key == "market_width":
        render_header("SW Industry Market Width", "chart")
        
        from sw_index_data_loader import calculate_market_width
        from sw_market_width_chart import plot_market_width_heatmap
        from datetime import datetime, timedelta
        
        # Left-right layout
        left_col, right_col = st.columns([1, 7])
        
        with left_col:
            st.markdown("**Parameters**")
            level = st.selectbox("Industry Level", ["L1", "L2", "L3"], index=0, key="mw_level")
            ma_period = st.selectbox("MA Period", [5, 10, 20, 50, 90, 120], index=2, key="mw_ma")
            days = st.slider("Display Days", 10, 60, 30, step=5, key="mw_days")
            
            today = datetime.now()
            if today.weekday() >= 5:
                today = today - timedelta(days=today.weekday() - 4)
            end_date = st.date_input("End Date", today, key="mw_end_date")
            end_date_str = end_date.strftime('%Y%m%d')
        
        with st.spinner(f"Calculating MA{ma_period} market width for {level}..."):
            df_width = calculate_market_width(end_date_str, days, ma_period, level)
        
        with right_col:
            st.caption("Market Width = % of stocks with Close > MA. Heatmap shows changes across industries.")
            
            if df_width.empty:
                st.warning("No market width data available.")
            else:
                latest_date = df_width['trade_date'].max()
                df_latest = df_width[df_width['trade_date'] == latest_date]
                avg_width = df_latest['width_ratio'].mean()
                max_width_row = df_latest.loc[df_latest['width_ratio'].idxmax()]
                min_width_row = df_latest.loc[df_latest['width_ratio'].idxmin()]
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Avg Market Width", f"{avg_width:.1f}%")
                c2.metric("Strongest Industry", f"{max_width_row['index_name']} ({max_width_row['width_ratio']:.1f}%)")
                c3.metric("Weakest Industry", f"{min_width_row['index_name']} ({min_width_row['width_ratio']:.1f}%)")
                
                fig = plot_market_width_heatmap(df_width, level, ma_period)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key="market_width_heatmap")
    

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
            
            tab1, tab2 = st.tabs(["Constituent Count Trend", "Constituent Details"])
            
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
            df_stats['year'] = df_stats['month'].dt.year
            years = sorted(df_stats['year'].unique().tolist(), reverse=True)
            
            # Left-right layout
            left_col, right_col = st.columns([1, 5])
            
            with left_col:
                st.markdown("**Year Filter**")
                sel_year = st.multiselect("Select Year(s)", years, default=years[:10], key="listing_years")
            
            df_f = df_stats[df_stats['year'].isin(sel_year)]
            
            with right_col:
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
                
                tab1, tab2, tab3 = st.tabs(["Trends", "Growth", "Monthly Data"])
                
                with tab1:
                    fig_trend = plot_listing_delisting_trend(df_f)
                    if fig_trend:
                        st.plotly_chart(fig_trend, use_container_width=True, key="listing_trend")
                        
                with tab2:
                    fig_growth = plot_listing_summary(df_f)
                    if fig_growth:
                        st.plotly_chart(fig_growth, use_container_width=True, key="listing_growth")
                        
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
                            "year": None
                    }
                )

# --- VIX CALCULATOR ---
elif category_config["key"] == "vix":
    import pandas as pd
    from vix_data_loader import get_available_underlyings, calculate_vix_series, get_default_date_range
    from vix_charts import (
        plot_vix_trend, plot_vix_components, plot_vix_distribution,
        plot_forward_prices, plot_weight_trend
    )
    from datetime import datetime, timedelta
    
    if subcategory_key == "vix_calc":
        render_header("VIX Calculator", "vix")
        
        # Get available underlyings
        underlyings = get_available_underlyings()
        underlying_codes = list(underlyings.keys())
        
        # Default date range
        default_start, default_end = get_default_date_range()
        
        # Left-right layout
        left_col, right_col = st.columns([1, 6])
        
        with left_col:
            st.markdown("**Underlying Asset**")
            selected_underlying = st.selectbox(
                "Select ETF/Index",
                underlying_codes,
                format_func=lambda x: underlyings.get(x, x),
                key="vix_underlying"
            )
            
            st.markdown("---")
            st.markdown("**Date Range**")
            start_date = st.date_input("Start Date", default_start, key="vix_start")
            end_date = st.date_input("End Date", default_end, key="vix_end")
            
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                calculate_btn = st.button("Calculate", type="primary", use_container_width=True)
            with col_btn2:
                if st.button("Clear Cache", use_container_width=True):
                    st.cache_data.clear()
                    st.session_state['vix_calculated'] = False
                    st.rerun()
        
        # Convert dates to strings
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        
        # Create a unique key for current parameters to detect changes
        current_params = f"{selected_underlying}_{start_str}_{end_str}"
        
        with right_col:
            # Calculate when button is clicked
            if calculate_btn:
                # Store current params and mark as calculated
                st.session_state['vix_params'] = current_params
                st.session_state['vix_calculated'] = True
            
            # Show results if calculated with current params
            if st.session_state.get('vix_calculated', False) and st.session_state.get('vix_params') == current_params:
                with st.spinner(f"Calculating VIX for {selected_underlying}..."):
                    df_summary, df_near, df_next = calculate_vix_series(start_str, end_str, selected_underlying)
                
                if df_summary.empty:
                    st.warning("No VIX data could be calculated. Please check if option data and Shibor data are available for the selected period.")
                else:
                    # Show data coverage info
                    actual_start = df_summary['date'].min().strftime('%Y-%m-%d')
                    actual_end = df_summary['date'].max().strftime('%Y-%m-%d')
                    if actual_end != end_date.strftime('%Y-%m-%d'):
                        st.caption(f"ℹ️ Data available: {actual_start} to {actual_end} ({len(df_summary)} trading days). VIX requires both option and Shibor data.")
                    
                    # Key Metrics
                    latest_vix = df_summary['vix'].iloc[-1]
                    avg_vix = df_summary['vix'].mean()
                    max_vix = df_summary['vix'].max()
                    min_vix = df_summary['vix'].min()
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Latest VIX", f"{latest_vix:.2f}")
                    col2.metric("Average", f"{avg_vix:.2f}")
                    col3.metric("Maximum", f"{max_vix:.2f}")
                    col4.metric("Minimum", f"{min_vix:.2f}")
                    
                    st.divider()
                    
                    # Tabs for different views
                    tab1, tab2, tab3, tab4 = st.tabs(["VIX Trend", "Components", "Analysis", "Raw Data"])
                    
                    with tab1:
                        fig_trend = plot_vix_trend(df_summary, selected_underlying)
                        if fig_trend:
                            st.plotly_chart(fig_trend, use_container_width=True, key="vix_trend")
                        
                        # Distribution
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_dist = plot_vix_distribution(df_summary)
                            if fig_dist:
                                st.plotly_chart(fig_dist, use_container_width=True, key="vix_dist")
                        with col2:
                            fig_weight = plot_weight_trend(df_summary)
                            if fig_weight:
                                st.plotly_chart(fig_weight, use_container_width=True, key="vix_weight")
                    
                    with tab2:
                        fig_comp = plot_vix_components(df_summary)
                        if fig_comp:
                            st.plotly_chart(fig_comp, use_container_width=True, key="vix_comp")
                        
                        fig_fwd = plot_forward_prices(df_summary)
                        if fig_fwd:
                            st.plotly_chart(fig_fwd, use_container_width=True, key="vix_fwd")
                    
                    with tab3:
                        st.subheader("VIX Statistics")
                        
                        stats_data = {
                            "Metric": ["Count", "Mean", "Std Dev", "Min", "25%", "50%", "75%", "Max"],
                            "Value": [
                                str(len(df_summary)),
                                f"{df_summary['vix'].mean():.4f}",
                                f"{df_summary['vix'].std():.4f}",
                                f"{df_summary['vix'].min():.4f}",
                                f"{df_summary['vix'].quantile(0.25):.4f}",
                                f"{df_summary['vix'].quantile(0.50):.4f}",
                                f"{df_summary['vix'].quantile(0.75):.4f}",
                                f"{df_summary['vix'].max():.4f}"
                            ]
                        }
                        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
                        
                        st.subheader("Calculation Details")
                        st.caption("The VIX is calculated using near-term and next-term options with interpolation to 30-day implied volatility.")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Near Term σ² Statistics**")
                            st.metric("Avg σ² Near", f"{df_summary['sigma_sq_near'].mean():.6f}")
                        with col2:
                            st.markdown("**Next Term σ² Statistics**")
                            st.metric("Avg σ² Next", f"{df_summary['sigma_sq_next'].mean():.6f}")
                    
                    with tab4:
                        st.subheader("VIX Summary Data")
                        display_cols = ['date_str', 'vix', 'near_term', 'next_term', 'r_near', 'r_next', 
                                       'sigma_sq_near', 'sigma_sq_next', 'F_near', 'F_next', 'weight']
                        st.dataframe(
                            df_summary[display_cols].sort_values('date_str', ascending=False),
                            use_container_width=True,
                            column_config={
                                "date_str": "Date",
                                "vix": st.column_config.NumberColumn("VIX", format="%.4f"),
                                "near_term": st.column_config.NumberColumn("Near Term", format="%.4f"),
                                "next_term": st.column_config.NumberColumn("Next Term", format="%.4f"),
                                "r_near": st.column_config.NumberColumn("R Near", format="%.4f"),
                                "r_next": st.column_config.NumberColumn("R Next", format="%.4f"),
                                "sigma_sq_near": st.column_config.NumberColumn("σ² Near", format="%.6f"),
                                "sigma_sq_next": st.column_config.NumberColumn("σ² Next", format="%.6f"),
                                "F_near": st.column_config.NumberColumn("F Near", format="%.4f"),
                                "F_next": st.column_config.NumberColumn("F Next", format="%.4f"),
                                "weight": st.column_config.NumberColumn("Weight", format="%.4f")
                            }
                        )
            else:
                # Show instructions when no calculation or parameters changed
                if st.session_state.get('vix_calculated', False) and st.session_state.get('vix_params') != current_params:
                    st.info("Parameters changed. Click 'Calculate VIX' to recalculate with new settings.")
                else:
                    st.info("Select an underlying asset and date range, then click 'Calculate VIX' to compute the volatility index.")
                
                st.markdown("""
                ### About VIX Calculation
                
                The VIX (Volatility Index) measures the market's expectation of 30-day forward-looking volatility.
                It is calculated using option prices on the selected underlying asset.
                
                **Key Parameters:**
                - **Near Term**: Options expiring in less than 30 days
                - **Next Term**: Options expiring after 30 days
                - **Interpolation**: Weighted average to target 30-day volatility
                
                **Supported Underlyings:**
                - ETF Options: 300ETF, 50ETF, 500ETF, etc.
                - Index Options: CSI 300, SSE 50, CSI 1000
                """)

# --- FX EDUCATION DATA ---
elif category_config["key"] == "fx_edu":
    # Import FX data modules
    from fx_data_loader import (
        load_fx_obasic, load_fx_daily, get_available_fx_codes,
        calculate_returns, calculate_volatility, create_price_pivot,
        create_returns_pivot, calculate_correlation_matrix,
        calculate_rolling_correlation, aggregate_monthly, calculate_annualized_stats,
        DEFAULT_FX_ASSETS
    )
    from fx_charts import (
        plot_classify_pie, plot_asset_table_summary,
        plot_price_lines, plot_log_returns, plot_price_distribution, plot_volatility_bar,
        plot_correlation_heatmap, plot_scatter_matrix, plot_rolling_correlation,
        plot_monthly_return_heatmap, plot_volatility_line, plot_risk_return_scatter,
        plot_seasonality_bar
    )
    from datetime import datetime, timedelta
    import numpy as np
    
    # Load basic info (always needed)
    with st.spinner('Loading FX asset data...'):
        df_obasic = load_fx_obasic()
    
    if df_obasic.empty:
        st.error("Unable to load FX data. Please check database connection.")
        st.stop()
    
    # Get available codes grouped by classification
    available_codes = get_available_fx_codes()
    all_codes = df_obasic['ts_code'].tolist()
    
    # Calculate date range defaults
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    # --- Level 1: Asset Overview ---
    if subcategory_key == "fx_assets":
        render_header("Level 1: Asset Overview", "asset")
        
        # Educational intro
        st.markdown("""
        ### 📚 What Are Financial Assets?
        
        Financial markets trade different types of assets, each representing a different form of value:
        
        - **FX (Foreign Exchange)**: Currency pairs like EUR/USD represent the exchange rate between two currencies
        - **Commodities**: Physical goods like Gold (XAUUSD) and Oil (USOIL) that are traded on global markets  
        - **Indices**: Stock market benchmarks like the Dow Jones (US30) and NASDAQ (NAS100)
        
        Understanding these asset classes is the first step to learning about global financial markets!
        """)
        
        st.divider()
        
        # Layout
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Filters**")
            classifications = df_obasic['classify'].dropna().unique().tolist()
            sel_classify = st.multiselect(
                "Category",
                options=classifications,
                default=classifications,
                key="fx_classify_filter"
            )
        
        # Filter data
        df_filtered = df_obasic.copy()
        if sel_classify:
            df_filtered = df_filtered[df_filtered['classify'].isin(sel_classify)]
        
        with right_col:
            tab1, tab2 = st.tabs(["📊 Overview", "📋 Asset Details"])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_pie = plot_classify_pie(df_filtered)
                    if fig_pie:
                        st.plotly_chart(fig_pie, use_container_width=True, key="fx_pie")
                
                with col2:
                    fig_bar = plot_asset_table_summary(df_filtered)
                    if fig_bar:
                        st.plotly_chart(fig_bar, use_container_width=True, key="fx_bar")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Assets", len(df_filtered))
                col2.metric("Categories", len(df_filtered['classify'].unique()))
                col3.metric("Exchanges", len(df_filtered['exchange'].dropna().unique()))
            
            with tab2:
                st.dataframe(
                    df_filtered[['ts_code', 'name', 'classify', 'exchange', 'pip', 'pip_cost', 'trading_hours']],
                    use_container_width=True,
                    height=500,
                    column_config={
                        "ts_code": "Symbol",
                        "name": "Name",
                        "classify": "Category",
                        "exchange": "Exchange",
                        "pip": st.column_config.NumberColumn("Pip Value", format="%.5f"),
                        "pip_cost": st.column_config.NumberColumn("Pip Cost", format="%.2f"),
                        "trading_hours": "Trading Hours"
                    }
                )
        
        # Thought questions
        with st.expander("🤔 Think About It"):
            st.markdown("""
            1. Why do you think FX pairs like EURUSD have different trading characteristics than commodities like Gold?
            2. What determines the 'pip' value for different assets?
            3. How might trading hours affect price volatility?
            """)
    
    # --- Level 2: Price Dynamics ---
    elif subcategory_key == "fx_price":
        render_header("Level 2: Price Dynamics", "chart")
        
        # Educational intro
        st.markdown("""
        ### 📈 Understanding Price Movements
        
        Prices of financial assets constantly fluctuate based on supply and demand, economic news, and market sentiment.
        
        **Key Concepts:**
        - **Time Series**: A sequence of prices over time
        - **Returns**: The percentage change in price (how much you gain or lose)
        - **Log Returns**: ln(P_t / P_{t-1}) - mathematically preferred for analysis
        - **Volatility**: How much prices fluctuate - higher volatility means higher risk AND potential reward
        """)
        
        st.divider()
        
        # Sidebar filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start", default_start.date(), key="fx_price_start")
            end_date = st.date_input("End", default_end.date(), key="fx_price_end")
            
            st.markdown("**Select Assets**")
            # Filter by category first
            classifications = df_obasic['classify'].dropna().unique().tolist()
            sel_classify = st.multiselect("Category Filter", classifications, default=classifications, key="fx_price_classify")
            
            # Filter codes
            available = df_obasic[df_obasic['classify'].isin(sel_classify)]['ts_code'].tolist() if sel_classify else all_codes
            
            # Default selection
            defaults = [c for c in DEFAULT_FX_ASSETS if c in available][:4]
            sel_codes = st.multiselect("Assets", available, default=defaults, key="fx_price_assets")
        
        if not sel_codes:
            st.info("Please select at least one asset to analyze.")
        else:
            with st.spinner('Loading price data...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_fx_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("No price data available for the selected assets and date range.")
            else:
                # Calculate returns
                df_returns = calculate_returns(df_daily, 'mid_close', 'log')
                
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Trend", "📉 Returns", "📊 Volatility", "📋 Raw Data"])
                    
                    with tab1:
                        normalize = st.toggle("Normalize prices (base = 100)", value=True, key="fx_normalize")
                        fig_lines = plot_price_lines(df_daily, sel_codes, normalize=normalize)
                        if fig_lines:
                            st.plotly_chart(fig_lines, use_container_width=True, key="fx_price_lines")
                    
                    with tab2:
                        fig_returns = plot_log_returns(df_returns, sel_codes)
                        if fig_returns:
                            st.plotly_chart(fig_returns, use_container_width=True, key="fx_returns")
                        
                        st.subheader("Returns Distribution")
                        fig_dist = plot_price_distribution(df_returns.dropna(), None)
                        if fig_dist:
                            st.plotly_chart(fig_dist, use_container_width=True, key="fx_dist")
                    
                    with tab3:
                        # Calculate annualized stats
                        df_pivot = create_returns_pivot(df_returns)
                        df_stats = calculate_annualized_stats(df_pivot)
                        
                        if not df_stats.empty:
                            # Metrics
                            st.subheader("Daily Volatility Comparison")
                            fig_vol_bar = plot_volatility_bar(df_stats)
                            if fig_vol_bar:
                                st.plotly_chart(fig_vol_bar, use_container_width=True, key="fx_vol_bar")
                            
                            # Stats table
                            st.subheader("Summary Statistics")
                            st.dataframe(
                                df_stats[['ts_code', 'annualized_return', 'annualized_volatility', 'sharpe_ratio']],
                                use_container_width=True,
                                column_config={
                                    "ts_code": "Asset",
                                    "annualized_return": st.column_config.NumberColumn("Annualized Return", format="%.2%"),
                                    "annualized_volatility": st.column_config.NumberColumn("Annualized Vol", format="%.2%"),
                                    "sharpe_ratio": st.column_config.NumberColumn("Sharpe Ratio", format="%.2f")
                                }
                            )
                    
                    with tab4:
                        st.dataframe(
                            df_daily[['ts_code', 'trade_date', 'mid_open', 'mid_high', 'mid_low', 'mid_close', 'tick_qty']].sort_values(['ts_code', 'trade_date'], ascending=[True, False]),
                            use_container_width=True,
                            height=500
                        )
                
                # Thought questions
                with st.expander("🤔 Think About It"):
                    st.markdown("""
                    1. Why might crude oil (USOIL) show higher volatility than EUR/USD?
                    2. What does a Sharpe Ratio > 1 indicate about an asset's risk-adjusted performance?
                    3. Why do we normalize prices to compare assets with different price levels?
                    """)
    
    # --- Level 3: Correlations ---
    elif subcategory_key == "fx_corr":
        render_header("Level 3: Correlations", "correlation")
        
        # Educational intro
        st.markdown("""
        ### 🔗 Understanding Asset Correlations
        
        **Correlation** measures how two assets move together:
        - **+1.0**: Perfect positive correlation (move together)
        - **0.0**: No correlation (move independently)
        - **-1.0**: Perfect negative correlation (move opposite)
        
        **Why It Matters:**
        - **Portfolio Diversification**: Combining negatively correlated assets reduces overall risk
        - **Hedging**: Using one asset to offset risk in another
        - **Trading Signals**: Strong correlations can break down during market stress
        
        Example: Gold (XAUUSD) often moves opposite to the US Dollar - investors buy gold as a "safe haven" when USD weakens.
        """)
        
        st.divider()
        
        # Sidebar filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            start_date = st.date_input("Start", default_start.date(), key="fx_corr_start")
            end_date = st.date_input("End", default_end.date(), key="fx_corr_end")
            
            st.markdown("**Select Assets**")
            defaults = [c for c in DEFAULT_FX_ASSETS if c in all_codes][:6]
            sel_codes = st.multiselect("Assets (min 2)", all_codes, default=defaults, key="fx_corr_assets")
        
        if len(sel_codes) < 2:
            st.info("Please select at least 2 assets to analyze correlations.")
        else:
            with st.spinner('Loading data and calculating correlations...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_fx_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("No data available for the selected assets and date range.")
            else:
                # Calculate returns and correlations
                df_returns = calculate_returns(df_daily, 'mid_close', 'log')
                df_pivot = create_returns_pivot(df_returns)
                df_corr = calculate_correlation_matrix(df_pivot)
                
                with right_col:
                    tab1, tab2, tab3 = st.tabs(["🔥 Correlation Heatmap", "🔄 Rolling Correlation", "⚡ Scatter Matrix"])
                    
                    with tab1:
                        if not df_corr.empty:
                            fig_heatmap = plot_correlation_heatmap(df_corr)
                            if fig_heatmap:
                                st.plotly_chart(fig_heatmap, use_container_width=True, key="fx_corr_heatmap")
                            
                            # Highlight interesting pairs
                            st.subheader("Notable Correlations")
                            corr_pairs = []
                            for i in range(len(df_corr.columns)):
                                for j in range(i+1, len(df_corr.columns)):
                                    corr_val = df_corr.iloc[i, j]
                                    corr_pairs.append({
                                        'Pair': f"{df_corr.columns[i]} vs {df_corr.columns[j]}",
                                        'Correlation': corr_val,
                                        'Relationship': 'Positive' if corr_val > 0.3 else ('Negative' if corr_val < -0.3 else 'Weak')
                                    })
                            
                            import pandas as pd
                            df_pairs = pd.DataFrame(corr_pairs).sort_values('Correlation', key=abs, ascending=False).head(5)
                            st.dataframe(df_pairs, use_container_width=True, hide_index=True)
                    
                    with tab2:
                        st.markdown("**Select Two Assets for Rolling Correlation**")
                        col1, col2 = st.columns(2)
                        with col1:
                            asset1 = st.selectbox("Asset 1", sel_codes, key="fx_roll_asset1")
                        with col2:
                            asset2 = st.selectbox("Asset 2", [c for c in sel_codes if c != asset1], key="fx_roll_asset2")
                        
                        if asset1 and asset2:
                            rolling_corr = calculate_rolling_correlation(df_pivot, asset1, asset2, window=30)
                            fig_roll = plot_rolling_correlation(rolling_corr, asset1, asset2)
                            if fig_roll:
                                st.plotly_chart(fig_roll, use_container_width=True, key="fx_roll_corr")
                    
                    with tab3:
                        # Limit to 5 assets for readability
                        scatter_codes = sel_codes[:5]
                        fig_scatter = plot_scatter_matrix(df_pivot, scatter_codes)
                        if fig_scatter:
                            st.plotly_chart(fig_scatter, use_container_width=True, key="fx_scatter")
                
                # Thought questions
                with st.expander("🤔 Think About It"):
                    st.markdown("""
                    1. Why might Gold (XAUUSD) and the US Dollar Index (USDOLLAR) be negatively correlated?
                    2. If two assets have a correlation of 0.8, does buying both provide good diversification?
                    3. Why might correlations change during market stress events (like a financial crisis)?
                    4. How would you use correlation analysis to build a diversified portfolio?
                    """)
    
    # --- Level 4: Advanced Analysis ---
    elif subcategory_key == "fx_advanced":
        render_header("Level 4: Advanced Analysis", "analysis")
        
        # Educational intro
        st.markdown("""
        ### 🎓 Advanced Financial Analysis
        
        This section covers more sophisticated concepts used by professional traders and analysts:
        
        - **Seasonality**: Recurring patterns at specific times of year (e.g., energy prices in winter)
        - **Volatility Clustering**: High volatility tends to follow high volatility
        - **Risk-Return Tradeoff**: Higher expected returns usually come with higher risk
        - **Monthly/Annual Patterns**: Identifying trends over longer time horizons
        
        These tools help analysts predict future behavior and make informed investment decisions.
        """)
        
        st.divider()
        
        # Sidebar filters
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**Date Range**")
            # Use longer default for advanced analysis
            adv_start = default_end - timedelta(days=730)  # 2 years
            start_date = st.date_input("Start", adv_start.date(), key="fx_adv_start")
            end_date = st.date_input("End", default_end.date(), key="fx_adv_end")
            
            st.markdown("**Select Assets**")
            defaults = [c for c in DEFAULT_FX_ASSETS if c in all_codes][:4]
            sel_codes = st.multiselect("Assets", all_codes, default=defaults, key="fx_adv_assets")
        
        if not sel_codes:
            st.info("Please select at least one asset for advanced analysis.")
        else:
            with st.spinner('Loading data for advanced analysis...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_fx_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("No data available for the selected assets and date range.")
            else:
                # Calculate various metrics
                df_returns = calculate_returns(df_daily, 'mid_close', 'log')
                df_vol = calculate_volatility(df_returns, window=20)
                df_monthly = aggregate_monthly(df_daily)
                df_pivot = create_returns_pivot(df_returns)
                df_stats = calculate_annualized_stats(df_pivot)
                
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📅 Seasonality", "📊 Volatility Trends", "⚖️ Risk-Return", "📋 Monthly Data"])
                    
                    with tab1:
                        st.subheader("Monthly Performance Heatmap")
                        sel_asset = st.selectbox("Select Asset", sel_codes, key="fx_season_asset")
                        
                        if sel_asset:
                            fig_monthly = plot_monthly_return_heatmap(df_monthly, sel_asset)
                            if fig_monthly:
                                st.plotly_chart(fig_monthly, use_container_width=True, key="fx_monthly_heatmap")
                            
                            # Seasonality bar
                            st.subheader("Average Return by Month")
                            fig_season = plot_seasonality_bar(df_monthly, sel_asset)
                            if fig_season:
                                st.plotly_chart(fig_season, use_container_width=True, key="fx_season_bar")
                    
                    with tab2:
                        st.subheader("Rolling 20-Day Volatility")
                        fig_vol_line = plot_volatility_line(df_vol, sel_codes)
                        if fig_vol_line:
                            st.plotly_chart(fig_vol_line, use_container_width=True, key="fx_vol_line")
                        
                        st.caption("Notice how volatility tends to cluster - periods of high volatility are often followed by more high volatility.")
                    
                    with tab3:
                        st.subheader("Risk vs Return Profile")
                        if not df_stats.empty:
                            fig_rr = plot_risk_return_scatter(df_stats)
                            if fig_rr:
                                st.plotly_chart(fig_rr, use_container_width=True, key="fx_risk_return")
                            
                            st.markdown("""
                            **How to Read This Chart:**
                            - **X-axis (Volatility)**: Higher = more risky
                            - **Y-axis (Return)**: Higher = better performance
                            - **Color (Sharpe Ratio)**: Green = better risk-adjusted return
                            - **Ideal position**: Top-left (high return, low risk)
                            """)
                    
                    with tab4:
                        st.dataframe(
                            df_monthly[['ts_code', 'month', 'mid_open', 'mid_high', 'mid_low', 'mid_close', 'monthly_return']].sort_values(['ts_code', 'month'], ascending=[True, False]),
                            use_container_width=True,
                            height=500,
                            column_config={
                                "monthly_return": st.column_config.NumberColumn("Monthly Return", format="%.2%")
                            }
                        )
                
                # Thought questions
                with st.expander("🤔 Think About It"):
                    st.markdown("""
                    1. Why might energy commodities show strong seasonality patterns?
                    2. What causes volatility clustering? (Hint: think about news and market psychology)
                    3. Is the Sharpe Ratio always the best measure of investment quality? What are its limitations?
                    4. How might macroeconomic events (interest rate changes, elections) affect these patterns?
                    """)

# --- A股教育 DATA ---
elif category_config["key"] == "stock_edu":
    # 导入A股教育模块
    from stock_edu_data_loader import (
        load_stock_basic, load_stock_company, get_market_summary,
        load_stock_daily, load_adj_factor, calculate_adjusted_price,
        calculate_returns, calculate_volatility,
        load_daily_basic, get_latest_valuation,
        aggregate_by_industry, calculate_industry_returns, calculate_industry_correlation,
        calculate_annualized_stats_by_stock, create_price_pivot, normalize_prices,
        get_stock_name_map, DEFAULT_STOCKS
    )
    from stock_edu_charts import (
        plot_market_pie, plot_status_pie, plot_industry_bar, plot_area_bar,
        plot_candlestick, plot_price_lines, plot_return_distribution, plot_volatility_comparison,
        plot_pe_timeseries, plot_pb_timeseries, plot_valuation_boxplot, plot_turnover_scatter,
        plot_market_cap_distribution, plot_industry_valuation, plot_industry_correlation_heatmap,
        plot_risk_return_scatter, plot_industry_returns_heatmap
    )
    from datetime import datetime, timedelta
    
    # 加载基本信息
    with st.spinner('正在加载A股数据...'):
        df_basic = load_stock_basic()
    
    if df_basic.empty:
        st.error("无法加载股票基本信息，请检查数据库连接。")
        st.stop()
    
    # 获取名称映射
    name_map = get_stock_name_map(df_basic)
    
    # 只保留正常上市的股票供选择
    listed_stocks = df_basic[df_basic['list_status'] == 'L']['ts_code'].tolist()
    
    # 计算日期默认值
    default_end = datetime.now()
    default_start = default_end - timedelta(days=365)
    
    # --- 第1层：认识A股 ---
    if subcategory_key == "stock_overview":
        render_header("第1层：认识A股市场", "market")
        
        # 教育内容
        st.markdown("""
        ### 📚 什么是A股市场？
        
        **A股**是指在中国境内上市、以人民币计价交易的股票。主要交易场所：
        
        - **上海证券交易所 (SSE)**：主板、科创板
        - **深圳证券交易所 (SZSE)**：主板、创业板
        - **北京证券交易所 (BSE)**：北交所
        
        **板块分类**：
        - **主板**：成熟大型企业，盈利要求较高
        - **创业板**：成长型创新企业
        - **科创板**：科技创新企业，注册制
        """)
        
        st.divider()
        
        # 获取市场统计
        summary = get_market_summary(df_basic)
        
        # 指标卡
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("上市公司总数", f"{summary.get('total', 0):,}")
        col2.metric("正常上市", f"{summary.get('listed', 0):,}")
        col3.metric("已退市", f"{summary.get('delisted', 0):,}")
        col4.metric("暂停上市", f"{summary.get('suspended', 0):,}")
        
        st.divider()
        
        # 布局
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**筛选**")
            show_listed_only = st.checkbox("仅显示上市中", value=True)
        
        df_display = df_basic.copy()
        if show_listed_only:
            df_display = df_display[df_display['list_status'] == 'L']
        
        with right_col:
            tab1, tab2, tab3, tab4 = st.tabs(["📊 板块分布", "🏭 行业分布", "🗺️ 地域分布", "📋 股票列表"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    fig_market = plot_market_pie(summary.get('by_market', {}))
                    if fig_market:
                        st.plotly_chart(fig_market, use_container_width=True, key="stock_market_pie")
                with col2:
                    fig_status = plot_status_pie(df_basic)
                    if fig_status:
                        st.plotly_chart(fig_status, use_container_width=True, key="stock_status_pie")
            
            with tab2:
                fig_industry = plot_industry_bar(summary.get('by_industry', {}))
                if fig_industry:
                    st.plotly_chart(fig_industry, use_container_width=True, key="stock_industry_bar")
            
            with tab3:
                fig_area = plot_area_bar(summary.get('by_area', {}))
                if fig_area:
                    st.plotly_chart(fig_area, use_container_width=True, key="stock_area_bar")
            
            with tab4:
                st.dataframe(
                    df_display[['ts_code', 'name', 'industry', 'market', 'area', 'list_date']],
                    use_container_width=True,
                    height=500,
                    column_config={
                        "ts_code": "股票代码",
                        "name": "股票名称",
                        "industry": "所属行业",
                        "market": "板块",
                        "area": "地域",
                        "list_date": "上市日期"
                    }
                )
        
        # 思考题
        with st.expander("🤔 思考题"):
            st.markdown("""
            1. 为什么中国要设立多个不同的股票板块（主板、创业板、科创板）？
            2. 从行业分布来看，A股市场的结构有什么特点？
            3. 地域分布与经济发展水平有什么关系？
            """)
    
    # --- 第2层：理解价格 ---
    elif subcategory_key == "stock_price":
        render_header("第2层：理解股票价格", "chart")
        
        # 教育内容
        st.markdown("""
        ### 📈 股票价格的基本概念
        
        **K线图（蜡烛图）**是展示价格走势的经典方式：
        - **开盘价 (Open)**：当日第一笔交易价格
        - **收盘价 (Close)**：当日最后一笔交易价格
        - **最高价 (High)**：当日最高成交价
        - **最低价 (Low)**：当日最低成交价
        
        **收益率**衡量投资回报：
        - 简单收益率：(P_t - P_{t-1}) / P_{t-1}
        - 对数收益率：ln(P_t / P_{t-1})
        
        **波动率**反映价格变化的剧烈程度，是衡量风险的重要指标。
        """)
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            start_date = st.date_input("开始", default_start.date(), key="stock_price_start")
            end_date = st.date_input("结束", default_end.date(), key="stock_price_end")
            
            st.markdown("**选择股票**")
            # 筛选行业
            industries = df_basic[df_basic['list_status'] == 'L']['industry'].dropna().unique().tolist()
            sel_industry = st.multiselect("行业筛选", industries, key="stock_price_industry")
            
            if sel_industry:
                available = df_basic[(df_basic['list_status'] == 'L') & (df_basic['industry'].isin(sel_industry))]['ts_code'].tolist()
            else:
                available = listed_stocks
            
            # 默认选择
            defaults = [c for c in DEFAULT_STOCKS if c in available][:4]
            sel_codes = st.multiselect("股票", available, default=defaults, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_price_codes")
        
        if not sel_codes:
            st.info("请选择至少一只股票进行分析。")
        else:
            with st.spinner('正在加载行情数据...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_daily = load_stock_daily(sel_codes, start_str, end_str)
            
            if df_daily.empty:
                st.warning("所选股票在该日期范围内无行情数据。")
            else:
                # 计算收益率
                df_returns = calculate_returns(df_daily, 'close', 'simple')
                df_stats = calculate_annualized_stats_by_stock(df_daily)
                
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 K线图", "📈 价格走势", "📉 收益分布", "📋 原始数据"])
                    
                    with tab1:
                        sel_kline = st.selectbox("选择股票查看K线", sel_codes, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_kline_select")
                        fig_kline = plot_candlestick(df_daily, sel_kline, name_map)
                        if fig_kline:
                            st.plotly_chart(fig_kline, use_container_width=True, key="stock_kline")
                    
                    with tab2:
                        normalize = st.toggle("归一化价格 (首日=100)", value=True, key="stock_normalize")
                        df_pivot = create_price_pivot(df_daily, 'close')
                        fig_lines = plot_price_lines(df_pivot, normalize=normalize, name_map=name_map)
                        if fig_lines:
                            st.plotly_chart(fig_lines, use_container_width=True, key="stock_price_lines")
                    
                    with tab3:
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_dist = plot_return_distribution(df_returns, name_map=name_map)
                            if fig_dist:
                                st.plotly_chart(fig_dist, use_container_width=True, key="stock_return_dist")
                        with col2:
                            fig_vol = plot_volatility_comparison(df_stats, name_map=name_map)
                            if fig_vol:
                                st.plotly_chart(fig_vol, use_container_width=True, key="stock_vol_compare")
                    
                    with tab4:
                        st.dataframe(
                            df_daily[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'pct_chg', 'vol', 'amount']].sort_values(['ts_code', 'trade_date'], ascending=[True, False]),
                            use_container_width=True,
                            height=500,
                            column_config={
                                "ts_code": "代码",
                                "trade_date": "日期",
                                "pct_chg": st.column_config.NumberColumn("涨跌幅%", format="%.2f"),
                                "vol": st.column_config.NumberColumn("成交量", format="%.0f"),
                                "amount": st.column_config.NumberColumn("成交额", format="%.0f")
                            }
                        )
                
                # 思考题
                with st.expander("🤔 思考题"):
                    st.markdown("""
                    1. 为什么A股市场中红色代表上涨、绿色代表下跌？与西方市场有何不同？
                    2. 高波动率的股票一定是不好的投资吗？
                    3. 为什么要用归一化价格来比较不同股票的走势？
                    """)
    
    # --- 第3层：分析估值 ---
    elif subcategory_key == "stock_valuation":
        render_header("第3层：分析估值指标", "valuation")
        
        # 教育内容
        st.markdown("""
        ### 💰 核心估值指标
        
        **市盈率 (PE - Price to Earnings)**
        - 公式：股价 / 每股收益 = 总市值 / 净利润
        - 含义：投资者愿意为每1元利润支付多少钱
        - PE高可能意味着高成长预期，也可能是高估
        
        **市净率 (PB - Price to Book)**
        - 公式：股价 / 每股净资产 = 总市值 / 净资产
        - 适用于重资产行业（银行、地产）
        - PB<1 可能意味着被低估
        
        **换手率 (Turnover Rate)**
        - 公式：成交量 / 流通股本 × 100%
        - 反映股票活跃度和市场情绪
        """)
        
        st.divider()
        
        # 筛选器
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            start_date = st.date_input("开始", default_start.date(), key="stock_val_start")
            end_date = st.date_input("结束", default_end.date(), key="stock_val_end")
            
            st.markdown("**选择股票**")
            defaults = [c for c in DEFAULT_STOCKS if c in listed_stocks][:5]
            sel_codes = st.multiselect("股票", listed_stocks, default=defaults, format_func=lambda x: f"{x} {name_map.get(x, '')}", key="stock_val_codes")
        
        if not sel_codes:
            st.info("请选择至少一只股票进行估值分析。")
        else:
            with st.spinner('正在加载估值数据...'):
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                df_valuation = load_daily_basic(sel_codes, start_str, end_str)
            
            if df_valuation.empty:
                st.warning("所选股票在该日期范围内无估值数据。")
            else:
                with right_col:
                    tab1, tab2, tab3, tab4 = st.tabs(["📈 PE走势", "📊 PB走势", "📉 估值分布", "📋 数据表"])
                    
                    with tab1:
                        fig_pe = plot_pe_timeseries(df_valuation, sel_codes, name_map)
                        if fig_pe:
                            st.plotly_chart(fig_pe, use_container_width=True, key="stock_pe_line")
                        
                        st.caption("PE-TTM：滚动12个月净利润计算的市盈率，更能反映最新盈利状况。")
                    
                    with tab2:
                        fig_pb = plot_pb_timeseries(df_valuation, sel_codes, name_map)
                        if fig_pb:
                            st.plotly_chart(fig_pb, use_container_width=True, key="stock_pb_line")
                    
                    with tab3:
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_pe_box = plot_valuation_boxplot(df_valuation, 'pe_ttm', name_map)
                            if fig_pe_box:
                                st.plotly_chart(fig_pe_box, use_container_width=True, key="stock_pe_box")
                        with col2:
                            fig_pb_box = plot_valuation_boxplot(df_valuation, 'pb', name_map)
                            if fig_pb_box:
                                st.plotly_chart(fig_pb_box, use_container_width=True, key="stock_pb_box")
                    
                    with tab4:
                        st.dataframe(
                            df_valuation[['ts_code', 'trade_date', 'close', 'pe_ttm', 'pb', 'turnover_rate', 'total_mv_yi']].sort_values(['ts_code', 'trade_date'], ascending=[True, False]),
                            use_container_width=True,
                            height=500,
                            column_config={
                                "ts_code": "代码",
                                "trade_date": "日期",
                                "close": st.column_config.NumberColumn("收盘价", format="%.2f"),
                                "pe_ttm": st.column_config.NumberColumn("PE-TTM", format="%.2f"),
                                "pb": st.column_config.NumberColumn("PB", format="%.2f"),
                                "turnover_rate": st.column_config.NumberColumn("换手率%", format="%.2f"),
                                "total_mv_yi": st.column_config.NumberColumn("总市值(亿)", format="%.2f")
                            }
                        )
                
                # 思考题
                with st.expander("🤔 思考题"):
                    st.markdown("""
                    1. 茅台的PE为什么可以长期高于银行股？这合理吗？
                    2. 为什么银行股的PB经常低于1？
                    3. 高换手率是好事还是坏事？对于不同类型投资者意义不同吗？
                    """)
    
    # --- 第4层：行业选股 ---
    elif subcategory_key == "stock_industry":
        render_header("第4层：行业分析与选股", "industry")
        
        # 教育内容
        st.markdown("""
        ### 🏭 行业分析框架
        
        **为什么要分析行业？**
        - 不同行业有不同的商业周期和估值逻辑
        - 行业轮动是重要的投资策略
        - 分散投资于低相关行业可以降低组合风险
        
        **关键指标**：
        - **行业PE中位数**：反映行业整体估值水平
        - **行业收益率**：衡量行业表现
        - **行业相关性**：用于构建分散组合
        
        **风险-收益分析**：
        - 高收益伴随高风险是普遍规律
        - 夏普比率 = (收益率 - 无风险收益率) / 波动率
        """)
        
        st.divider()
        
        # 筛选
        left_col, right_col = st.columns([1, 5])
        
        with left_col:
            st.markdown("**日期范围**")
            adv_start = default_end - timedelta(days=180)  # 半年
            start_date = st.date_input("开始", adv_start.date(), key="stock_ind_start")
            end_date = st.date_input("结束", default_end.date(), key="stock_ind_end")
            
            st.markdown("**行业筛选**")
            all_industries = df_basic[df_basic['list_status'] == 'L']['industry'].dropna().unique().tolist()
            sel_industries = st.multiselect("选择行业", all_industries, default=all_industries[:10], key="stock_ind_select")
        
        if not sel_industries:
            st.info("请选择至少一个行业进行分析。")
        else:
            with st.spinner('正在加载行业数据...'):
                # 获取行业内股票
                industry_stocks = df_basic[(df_basic['list_status'] == 'L') & (df_basic['industry'].isin(sel_industries))]['ts_code'].tolist()
                
                # 限制数量
                if len(industry_stocks) > 200:
                    industry_stocks = industry_stocks[:200]
                
                start_str = start_date.strftime('%Y%m%d')
                end_str = end_date.strftime('%Y%m%d')
                
                df_daily = load_stock_daily(industry_stocks, start_str, end_str)
                df_valuation = get_latest_valuation(industry_stocks)
            
            with right_col:
                tab1, tab2, tab3, tab4 = st.tabs(["📊 行业估值", "🔥 收益分析", "🔗 相关性", "⚖️ 风险收益"])
                
                with tab1:
                    if not df_valuation.empty:
                        df_industry_val = aggregate_by_industry(df_basic, df_valuation)
                        if not df_industry_val.empty:
                            fig_ind_val = plot_industry_valuation(df_industry_val)
                            if fig_ind_val:
                                st.plotly_chart(fig_ind_val, use_container_width=True, key="stock_ind_val")
                            
                            st.subheader("行业估值一览")
                            st.dataframe(df_industry_val, use_container_width=True, hide_index=True)
                    else:
                        st.warning("无法获取估值数据。")
                
                with tab2:
                    if not df_daily.empty:
                        df_ind_daily = calculate_industry_returns(df_daily, df_basic)
                        if not df_ind_daily.empty:
                            fig_heatmap = plot_industry_returns_heatmap(df_ind_daily)
                            if fig_heatmap:
                                st.plotly_chart(fig_heatmap, use_container_width=True, key="stock_ind_ret")
                    else:
                        st.warning("无法获取行情数据。")
                
                with tab3:
                    if not df_daily.empty:
                        df_ind_daily = calculate_industry_returns(df_daily, df_basic)
                        if not df_ind_daily.empty:
                            df_corr = calculate_industry_correlation(df_ind_daily)
                            if not df_corr.empty:
                                fig_corr = plot_industry_correlation_heatmap(df_corr)
                                if fig_corr:
                                    st.plotly_chart(fig_corr, use_container_width=True, key="stock_ind_corr")
                                
                                st.caption("低相关性的行业组合可以有效分散风险。")
                
                with tab4:
                    if not df_daily.empty:
                        df_stats = calculate_annualized_stats_by_stock(df_daily)
                        if not df_stats.empty:
                            # 合并名称
                            df_stats = df_stats.merge(df_basic[['ts_code', 'name', 'industry']], on='ts_code', how='left')
                            
                            fig_rr = plot_risk_return_scatter(df_stats, name_map)
                            if fig_rr:
                                st.plotly_chart(fig_rr, use_container_width=True, key="stock_risk_return")
                            
                            st.markdown("""
                            **如何解读风险-收益图：**
                            - **X轴（波动率）**：越靠右风险越高
                            - **Y轴（收益率）**：越靠上收益越高
                            - **理想位置**：左上角（高收益低风险）
                            - **颜色（夏普比率）**：绿色代表更好的风险调整后收益
                            """)
            
            # 思考题
            with st.expander("🤔 思考题"):
                st.markdown("""
                1. 为什么有些行业的PE长期高于其他行业？这与行业特性有何关系？
                2. 如何利用行业相关性构建一个分散化的投资组合？
                3. 高夏普比率的股票一定是好的投资标的吗？有什么局限性？
                4. 宏观经济周期如何影响不同行业的轮动？
                """)

# Sidebar footer
st.sidebar.divider()
st.sidebar.markdown(f"""
<div style="display: flex; align-items: center; gap: 8px; color: #8C8580; font-size: 0.75rem;">
    {ICONS["home"].replace('width="18"', 'width="14"').replace('height="18"', 'height="14"')}
    <span>Tushare Data Dashboard v1.1</span>
</div>
<div style="margin-left: 22px; color: #8C8580; font-size: 0.75rem;">Data Source: Tushare Pro</div>
""", unsafe_allow_html=True)
