"""
Home Page
=========
Landing page for the dashboard.
"""
import streamlit as st
import textwrap
from dashboard.components.styles import ICONS

def render_home_page():
    """
    Render the home page content.
    """
    # Decorative banner with Anthropic-inspired gradient
    st.markdown(textwrap.dedent("""
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
    """), unsafe_allow_html=True)
    
    st.markdown("#### Features")
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    # Get Icons for cards
    macro_icon = ICONS['macro'].replace('width="18"', 'width="32"').replace('height="18"', 'height="32"')
    index_icon = ICONS['index'].replace('width="18"', 'width="32"').replace('height="18"', 'height="32"')
    stock_icon = ICONS['stock'].replace('width="18"', 'width="32"').replace('height="18"', 'height="32"')
    
    with col1:
        st.markdown(textwrap.dedent(f"""
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
        """), unsafe_allow_html=True)
    
    with col2:
        st.markdown(textwrap.dedent(f"""
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
        """), unsafe_allow_html=True)
        
    with col3:
        st.markdown(textwrap.dedent(f"""
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
        """), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Use the sidebar to navigate between data categories")
