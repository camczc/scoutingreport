"""frontend/views/report.py"""
import streamlit as st
import requests

API_BASE = "http://localhost:8000"
HEADSHOT_URL = "https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{mlb_id}/headshot/67/current"


def render():
    player_id = st.session_state.get("selected_player_id")
    player_name = st.session_state.get("selected_player_name", "Select a player first")

    st.markdown('<div class="logo-header">Scouting Report</div>', unsafe_allow_html=True)

    if not player_id:
        st.markdown('<div class="logo-sub">AI-Powered MLB Player Analysis</div>', unsafe_allow_html=True)
        st.info("Go to Player Search and select a player first.")
        return

    # Player header with headshot
    try:
        p = requests.get(f"{API_BASE}/players/{player_id}", timeout=10).json()
        pos = p.get("position", "")
        headshot_url = HEADSHOT_URL.format(mlb_id=player_id)
        col_photo, col_info = st.columns([1, 5])
        with col_photo:
            st.markdown(f"""
            <img src="{headshot_url}" style="width:120px;border-bottom:3px solid #c0392b;"
                onerror="this.style.display='none'">
            """, unsafe_allow_html=True)
        with col_info:
            st.markdown(f'<div class="logo-header" style="font-size:3rem;">{player_name}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="logo-sub">{p.get("team","")}</div>', unsafe_allow_html=True)
    except:
        st.markdown(f'<div class="logo-sub">{player_name}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        season = st.selectbox("Season", list(range(2025, 2014, -1)), index=0)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button("Generate Report", use_container_width=True)
    with col3:
        question = st.text_input("", placeholder="Optional: Ask a specific question...", label_visibility="collapsed")

    if generate:
        with st.spinner(f"Scouting {player_name}..."):
            try:
                params = {"season": season}
                if question:
                    params["question"] = question
                resp = requests.get(f"{API_BASE}/players/{player_id}/report", params=params, timeout=60)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                st.error(f"Error: {e}")
                return

        report = data.get("report", "")
        stat_group = data.get("stat_group", "hitting")

        st.markdown('<div class="section-header">Report</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-body">{report}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-header">Quick Stats Reference</div>', unsafe_allow_html=True)
        try:
            career = requests.get(f"{API_BASE}/players/{player_id}/stats/career", params={"group": stat_group}, timeout=15).json()
            season_data = next((s for s in career if s["season"] == season), None)
            if season_data:
                stats = season_data["stats"]
                if stat_group == "hitting":
                    cols = st.columns(6)
                    for col, (key, label) in zip(cols, [("avg","AVG"),("obp","OBP"),("slg","SLG"),("ops","OPS"),("homeRuns","HR"),("rbi","RBI")]):
                        with col:
                            st.markdown(f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{stats.get(key,"—")}</div></div>', unsafe_allow_html=True)
                else:
                    cols = st.columns(6)
                    for col, (key, label) in zip(cols, [("era","ERA"),("whip","WHIP"),("wins","W"),("strikeOuts","K"),("inningsPitched","IP"),("strikeoutsPer9Inn","K/9")]):
                        with col:
                            st.markdown(f'<div class="stat-card"><div class="stat-label">{label}</div><div class="stat-value">{stats.get(key,"—")}</div></div>', unsafe_allow_html=True)
        except:
            pass
    else:
        st.markdown("""
        <div style="border: 1px dashed #222; padding: 3rem; text-align: center; margin-top: 2rem;">
            <div style="font-family: Bebas Neue, sans-serif; font-size: 1.5rem; color: #333; letter-spacing: 0.1em;">
                SELECT A SEASON AND GENERATE REPORT
            </div>
            <div style="font-family: IBM Plex Mono, monospace; font-size: 0.65rem; color: #444; margin-top: 0.5rem; letter-spacing: 0.15em;">
                CLAUDE WILL ANALYZE CAREER STATS AND PRODUCE A PROFESSIONAL SCOUTING REPORT
            </div>
        </div>
        """, unsafe_allow_html=True)