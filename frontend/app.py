"""frontend/app.py"""
import streamlit as st

st.set_page_config(
    page_title="ScoutingReport",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "page" not in st.session_state:
    st.session_state.page = "search"

nav_items = [
    ("search",  "01", "PLAYER SEARCH"),
    ("stats",   "02", "CAREER STATS"),
    ("report",  "03", "SCOUTING REPORT"),
    ("matchup", "04", "MATCHUP"),
    ("today",   "05", "TODAY'S GAMES"),
]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,600;1,300&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0a0a;
    color: #e8e0d0;
}
.stApp { background-color: #0a0a0a; }
#MainMenu, footer, header, button[data-testid="collapsedControl"] { visibility: hidden; }

section[data-testid="stSidebar"] {
    background-color: #0d0d0d !important;
    border-right: 1px solid #1a1a1a !important;
}
section[data-testid="stSidebar"] * { color: #e8e0d0 !important; }
section[data-testid="stSidebar"] .stRadio label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0.4rem 0 !important;
}
section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.2em !important;
}

.logo-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    letter-spacing: 0.12em;
    color: #e8e0d0;
    line-height: 1;
    margin-bottom: 0.1rem;
}
.logo-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.3em;
    color: #c0392b;
    text-transform: uppercase;
    margin-bottom: 2rem;
}
.player-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem;
    letter-spacing: 0.08em;
    line-height: 1;
    color: #e8e0d0;
}
.player-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #888;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}
.stat-card {
    background: #111;
    border: 1px solid #222;
    border-top: 3px solid #c0392b;
    padding: 1.2rem 1rem;
    margin-bottom: 0.5rem;
}
.stat-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 0.3rem;
}
.stat-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    letter-spacing: 0.05em;
    color: #e8e0d0;
    line-height: 1;
}
.stat-value.highlight { color: #c0392b; }
.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #c0392b;
    border-bottom: 1px solid #222;
    padding-bottom: 0.5rem;
    margin: 2rem 0 1rem 0;
}
.report-body {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.95rem;
    line-height: 1.75;
    color: #c8c0b0;
    background: #0f0f0f;
    border-left: 3px solid #c0392b;
    padding: 1.5rem 2rem;
    margin-top: 1rem;
}
.report-body h2 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 0.1em;
    color: #e8e0d0;
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
}
.stTextInput input {
    background: #111 !important;
    border: 1px solid #333 !important;
    border-radius: 0 !important;
    color: #e8e0d0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stTextInput input:focus { border-color: #c0392b !important; box-shadow: none !important; }
.stButton button {
    background: #c0392b !important;
    color: #e8e0d0 !important;
    border: none !important;
    border-radius: 0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.5rem !important;
}
.stButton button:hover { background: #a93226 !important; }
.stSelectbox select, div[data-baseweb="select"] {
    background: #111 !important;
    border-radius: 0 !important;
    border-color: #333 !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid #222; }
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: #666 !important;
}
.stTabs [aria-selected="true"] { color: #c0392b !important; border-bottom: 2px solid #c0392b !important; }
.stDataFrame { font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important; }
hr { border-color: #222 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="logo-header" style="font-size:2.5rem;">SR</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Scouting Report<br>by Cameron Cooper</div>', unsafe_allow_html=True)
    st.markdown("---")
    for key, num, label in nav_items:
        if st.button(f"{num}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

# Page routing
page = st.session_state.page
if page == "search":
    from frontend.views.search import render
elif page == "stats":
    from frontend.views.stats import render
elif page == "report":
    from frontend.views.report import render
elif page == "matchup":
    from frontend.views.matchup import render
else:
    from frontend.views.today import render

render()
