"""frontend/views/stats.py"""
import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

API_BASE = "http://localhost:8000"
HEADSHOT_URL = "https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{mlb_id}/headshot/67/current"

HITTING_DISPLAY = {
    "avg": "AVG", "obp": "OBP", "slg": "SLG", "ops": "OPS",
    "homeRuns": "HR", "rbi": "RBI", "runs": "R", "hits": "H",
    "stolenBases": "SB", "strikeOuts": "K", "walks": "BB",
    "doubles": "2B", "triples": "3B", "gamesPlayed": "G",
    "plateAppearances": "PA", "atBats": "AB",
}

PITCHING_DISPLAY = {
    "era": "ERA", "whip": "WHIP", "wins": "W", "losses": "L",
    "saves": "SV", "strikeOuts": "K", "inningsPitched": "IP",
    "strikeoutsPer9Inn": "K/9", "walksPer9Inn": "BB/9",
    "hitsPer9Inn": "H/9", "gamesPlayed": "G", "gamesStarted": "GS",
    "qualityStarts": "QS", "holds": "HLD",
}


def make_trend_chart(data: list, metric: str, label: str, color: str = "#c0392b"):
    seasons = [d["season"] for d in data if d["stats"].get(metric) is not None]
    values = [float(d["stats"][metric]) for d in data if d["stats"].get(metric) is not None]
    if not seasons:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=seasons, y=values,
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=6, color=color),
        fill="tozeroy",
        fillcolor="rgba(192,57,43,0.08)",
        name=label,
    ))
    fig.update_layout(
        height=200,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(family="IBM Plex Mono", size=10, color="#666"),
        xaxis=dict(showgrid=False, color="#444", tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#1a1a1a", color="#444", tickfont=dict(size=9)),
        showlegend=False,
    )
    return fig


def render():
    player_id = st.session_state.get("selected_player_id")
    player_name = st.session_state.get("selected_player_name", "Select a player first")

    if not player_id:
        st.markdown('<div class="logo-header">Career Stats</div>', unsafe_allow_html=True)
        st.markdown('<div class="logo-sub">Search for a player first</div>', unsafe_allow_html=True)
        st.info("Go to Player Search and select a player.")
        return

    with st.spinner("Loading..."):
        try:
            p = requests.get(f"{API_BASE}/players/{player_id}", timeout=10).json()
        except:
            st.error("Could not load player data.")
            return

    pos = p.get("position", "")
    headshot_url = HEADSHOT_URL.format(mlb_id=player_id)

    col_photo, col_info = st.columns([1, 6])
    with col_photo:
        st.markdown(f"""
        <img src="{headshot_url}" style="width:120px;border-bottom:3px solid #c0392b;"
            onerror="this.style.display='none'">
        """, unsafe_allow_html=True)
    with col_info:
        st.markdown(f'<div class="logo-header" style="font-size:3rem;">{player_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="player-meta">{p.get("team","Free Agent")} · {pos} · Bats {p.get("bats","?")} / Throws {p.get("throws","?")} · {p.get("height","?")} {p.get("weight","?")}lbs · Debut {p.get("debut","?")}</div>', unsafe_allow_html=True)

    is_pitcher = pos in ["SP", "RP", "P", "CL"]
    stat_group = "pitching" if is_pitcher else "hitting"
    if not is_pitcher:
        stat_group = st.radio("", ["hitting", "pitching"], horizontal=True, label_visibility="collapsed")

    with st.spinner("Fetching career stats..."):
        try:
            career = requests.get(f"{API_BASE}/players/{player_id}/stats/career", params={"group": stat_group}, timeout=15).json()
        except Exception as e:
            st.error(f"Stats error: {e}")
            return

    if not career:
        st.warning("No career stats found.")
        return

    latest = career[-1] if career else None
    if latest:
        st.markdown('<div class="section-header">Most Recent Season</div>', unsafe_allow_html=True)
        display_map = PITCHING_DISPLAY if stat_group == "pitching" else HITTING_DISPLAY
        key_stats = list(display_map.items())[:8]
        cols = st.columns(len(key_stats))
        for i, (key, label) in enumerate(key_stats):
            val = latest["stats"].get(key)
            if val is not None:
                with cols[i]:
                    highlight = key in ["ops", "era", "homeRuns", "strikeOuts", "wins"]
                    cls = "highlight" if highlight else ""
                    st.markdown(f'<div class="stat-card"><div class="stat-label">{label} {latest["season"]}</div><div class="stat-value {cls}">{val}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Career Trends</div>', unsafe_allow_html=True)
    if stat_group == "hitting":
        chart_metrics = [("ops", "OPS"), ("homeRuns", "Home Runs"), ("avg", "Batting Avg"), ("rbi", "RBI")]
    else:
        chart_metrics = [("era", "ERA"), ("strikeOuts", "Strikeouts"), ("whip", "WHIP"), ("wins", "Wins")]

    cols = st.columns(2)
    for i, (metric, label) in enumerate(chart_metrics):
        fig = make_trend_chart(career, metric, label)
        if fig:
            with cols[i % 2]:
                st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.65rem;color:#c0392b;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:0.3rem;">{label}</div>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Career Stats Table</div>', unsafe_allow_html=True)
    display_map = PITCHING_DISPLAY if stat_group == "pitching" else HITTING_DISPLAY
    rows = []
    for s in career:
        row = {"Season": s["season"], "Team": s.get("team", "")}
        for key, label in display_map.items():
            val = s["stats"].get(key)
            if val is not None:
                row[label] = val
        rows.append(row)
    if rows:
        df = pd.DataFrame(rows).sort_values("Season", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)