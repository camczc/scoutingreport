import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
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
    "Gerrit Cole": 543037,
    "Spencer Strider": 675911,
    "Zack Wheeler": 554430,
    "Carlos Rodon": 607074,
    "Byron Buxton": 621439,
    "Jose Ramirez": 608070,
    "Yordan Alvarez": 670541,
}


def render():
    st.markdown("# 🔍 Player Scout")
    st.caption("Search any MLB player for career stats, trends, and an AI-generated scouting report")

    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("Search player by name", placeholder="e.g. Shohei Ohtani, Aaron Judge...")
    with col2:
        featured = st.selectbox("Or pick a featured player", [""] + list(FEATURED_PLAYERS.keys()))

    mlb_id = None
    player_name = ""

    if featured:
        mlb_id = FEATURED_PLAYERS[featured]
        player_name = featured
    elif search_query and len(search_query) >= 2:
        with st.spinner("Searching..."):
            try:
                resp = requests.get(f"{API}/players/search", params={"name": search_query}, timeout=10)
                results = resp.json()
            except:
                results = []

        if not results:
            st.warning("No players found.")
            return

        options = {f"{r['full_name']} — {r['position']} | {r['team']}": r['mlb_id'] for r in results[:10]}
        selected = st.selectbox("Select player", list(options.keys()))
        if selected:
            mlb_id = options[selected]
            player_name = selected.split(" —")[0]

    if not mlb_id:
        _render_landing()
        return

    _render_player(mlb_id, player_name)


def _render_landing():
    st.divider()
    st.markdown("### Featured Players")
    cols = st.columns(4)
    stars = ["Shohei Ohtani", "Aaron Judge", "Juan Soto", "Gerrit Cole",
             "Mookie Betts", "Yordan Alvarez", "Jose Ramirez", "Spencer Strider"]
    for i, name in enumerate(stars):
        with cols[i % 4]:
            st.markdown(f"**{name}**")
            st.caption(f"ID: {FEATURED_PLAYERS[name]}")


def _render_player(mlb_id: int, player_name: str):
    with st.spinner(f"Loading {player_name}..."):
        try:
            # Fetch/store player
            requests.post(f"{API}/players/{mlb_id}", timeout=10)
            profile_resp = requests.get(f"{API}/players/{mlb_id}/profile", timeout=10)
            profile = profile_resp.json()

            # Fetch stats
            requests.post(f"{API}/players/{mlb_id}/fetch-stats", timeout=30)
        except Exception as e:
            st.error(f"Error loading player: {e}")
            return

    is_pitcher = profile.get("position", "") in ("SP", "RP", "P", "CP")

    # Header
    st.divider()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Name", profile.get("full_name", player_name))
    c2.metric("Position", profile.get("position", ""))
    c3.metric("Team", profile.get("team", ""))
    c4.metric("Bats/Throws", f"{profile.get('bats','')}/{profile.get('throws','')}")
    c5.metric("Debut", profile.get("debut_date", "")[:4] if profile.get("debut_date") else "")

    st.divider()

    # Stats table + chart
    if is_pitcher:
        _render_pitching_section(mlb_id)
    else:
        _render_hitting_section(mlb_id)

    st.divider()

    # AI Scouting Report
    st.subheader("🤖 AI Scouting Report")
    question = st.text_input("Optional: Ask a specific question about this player", placeholder="e.g. Is he worth a $30M/year contract?")

    col_a, col_b = st.columns(2)
    with col_a:
        gen = st.button("📋 Generate Scouting Report", type="primary")
    with col_b:
        regen = st.button("🔄 Regenerate")

    if gen or regen:
        with st.spinner("Claude is writing the scouting report..."):
            try:
                resp = requests.post(
                    f"{API}/scout/{mlb_id}",
                    json={"season": 2024, "question": question or None, "force_regenerate": regen},
                    timeout=60,
                )
                report = resp.json().get("report", "")
                st.markdown(report)
            except Exception as e:
                st.error(f"Error generating report: {e}")
    else:
        # Check for cached report
        try:
            resp = requests.get(f"{API}/scout/{mlb_id}", params={"season": 2024}, timeout=10)
            cached = resp.json().get("report")
            if cached:
                st.info("Showing cached report — click Regenerate to refresh.")
                st.markdown(cached)
        except:
            pass


def _render_hitting_section(mlb_id: int):
    try:
        resp = requests.get(f"{API}/players/{mlb_id}/hitting", timeout=10)
        stats = resp.json()
    except:
        stats = []

    if not stats:
        st.info("No hitting stats available.")
        return

    df = pd.DataFrame(stats)
    if df.empty:
        return

    st.subheader("📊 Career Hitting Stats")

    # Key metrics for latest season
    latest = df.iloc[-1]
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("AVG", f"{latest.get('avg', 0):.3f}")
    m2.metric("OBP", f"{latest.get('obp', 0):.3f}")
    m3.metric("SLG", f"{latest.get('slg', 0):.3f}")
    m4.metric("OPS", f"{latest.get('ops', 0):.3f}")
    m5.metric("HR", int(latest.get('home_runs', 0)))
    m6.metric("RBI", int(latest.get('rbi', 0)))

    # Career table
    display_cols = ["season", "team", "games", "at_bats", "hits", "home_runs", "rbi", "runs",
                    "stolen_bases", "walks", "strikeouts", "avg", "obp", "slg", "ops", "babip"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    # Trend charts
    st.subheader("📈 Career Trends")
    tab1, tab2, tab3 = st.tabs(["OPS / SLG / OBP", "HR & RBI", "AVG & BABIP"])

    with tab1:
        fig = go.Figure()
        for col, color in [("ops", "#6c63ff"), ("slg", "#00c853"), ("obp", "#ff9800")]:
            if col in df.columns:
                fig.add_trace(go.Scatter(x=df["season"], y=df[col], name=col.upper(), line=dict(color=color, width=2), mode="lines+markers"))
        fig.update_layout(height=300, margin=dict(t=10, b=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = go.Figure()
        if "home_runs" in df.columns:
            fig.add_trace(go.Bar(x=df["season"], y=df["home_runs"], name="HR", marker_color="#6c63ff"))
        if "rbi" in df.columns:
            fig.add_trace(go.Bar(x=df["season"], y=df["rbi"], name="RBI", marker_color="#00c853"))
        fig.update_layout(height=300, barmode="group", margin=dict(t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = go.Figure()
        for col, color in [("avg", "#6c63ff"), ("babip", "#ff9800")]:
            if col in df.columns:
                fig.add_trace(go.Scatter(x=df["season"], y=df[col], name=col.upper(), line=dict(color=color, width=2), mode="lines+markers"))
        fig.update_layout(height=300, margin=dict(t=10, b=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)


def _render_pitching_section(mlb_id: int):
    try:
        resp = requests.get(f"{API}/players/{mlb_id}/pitching", timeout=10)
        stats = resp.json()
    except:
        stats = []

    if not stats:
        st.info("No pitching stats available.")
        return

    df = pd.DataFrame(stats)
    if df.empty:
        return

    st.subheader("📊 Career Pitching Stats")

    latest = df.iloc[-1]
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("ERA", f"{latest.get('era', 0):.2f}")
    m2.metric("WHIP", f"{latest.get('whip', 0):.2f}")
    m3.metric("K/9", f"{latest.get('k_per_9', 0):.1f}")
    m4.metric("BB/9", f"{latest.get('bb_per_9', 0):.1f}")
    m5.metric("W-L", f"{int(latest.get('wins', 0))}-{int(latest.get('losses', 0))}")
    m6.metric("IP", f"{latest.get('innings_pitched', 0):.1f}")

    display_cols = ["season", "team", "games", "games_started", "wins", "losses", "saves",
                    "innings_pitched", "strikeouts", "era", "whip", "k_per_9", "bb_per_9",
                    "k_bb_ratio", "batting_avg_against"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    st.subheader("📈 Career Trends")
    tab1, tab2, tab3 = st.tabs(["ERA & WHIP", "K/9 & BB/9", "Wins & IP"])

    with tab1:
        fig = go.Figure()
        if "era" in df.columns:
            fig.add_trace(go.Scatter(x=df["season"], y=df["era"], name="ERA", line=dict(color="#f44336", width=2), mode="lines+markers"))
        if "whip" in df.columns:
            fig.add_trace(go.Scatter(x=df["season"], y=df["whip"], name="WHIP", line=dict(color="#ff9800", width=2), mode="lines+markers", yaxis="y2"))
        fig.update_layout(height=300, margin=dict(t=10, b=0), hovermode="x unified",
                          yaxis2=dict(overlaying="y", side="right"))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = go.Figure()
        for col, color in [("k_per_9", "#6c63ff"), ("bb_per_9", "#f44336")]:
            if col in df.columns:
                fig.add_trace(go.Scatter(x=df["season"], y=df[col], name=col.upper().replace("_", "/"), line=dict(color=color, width=2), mode="lines+markers"))
        fig.update_layout(height=300, margin=dict(t=10, b=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = go.Figure()
        if "wins" in df.columns:
            fig.add_trace(go.Bar(x=df["season"], y=df["wins"], name="Wins", marker_color="#6c63ff"))
        if "innings_pitched" in df.columns:
            fig.add_trace(go.Bar(x=df["season"], y=df["innings_pitched"], name="IP", marker_color="#00c853"))
        fig.update_layout(height=300, barmode="group", margin=dict(t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
