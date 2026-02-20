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
    "Jose Ramirez": 608070,
    "Yordan Alvarez": 670541,
    "Gerrit Cole": 543037,
    "Spencer Strider": 675911,
    "Zack Wheeler": 554430,
}


def render():
    st.markdown("# 📅 Game Logs")
    st.caption("Game-by-game performance for any MLB player")

    with st.sidebar:
        st.subheader("Game Log Config")
        featured = st.selectbox("Player", [""] + list(FEATURED_PLAYERS.keys()))
        custom_id = st.text_input("Or MLB ID", placeholder="e.g. 660271")
        season = st.selectbox("Season", [2024, 2023, 2022, 2021, 2020])
        load = st.button("📥 Load Game Logs", type="primary")

    mlb_id = None
    if featured:
        mlb_id = FEATURED_PLAYERS[featured]
    elif custom_id:
        try:
            mlb_id = int(custom_id)
        except:
            st.error("Invalid MLB ID")
            return

    if not mlb_id or not load:
        st.divider()
        st.markdown("Select a player in the sidebar and click **Load Game Logs**.")
        return

    # Figure out stat type
    with st.spinner("Loading..."):
        try:
            requests.post(f"{API}/players/{mlb_id}", timeout=10)
            profile_resp = requests.get(f"{API}/players/{mlb_id}/profile", timeout=10)
            profile = profile_resp.json()
            is_pitcher = profile.get("position", "") in ("SP", "RP", "P", "CP")
            stat_type = "pitching" if is_pitcher else "hitting"

            logs_resp = requests.get(
                f"{API}/players/{mlb_id}/gamelogs",
                params={"season": season, "stat_type": stat_type},
                timeout=30,
            )
            logs = logs_resp.json()
        except Exception as e:
            st.error(f"Error: {e}")
            return

    if not logs:
        st.warning("No game logs found. Try fetching stats first from the Player Scout page.")
        return

    st.divider()
    st.subheader(f"📋 {profile.get('full_name', '')} — {season} Game Log")

    rows = []
    for g in logs:
        row = {"Date": g["game_date"], "Opponent": g["opponent"], "H/A": g["home_away"]}
        row.update(g.get("stats", {}))
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Rolling average chart
    if not is_pitcher and "avg" in df.columns:
        st.subheader("📈 Rolling AVG (10-game)")
        df["avg_num"] = pd.to_numeric(df.get("avg", 0), errors="coerce").fillna(0)
        df["rolling_avg"] = df["avg_num"].rolling(10, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["avg_num"], name="Game AVG", line=dict(color="#aaaaaa", width=1), opacity=0.5))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["rolling_avg"], name="10-Game Rolling", line=dict(color="#6c63ff", width=2)))
        fig.update_layout(height=300, margin=dict(t=10, b=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    if is_pitcher and "era" in df.columns:
        st.subheader("📈 ERA by Game")
        df["era_num"] = pd.to_numeric(df.get("era", 0), errors="coerce").fillna(0)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["Date"], y=df["era_num"], name="ERA", marker_color="#f44336"))
        fig.update_layout(height=300, margin=dict(t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
