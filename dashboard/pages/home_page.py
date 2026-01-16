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
    Render the home page content with a 'Refined FinTech' aesthetic.
    """
    # Inject Global CSS for "Refined FinTech" Design
    st.markdown("""
    <style>
        /* Import a nice font if possible, or fallback to a premium system stack */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

        :root {
            --primary: #D97757;
            --primary-dark: #B55D42;
            --primary-light: #FBECE8;
            --bg-canvas: #FAFAFA;
            --bg-card: #FFFFFF;
            --text-main: #1A1A1A;
            --text-muted: #666666;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.03);
            --shadow-md: 0 8px 16px rgba(0,0,0,0.04), 0 4px 8px rgba(0,0,0,0.02);
            --shadow-lg: 0 16px 32px rgba(217, 119, 87, 0.15), 0 8px 16px rgba(217, 119, 87, 0.05);
            --radius-md: 12px;
            --radius-lg: 24px;
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0px); }
        }

        /* Hero Section Styling */
        .hero-container {
            background: linear-gradient(135deg, #1A1A1A 0%, #2D2D2D 100%);
            border-radius: var(--radius-lg);
            padding: 4rem 3rem;
            color: white;
            position: relative;
            overflow: hidden;
            box-shadow: var(--shadow-md);
            margin-bottom: 3rem;
            animation: fadeIn 0.8s ease-out;
        }
        
        .hero-pattern {
            position: absolute;
            top: 0; right: 0; bottom: 0; left: 0;
            background-image: radial-gradient(circle at 100% 0%, rgba(217, 119, 87, 0.15) 0%, transparent 50%),
                              radial-gradient(circle at 0% 100%, rgba(217, 119, 87, 0.1) 0%, transparent 50%);
            pointer-events: none;
        }

        .hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3rem;
            font-weight: 700;
            margin: 0;
            background: linear-gradient(90deg, #FFFFFF 0%, #FFD1C1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.03em;
            line-height: 1.1;
        }

        .hero-subtitle {
            font-family: 'Outfit', sans-serif;
            font-size: 1.1rem;
            color: rgba(255, 255, 255, 0.7);
            margin-top: 1rem;
            font-weight: 300;
            max-width: 600px;
        }

        /* Card Grid Styling */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-top: 2rem;
        }

        .feature-card {
            background: var(--bg-card);
            border-radius: var(--radius-md);
            padding: 2rem;
            border: 1px solid rgba(0,0,0,0.04);
            box-shadow: var(--shadow-sm);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            height: 100%;
            position: relative;
            overflow: hidden;
            cursor: pointer;
            text-decoration: none !important;
        }

        .feature-card:hover {
            transform: translateY(-8px);
            box-shadow: var(--shadow-lg);
            border-color: rgba(217, 119, 87, 0.2);
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
            background: var(--primary);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .feature-card:hover::before {
            opacity: 1;
        }

        .icon-box {
            width: 56px;
            height: 56px;
            background: var(--primary-light);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            color: var(--primary);
            transition: transform 0.3s ease;
        }

        .feature-card:hover .icon-box {
            transform: scale(1.1) rotate(5deg);
            background: var(--primary);
            color: white;
        }
        
        .feature-card:hover .icon-box svg {
             fill: white !important; /* Force fill change on hover if SVG uses fill */
        }

        .card-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 0.75rem;
        }

        .card-list {
            margin: 0;
            padding: 0;
            list-style: none;
        }

        .card-list li {
            font-family: 'Outfit', sans-serif;
            color: var(--text-muted);
            font-size: 0.9rem;
            padding: 0.25rem 0;
            display: flex;
            align-items: center;
        }
        
        .card-list li::before {
            content: "•";
            color: var(--primary);
            margin-right: 0.5rem;
            font-weight: bold;
        }

        /* Utility */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #F1F1F1;
            color: #666;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-family: 'Outfit', sans-serif;
        }
        
    </style>
    """, unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
    <div class="hero-container">
        <div class="hero-pattern"></div>
        <span class="badge">V2.0.0 Alpha</span>
        <h1 class="hero-title">Quantitative Intelligence</h1>
        <p class="hero-subtitle">
            Advanced analytics for Macro, Index, and Market data. 
            Empowering data-driven investment decisions with real-time visualization.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    # We use st.columns but wrap the content in our custom HTML structure
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    # Adjust Icons size for the new layout
    macro_icon = ICONS['macro'].replace('width="18"', 'width="28"').replace('height="18"', 'height="28"')
    index_icon = ICONS['index'].replace('width="18"', 'width="28"').replace('height="18"', 'height="28"')
    stock_icon = ICONS['stock'].replace('width="18"', 'width="28"').replace('height="18"', 'height="28"')
    
    def create_card(icon, title, items, delay="0s"):
        return f"""
        <div class="feature-card" style="animation: fadeIn 0.6s ease-out {delay} backwards;">
            <div class="icon-box">
                {icon}
            </div>
            <div class="card-title">{title}</div>
            <ul class="card-list">
                {''.join([f'<li>{item}</li>' for item in items])}
            </ul>
        </div>
        """

    with col1:
        st.markdown(create_card(
            macro_icon, 
            "Macro Economics", 
            ["PMI Manufacturing Index", "Money Supply (M0/M1/M2)", "Social Financing Aggregates"],
            delay="0.1s"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_card(
            index_icon, 
            "Market Indices", 
            ["Index Composition & Filtering", "Constituent Weight Analysis", "Historical Performance Tracking"],
            delay="0.2s"
        ), unsafe_allow_html=True)
        
    with col3:
        st.markdown(create_card(
            stock_icon, 
            "Equity Analysis", 
            ["Real-time Listing Statistics", "Fundamental Data & Metrics", "Market-wide Overview"],
            delay="0.3s"
        ), unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
