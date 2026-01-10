"""
Header Components
================
Reusable header rendering components.
"""
import streamlit as st
import textwrap
from dashboard.components.styles import ICONS

def render_header(title, icon_name=None):
    """
    Render a consistent header with optional SVG icon.
    """
    icon_html = ""
    if icon_name and icon_name in ICONS:
        icon_svg = ICONS[icon_name]
        # Inject style into SVG string
        icon_svg = icon_svg.replace('width="16"', 'width="28"').replace('height="16"', 'height="28"')
        icon_html = f'<span style="display: inline-block; vertical-align: middle; margin-right: 12px; color: #D97757;">{icon_svg}</span>'
        
    st.markdown(textwrap.dedent(f"""
    <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
        {icon_html}
        <h2 style="margin: 0; font-size: 1.75rem; font-weight: 600; color: #4A4A4A;">{title}</h2>
    </div>
    """), unsafe_allow_html=True)

def render_main_header(title, subtitle=None):
    """
    Render the main page header.
    """
    st.markdown(textwrap.dedent(f"""
    <h1 style="color: #1A1A1A; margin-bottom: 0.5rem;">{title}</h1>
    """), unsafe_allow_html=True)
    
    if subtitle:
        st.markdown(textwrap.dedent(f"""
        <p style="color: #5C5653; font-size: 1.1rem; margin-bottom: 2rem;">{subtitle}</p>
        """), unsafe_allow_html=True)
