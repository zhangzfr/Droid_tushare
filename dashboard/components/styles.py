"""
Shared Styles and Icons
======================
Contains CSS styles and SVG icon definitions for the dashboard.
"""

# Custom CSS with Anthropic-style design system
CUSTOM_CSS = """
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
    }
    
    /* Remove massive top padding from sidebar */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label div {
        font-size: 0.85rem !important;
        color: #5C5653;
    }
    
    /* Checkbox labels - smaller than nav labels */
    [data-testid="stSidebar"] .stCheckbox label span,
    .stCheckbox label span {
        font-size: 0.75rem !important;
    }
    
    /* ===== FONT HIERARCHY FOR MAIN CONTENT FILTERS ===== */
    
    /* L1: Section Headers - Bold (e.g., **Filters**, **Date Range**) */
    .main [data-testid="stMarkdownContainer"] strong,
    .main [data-testid="stMarkdownContainer"] b {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    
    /* L2: Category Labels - Italic (e.g., *Market*, *Publisher*) */
    .main [data-testid="stMarkdownContainer"] em {
        font-size: 0.75rem !important;
    }
    
    /* L3: Sub-category Labels (e.g., *其他*, *亚太地区*) - smaller via <small> tag */
    .main [data-testid="stMarkdownContainer"] small,
    .main [data-testid="stMarkdownContainer"] small em,
    .main [data-testid="stMarkdownContainer"] small *,
    .main small,
    .main small * {
        font-size: 0.65rem !important;
    }
    
    /* ===== ULTRA-AGGRESSIVE CHECKBOX STYLING ===== */
    /* Target ALL possible checkbox label elements */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label span,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stCheckbox"] label div,
    div[data-testid="stCheckbox"] > label > div,
    div[data-testid="stCheckbox"] > label > div > p,
    .stCheckbox label,
    .stCheckbox label span,
    .stCheckbox label p,
    .stCheckbox label div,
    .stCheckbox > label > div,
    .stCheckbox > label > div > p {
        font-size: 0.7rem !important;
        line-height: 1.3 !important;
    }
    
    /* Checkbox icon - target SPAN element (confirmed by browser inspection) */
    div[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > span:first-child,
    div[data-testid="stCheckbox"] label > span:first-child,
    .stCheckbox label[data-baseweb="checkbox"] > span:first-child,
    .stCheckbox label > span:first-child,
    [data-baseweb="checkbox"] > span:first-child {
        width: 14px !important;
        height: 14px !important;
        min-width: 14px !important;
        min-height: 14px !important;
        max-width: 14px !important;
        max-height: 14px !important;
        transform: scale(0.8) !important;
        transform-origin: center center !important;
    }
    
    /* Checkbox container - reduce gap */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label[data-baseweb="checkbox"],
    .stCheckbox label,
    [data-baseweb="checkbox"] {
        gap: 0.3rem !important;
    }
    
    /* ===== RADIO BUTTON STYLING ===== */
    /* Radio button icon - target SPAN element similar to checkbox */
    div[data-testid="stRadio"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child,
    div[data-testid="stRadio"] [role="radiogroup"] label > div:first-child,
    .stRadio [role="radiogroup"] label[data-baseweb="radio"] > div:first-child,
    .stRadio [role="radiogroup"] label > div:first-child,
    [data-baseweb="radio"] > div:first-child {
        width: 14px !important;
        height: 14px !important;
        min-width: 14px !important;
        min-height: 14px !important;
        max-width: 14px !important;
        max-height: 14px !important;
        transform: scale(0.8) !important;
        transform-origin: center center !important;
    }
    
    /* Radio button text */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label span,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] [role="radiogroup"] label,
    div[data-testid="stRadio"] [role="radiogroup"] label span,
    .stRadio label,
    .stRadio [role="radiogroup"] label,
    .stRadio [role="radiogroup"] label span {
        font-size: 0.7rem !important;
        line-height: 1.1 !important;
    }
    
    /* Radio container - reduce gap and align */
    div[data-testid="stRadio"] [role="radiogroup"] label,
    .stRadio [role="radiogroup"] label,
    [data-baseweb="radio"] {
        gap: 0.3rem !important;
        align-items: center !important;
    }
    
    /* ===== CHECKBOX/RADIO ALIGNMENT & SPACING ===== */
    
    /* FIX: Parent container gap (stVerticalBlock has 16px gap) */
    div[data-testid="stVerticalBlock"]:has(div[data-testid="stCheckbox"]) {
        gap: 0.1rem !important;
    }
    
    /* FIX: Checkbox icon margin-top causing misalignment */
    div[data-testid="stCheckbox"] label span[data-baseweb="checkbox"],
    div[data-testid="stCheckbox"] label > span:first-child,
    [data-baseweb="checkbox"] > span:first-child {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        align-self: center !important;
    }
    
    /* Vertical alignment */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label[data-baseweb="checkbox"],
    .stCheckbox label,
    [data-baseweb="checkbox"] {
        align-items: center !important;
        gap: 0.25rem !important;
    }
    
    /* Reduced row spacing for checkboxes */
    div[data-testid="stCheckbox"],
    .stCheckbox {
        margin-bottom: -0.5rem !important;
        padding: 0 !important;
    }
    
    /* Target element-container wrapper */
    div[data-testid="stElementContainer"]:has(div[data-testid="stCheckbox"]) {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Checkbox label line height */
    div[data-testid="stCheckbox"] label,
    .stCheckbox label {
        line-height: 1.1 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Reduced row spacing for radio buttons */
    div[data-testid="stRadio"] [role="radiogroup"],
    .stRadio [role="radiogroup"] {
        gap: 0.05rem !important;
    }
    
    div[data-testid="stRadio"] [role="radiogroup"] label,
    .stRadio [role="radiogroup"] label {
        padding: 0.1rem 0 !important;
        margin: 0 !important;
    }
    
    /* Input labels (Date, Number, etc.) */
    .main .stDateInput label,
    .main .stNumberInput label,
    .main .stSlider label,
    .main .stTextInput label,
    .main .stSelectbox label,
    .main .stMultiSelect label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stNumberInput"] label {
        font-size: 0.7rem !important;
    }
    
    /* Input values */
    .main .stDateInput input,
    .main .stNumberInput input,
    .main .stTextInput input,
    .main [data-baseweb="input"] input,
    .main .stSelectbox [data-baseweb="select"],
    div[data-testid="stDateInput"] input,
    [data-baseweb="input"] input {
        font-size: 0.7rem !important;
    }
    
    /* Spacing adjustments */
    div[data-testid="stCheckbox"],
    .stCheckbox {
        margin-bottom: 0.05rem !important;
        padding: 0.05rem 0 !important;
    }
    
    div[data-testid="stRadio"] [role="radiogroup"],
    .stRadio [role="radiogroup"] {
        gap: 0.1rem !important;
    }
    
    /* Date picker calendar */
    [data-baseweb="calendar"] {
        font-size: 0.7rem !important;
    }
    
    /* Sidebar title */
    [data-testid="stSidebar"] h1 {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1A1A1A;
        padding-bottom: 0.5rem;
        border-bottom: none; /* Removed border */
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
        border: none !important; /* STRICTLY NO BORDER */
        box-shadow: none;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: #FDFBF9;
        border: none !important; /* STRICTLY NO BORDER */
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
        border: none !important; /* STRICTLY NO BORDER */
        background-color: #F5F5F5; /* Light background instead of border */
        transition: all 0.15s ease;
    }
    
    .stButton > button:hover {
        background-color: #E0E0E0;
        color: #D97757;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border-radius: 0.75rem;
        overflow: hidden;
        border: none !important; /* STRICTLY NO BORDER */
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
"""

NAV_CSS = """
<style>
    /* Hide default streamlit sidebar styling if needed to minimize clutter */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    
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

    /* ===== Sidebar Expander Styling ===== */
    /* Target the expander container in sidebar */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        margin-bottom: 0px !important;
    }

    /* Target the details element itself (the border often lives here) */
    [data-testid="stSidebar"] [data-testid="stExpander"] details {
        border-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }

    /* Target the summary (clickable header) */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        padding: 0px 12px 0px 4px !important; /* Align with nav links */
        min-height: 0px !important;
        height: auto !important;
        background-color: transparent !important;
        color: #8C8580 !important; /* Match .nav-header color */
        transition: color 0.2s ease;
        border: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: #1A1A1A !important;
        background-color: transparent !important;
    }

    /* Text inside summary (The Category Name) */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p {
        font-size: 13px !important; /* Slightly larger than tiny header */
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0 !important;
    }
    
    /* Content inside expander */
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0px 0px 8px 10px !important; /* Indent sub-items */
        border: none !important;
    }
    
    /* Remove default streamlit expander content border */
    .streamlit-expanderContent {
        border: none !important;
        box-shadow: none !important;
    }

    /* Fix strict top padding for expanders */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        margin-top: 8px !important;
    }
</style>
"""

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
    "industry": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/></svg>''',
    "insights": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>''',
    "gauge": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></svg>''',
    "globe": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>''',
    "pulse": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>''',
    'cn_ppi': '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    'gdp': '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V7l8-4 8 4v14"/><path d="M9 10a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z"/></svg>',
    "price": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>''',
    "finance": '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/><line x1="12" x2="12" y1="15" y2="15"/></svg>''',
    "bar": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>''',
    "pie": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>''',
    "stats": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/></svg>''',
    "trend": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>''',
    "calc": '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" x2="16" y1="6" y2="6"/><line x1="16" x2="16" y1="14" y2="18"/><path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/><path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/></svg>'''
}
