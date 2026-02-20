import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

API = "http://localhost:8000"

FEATURED_PLAYERS = {
    "Shohei Ohtani": 660271,
    "Aaron Judge": 592450,
    "Mookie Betts": 605141,
    "Freddie Freeman": 518692,
    "Juan Soto": 665742,
    "Corbin Carroll": 682998,
    "Julio Rodriguez": 677594,
    "Jose Ramirez": 608070,
    "Yordan Alvarez": 670541,
    "Gerrit Cole": 543037,
    "Spencer Strider": 675911,
    "Zack Wheeler": 554430,
    "Carlos Rodon": 607074,
    "Byron Buxton": 621439,
}

HITTING_METRICS = ["avg", "obp", "slg", "ops", "home_runs", "rbi", "stolen_bases", "strikeouts", "babip"]
PITCHING_METRICS = ["era", "whip", "k_per_9", "bb_per_9", "wins", "innings_pitched", "batting_avg_against"]


def render():
    st.markdown("# ⚖️ Compare Players")
    st.caption("Side-by-side stat comparison for 2-3 players")

    with st.sidebar:
        st.subheader("Player 1")
        p1 = st.selectbox("Player 1", [""] + list(FEATURED_PLAYERS.keys()), key="p1")
        st.subheader("Player 2")
        p2 = st.selectbox("Player 2", [""] + list(FEATURED_PLAYERS.keys()), key="p2")
        st.subheader("Player 3 (optional)")
        p3 = st.selectbox("Player 3", [""] + list(FEATURED_PLAYERS.keys()), key="p3")
        season = st.selectbox("Season", [2024, 2023, 2022, 2021, 2020])
        compare_btn = st.button("⚖️ Compare", type="primary")

    players = [(name, FEATURED_PLAYERS[name]) for name in [p1, p2, p3] if name]
    if len(players) < 2:
        st.divider()
        st.markdown("Select at least 2 players in the sidebar to compare.")
        return

    if not compare_btn:
        st.divider()
        st.markdown("Click **Compare** in the sidebar to run the comparison.")
        return

    with st.spinner("Loading player data..."):
        profiles = {}
        hitting = {}
        pitching = {}
        for name, mid in players:
            try:
                requests.post(f"{API}/players/{mid}", timeout=10)
                p = requests.get(f"{API}/players/{mid}/profile", timeout=10).json()
                profiles[mid] = p
                requests.post(f"{API}/players/{mid}/fetch-stats", timeout=30)
                h = requests.get(f"{API}/players/{mid}/hitting", timeout=10).json()
                hitting[mid] = {s["season"]: s for s in h} if h else {}
                pit = requests.get(f"{API}/players/{mid}/pitching", timeout=10).json()
                pitching[mid] = {s["season"]: s for s in pit} if pit else {}
            except Exception as e:
                st.error(f"Error loading {name}: {e}")

    # Determine type (use first player)
    first_pos = profiles.get(players[0][1], {}).get("position", "")
    is_pitcher = first_pos in ("SP", "RP", "P", "CP")
    metrics = PITCHING_METRICS if is_pitcher else HITTING_METRICS

    st.divider()

    # Side-by-side profile cards
    cols = st.columns(len(players))
    for i, (name, mid) in enumerate(players):
        p = profiles.get(mid, {})
        with cols[i]:
            st.markdown(f"### {p.get('full_name', name)}")
            st.markdown(f"**{p.get('position','')} | {p.get('team','')}**")
            st.caption(f"Bats/Throws: {p.get('bats','')}/{p.get('throws','')} · Debut: {(p.get('debut_date','')[:4])}")

            stats_src = pitching if is_pitcher else hitting
            season_stats = stats_src.get(mid, {}).get(season, {})
            if season_stats:
                if not is_pitcher:
                    st.metric("OPS", f"{season_stats.get('ops', 0):.3f}")
                    st.metric("AVG", f"{season_stats.get('avg', 0):.3f}")
                    st.metric("HR", season_stats.get('home_runs', 0))
                else:
                    st.metric("ERA", f"{season_stats.get('era', 0):.2f}")
                    st.metric("WHIP", f"{season_stats.get('whip', 0):.2f}")
                    st.metric("K/9", f"{season_stats.get('k_per_9', 0):.1f}")
            else:
                st.info(f"No {season} stats")

    st.divider()

    # Comparison table
    st.subheader(f"📊 {season} Stats Comparison")
    rows = []
    for metric in metrics:
        row = {"Metric": metric.upper().replace("_", " ")}
        for name, mid in players:
            stats_src = pitching if is_pitcher else hitting
            val = stats_src.get(mid, {}).get(season, {}).get(metric, "—")
            if isinstance(val, float):
                val = round(val, 3)
            row[profiles.get(mid, {}).get("full_name", name)] = val
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Radar chart
    st.subheader("🕸️ Radar Comparison")
    radar_metrics = ["avg", "obp", "slg", "ops", "home_runs"] if not is_pitcher else ["era", "whip", "k_per_9", "bb_per_9", "innings_pitched"]
    fig = go.Figure()
    colors = ["#6c63ff", "#00c853", "#ff9800"]
    for i, (name, mid) in enumerate(players):
        stats_src = pitching if is_pitcher else hitting
        season_stats = stats_src.get(mid, {}).get(season, {})
        vals = [float(season_stats.get(m, 0) or 0) for m in radar_metrics]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=[m.upper().replace("_", " ") for m in radar_metrics] + [radar_metrics[0].upper()],
            name=profiles.get(mid, {}).get("full_name", name),
            line=dict(color=colors[i % len(colors)], width=2),
            fill="toself",
            opacity=0.3,
        ))
    fig.update_layout(height=400, polar=dict(radialaxis=dict(visible=True)), margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

    # Career OPS/ERA trend overlay
    st.subheader("📈 Career Trend Overlay")
    fig2 = go.Figure()
    for i, (name, mid) in enumerate(players):
        stats_src = pitching if is_pitcher else hitting
        career = sorted(stats_src.get(mid, {}).items())
        if not career:
            continue
        seasons = [s for s, _ in career]
        key_metric = "era" if is_pitcher else "ops"
        vals = [float(d.get(key_metric, 0) or 0) for _, d in career]
        fig2.add_trace(go.Scatter(
            x=seasons, y=vals,
            name=profiles.get(mid, {}).get("full_name", name),
            line=dict(color=colors[i % len(colors)], width=2),
            mode="lines+markers",
        ))
    fig2.update_layout(
        height=350,
        yaxis_title="ERA" if is_pitcher else "OPS",
        hovermode="x unified",
        margin=dict(t=10, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True)
