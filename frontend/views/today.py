"""frontend/views/today.py - Today's Games with pitcher heatmaps"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import anthropic
import os
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8000"
HEADSHOT_URL = "https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{mlb_id}/headshot/67/current"
TEAM_LOGO_URL = "https://www.mlbstatic.com/team-logos/{team_id}.svg"


def get_today_games():
    try:
        resp = requests.get(f"{API_BASE}/games/today", timeout=10)
        return resp.json()
    except:
        return []


def get_pitcher_heatmap(mlb_id: int, season: int = 2024):
    try:
        resp = requests.get(f"{API_BASE}/games/pitcher-heatmap/{mlb_id}", params={"season": season}, timeout=60)
        return resp.json()
    except:
        return {}


def get_pitcher_vs_team(pitcher_id: int, team_id: int):
    try:
        resp = requests.get(f"{API_BASE}/games/pitcher-vs-team/{pitcher_id}/{team_id}", timeout=30)
        return resp.json()
    except:
        return []


def draw_strike_zone():
    shapes = [
        # Outer strike zone — brighter, thicker
        dict(type="rect", x0=-0.83, x1=0.83, y0=1.5, y1=3.5,
             line=dict(color="#aaa", width=2), fillcolor="rgba(0,0,0,0)"),
        # Home plate outline
        dict(type="rect", x0=-0.71, x1=0.71, y0=0.0, y1=0.3,
             line=dict(color="#555", width=1), fillcolor="rgba(255,255,255,0.03)"),
    ]
    # Inner grid lines
    shapes += [
        dict(type="line", x0=-0.83/3, x1=-0.83/3, y0=1.5, y1=3.5,
             line=dict(color="#555", width=1, dash="dot")),
        dict(type="line", x0=0.83/3, x1=0.83/3, y0=1.5, y1=3.5,
             line=dict(color="#555", width=1, dash="dot")),
        dict(type="line", x0=-0.83, x1=0.83, y0=1.5+(2/3), y1=1.5+(2/3),
             line=dict(color="#555", width=1, dash="dot")),
        dict(type="line", x0=-0.83, x1=0.83, y0=1.5+(4/3), y1=1.5+(4/3),
             line=dict(color="#555", width=1, dash="dot")),
    ]
    return shapes


def render_heatmap(pitch_data: dict, pitch_type_filter: str = "ALL", hand_filter: str = "ALL"):
    if not pitch_data or not pitch_data.get("pitches"):
        st.markdown('<div style="color:#444;font-family:IBM Plex Mono,monospace;font-size:0.7rem;letter-spacing:0.2em;">NO PITCH DATA AVAILABLE</div>', unsafe_allow_html=True)
        return

    pitches = pitch_data["pitches"]
    df = pd.DataFrame(pitches)

    if pitch_type_filter != "ALL" and "pitch_name" in df.columns:
        df = df[df["pitch_name"] == pitch_type_filter]
    if hand_filter != "ALL" and "stand" in df.columns:
        df = df[df["stand"] == hand_filter]

    if df.empty or "plate_x" not in df.columns:
        st.markdown('<div style="color:#444;font-family:IBM Plex Mono,monospace;font-size:0.7rem;">NO DATA FOR SELECTION</div>', unsafe_allow_html=True)
        return

    df = df.dropna(subset=["plate_x", "plate_z"])

    fig = go.Figure()

    # Heatmap contour
    fig.add_trace(go.Histogram2dContour(
        x=df["plate_x"], y=df["plate_z"],
        colorscale=[
            [0,   "rgba(0,0,0,0)"],
            [0.15, "rgba(192,57,43,0.15)"],
            [0.4, "rgba(192,57,43,0.5)"],
            [0.7, "rgba(192,57,43,0.85)"],
            [1.0, "rgba(220,80,60,1.0)"],
        ],
        showscale=False, ncontours=15,
        contours=dict(showlines=False),
    ))

    # Scatter dots — larger, more visible
    colors_by_type = {
        "Four-Seam Fastball": "#e8e0d0",
        "Sinker": "#b0b0b0",
        "Slider": "#e74c3c",
        "Curveball": "#3498db",
        "Changeup": "#2ecc71",
        "Cutter": "#f39c12",
        "Sweeper": "#9b59b6",
        "Splitter": "#1abc9c",
    }
    if "pitch_name" in df.columns:
        for pname, grp in df.groupby("pitch_name"):
            color = colors_by_type.get(pname, "#888")
            fig.add_trace(go.Scatter(
                x=grp["plate_x"], y=grp["plate_z"],
                mode="markers",
                marker=dict(size=5, color=color, opacity=0.6,
                            line=dict(width=0.5, color="rgba(0,0,0,0.3)")),
                name=pname,
                hovertemplate=f"<b>{pname}</b><br>X: %{{x:.2f}}<br>Z: %{{y:.2f}}<extra></extra>"
            ))

    fig.update_layout(
        shapes=draw_strike_zone(),
        xaxis=dict(
            range=[-2.5, 2.5], zeroline=False, showgrid=False,
            tickfont=dict(family="IBM Plex Mono", size=10, color="#555"),
            title=dict(text="← ARM SIDE    GLOVE SIDE →",
                       font=dict(family="IBM Plex Mono", size=9, color="#555"))
        ),
        yaxis=dict(
            range=[0.0, 5.5], zeroline=False, showgrid=False,
            tickfont=dict(family="IBM Plex Mono", size=10, color="#555")
        ),
        paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
        margin=dict(l=20, r=120, t=20, b=40), height=480,
        showlegend=True,
        legend=dict(
            font=dict(family="IBM Plex Mono", size=10, color="#aaa"),
            bgcolor="rgba(15,15,15,0.8)",
            bordercolor="#333",
            borderwidth=1,
            x=1.02, y=1
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def render():
    st.markdown("<div class='logo-header'>Today's Games</div>", unsafe_allow_html=True)
    today = datetime.now().strftime("%B %d, %Y")
    st.markdown(f'<div class="logo-sub">{today.upper()} — MLB SCHEDULE & PITCHER ANALYSIS</div>', unsafe_allow_html=True)

    with st.spinner("Loading today's schedule..."):
        games = get_today_games()

    if not games:
        st.markdown("""
        <div style="border:1px dashed #222;padding:3rem;text-align:center;margin-top:2rem;">
            <div style="font-family:Bebas Neue,sans-serif;font-size:1.5rem;color:#333;letter-spacing:0.1em;">NO GAMES SCHEDULED TODAY</div>
            <div style="font-family:IBM Plex Mono,monospace;font-size:0.65rem;color:#444;margin-top:0.5rem;letter-spacing:0.15em;">CHECK BACK ON A GAME DAY</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown('<div class="section-header">Select a Game</div>', unsafe_allow_html=True)

    game_labels = []
    for g in games:
        away = g.get("away_name", "TBD")
        home = g.get("home_name", "TBD")
        time_utc = g.get("game_datetime", "")
        try:
            from datetime import timezone
            import pytz
            dt = datetime.strptime(time_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            local_time = dt.astimezone(pytz.timezone("US/Eastern")).strftime("%I:%M %p ET")
        except:
            local_time = "TBD"
        away_pitcher = g.get("away_probable_pitcher") or "TBD"
        home_pitcher = g.get("home_probable_pitcher") or "TBD"
        game_labels.append(f"{away} @ {home}  |  {local_time}  |  {away_pitcher} vs {home_pitcher}")

    selected_idx = st.selectbox("Game", range(len(game_labels)),
                                format_func=lambda i: game_labels[i],
                                label_visibility="collapsed")
    selected_game = games[selected_idx]

    away = selected_game.get("away_name", "")
    home = selected_game.get("home_name", "")
    away_id = selected_game.get("away_id")
    home_id = selected_game.get("home_id")
    venue = selected_game.get("venue_name", "")
    game_type = selected_game.get("game_type", "")
    type_label = "SPRING TRAINING" if game_type == "S" else "REGULAR SEASON" if game_type == "R" else game_type

    away_logo = TEAM_LOGO_URL.format(team_id=away_id)
    home_logo = TEAM_LOGO_URL.format(team_id=home_id)

    st.markdown(f"""
    <div style="margin:1.5rem 0;padding:1.5rem 2rem;background:#111;border:1px solid #222;border-top:3px solid #c0392b;display:flex;align-items:center;gap:2rem;">
        <img src="{away_logo}" style="width:60px;height:60px;object-fit:contain;opacity:0.9;" onerror="this.style.display='none'">
        <div style="flex:1;">
            <div style="font-family:Bebas Neue,sans-serif;font-size:2.5rem;letter-spacing:0.08em;color:#e8e0d0;line-height:1;">
                {away} <span style="color:#333;font-size:1.5rem;">@</span> {home}
            </div>
            <div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;color:#555;letter-spacing:0.2em;margin-top:0.3rem;">
                {type_label} · {venue}
            </div>
        </div>
        <img src="{home_logo}" style="width:60px;height:60px;object-fit:contain;opacity:0.9;" onerror="this.style.display='none'">
    </div>
    """, unsafe_allow_html=True)

    preview_key = f"preview_{selected_game.get('game_id')}"
    if st.button("⚡ AI Game Preview", key=f"btn_{preview_key}"):
        away_pitcher = selected_game.get("away_probable_pitcher", "TBD")
        home_pitcher = selected_game.get("home_probable_pitcher", "TBD")
        away_pitcher_id = selected_game.get("away_pitcher_id")
        home_pitcher_id = selected_game.get("home_pitcher_id")

        with st.spinner("Generating game preview..."):
            def get_pitcher_stats(pid):
                if not pid:
                    return {}
                try:
                    career = requests.get(f"{API_BASE}/players/{pid}/stats/career", params={"group": "pitching"}, timeout=15).json()
                    info = requests.get(f"{API_BASE}/players/{pid}", timeout=10).json()
                    recent = career[-3:] if career else []
                    lines = []
                    for s in recent:
                        st2 = s["stats"]
                        lines.append(f"  {s['season']}: ERA {st2.get('era','?')} | WHIP {st2.get('whip','?')} | K {st2.get('strikeOuts','?')} | W {st2.get('wins','?')} | IP {st2.get('inningsPitched','?')}")
                    return {"name": info.get("full_name", ""), "throws": info.get("throws",""), "lines": "\n".join(lines)}
                except:
                    return {}

            away_stats = get_pitcher_stats(away_pitcher_id)
            home_stats = get_pitcher_stats(home_pitcher_id)

            prompt = f"""Generate a concise, engaging game preview for tonight's MLB game.

{away} @ {home} at {venue}

AWAY STARTER: {away_pitcher} (Throws: {away_stats.get('throws','?')})
Recent stats:
{away_stats.get('lines', 'No data')}

HOME STARTER: {home_pitcher} (Throws: {home_stats.get('throws','?')})
Recent stats:
{home_stats.get('lines', 'No data')}

Write a 3-4 paragraph game preview covering:
1. The pitching matchup and who has the edge
2. Key storylines or narratives for tonight
3. What to watch for offensively
4. Your predicted outcome and final score

Be specific, use the actual stats, and write like a beat reporter."""

            try:
                client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                resp = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}]
                )
                st.session_state[preview_key] = resp.content[0].text
            except Exception as e:
                st.error(f"Preview failed: {e}")

    if st.session_state.get(preview_key):
        st.markdown('<div class="section-header">AI Game Preview</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-body">{st.session_state[preview_key]}</div>', unsafe_allow_html=True)

    away_pitcher = selected_game.get("away_probable_pitcher", "")
    home_pitcher = selected_game.get("home_probable_pitcher", "")
    away_pitcher_id = selected_game.get("away_pitcher_id")
    home_pitcher_id = selected_game.get("home_pitcher_id")

    pitchers = []
    if away_pitcher:
        pitchers.append({"name": away_pitcher, "pitcher_id": away_pitcher_id, "team": away, "team_id": away_id, "opponent_id": home_id, "opponent": home, "side": "AWAY"})
    if home_pitcher:
        pitchers.append({"name": home_pitcher, "pitcher_id": home_pitcher_id, "team": home, "team_id": home_id, "opponent_id": away_id, "opponent": away, "side": "HOME"})

    if not pitchers:
        st.markdown('<div style="color:#444;font-family:IBM Plex Mono,monospace;font-size:0.75rem;letter-spacing:0.2em;margin-top:2rem;">PROBABLE PITCHERS NOT YET ANNOUNCED</div>', unsafe_allow_html=True)
        return

    tabs = st.tabs([f"{p['side']}: {p['name']}" for p in pitchers])

    for tab, pitcher in zip(tabs, pitchers):
        with tab:
            pitcher_name = pitcher["name"]
            pitcher_id = pitcher.get("pitcher_id")
            if not pitcher_id:
                st.error(f"No pitcher ID for {pitcher_name}")
                continue

            full_info = requests.get(f"{API_BASE}/players/{pitcher_id}", timeout=10).json()
            headshot_url = HEADSHOT_URL.format(mlb_id=pitcher_id)

            col_photo, col_bio, col_stats = st.columns([1, 2, 4])
            with col_photo:
                st.markdown(f"""
                <img src="{headshot_url}" style="width:120px;border-bottom:3px solid #c0392b;"
                     onerror="this.style.display='none'">
                """, unsafe_allow_html=True)
            with col_bio:
                pos = full_info.get("position", "P")
                throws = full_info.get("throws", "R")
                height = full_info.get("height", "")
                weight = full_info.get("weight", "")
                debut = full_info.get("debut", "")
                st.markdown(f"""
                <div class="player-name" style="font-size:2rem;">{pitcher_name}</div>
                <div class="player-meta">{pitcher["team"]} · {pos} · THROWS {throws}<br>{height} {weight}LBS · DEBUT {debut}</div>
                """, unsafe_allow_html=True)
            with col_stats:
                career = requests.get(f"{API_BASE}/players/{pitcher_id}/stats/career",
                                      params={"group": "pitching"}, timeout=15).json()
                if career:
                    recent = career[-1]
                    s = recent.get("stats", {})
                    season_yr = recent.get("season", "")
                    metrics = [("ERA", s.get("era","—")), ("WHIP", s.get("whip","—")),
                               ("K", s.get("strikeOuts","—")), ("W", s.get("wins","—")),
                               ("IP", s.get("inningsPitched","—")), ("K/9", s.get("strikeoutsPer9Inn","—"))]
                    cols = st.columns(6)
                    for col, (label, val) in zip(cols, metrics):
                        with col:
                            st.markdown(f'<div class="stat-card"><div class="stat-label">{label} {season_yr}</div><div class="stat-value">{val}</div></div>', unsafe_allow_html=True)

            # Heatmap — all 3 filters on one row
            st.markdown('<div class="section-header">Pitch Location Heatmap</div>', unsafe_allow_html=True)

            hm_col1, hm_col2, hm_col3 = st.columns([2, 2, 2])
            with hm_col1:
                season_sel = st.selectbox("Season", [2025, 2024, 2023, 2022], key=f"hm_season_{pitcher_id}")
            with hm_col2:
                hand_filter = st.selectbox("vs Batter Hand", ["ALL", "L", "R"], key=f"hand_{pitcher_id}")

            hm_cache_key = f"heatmap_{pitcher_id}_{season_sel}"
            if hm_cache_key not in st.session_state:
                with st.spinner("Loading pitch data..."):
                    st.session_state[hm_cache_key] = get_pitcher_heatmap(pitcher_id, season_sel)

            heatmap_data = st.session_state.get(hm_cache_key, {})

            if heatmap_data.get("pitches"):
                pitch_types = ["ALL"] + sorted(set(p.get("pitch_name","") for p in heatmap_data["pitches"] if p.get("pitch_name")))
                with hm_col3:
                    pitch_filter = st.selectbox("Pitch Type", pitch_types, key=f"pt_{pitcher_id}")

                total = heatmap_data.get("total_pitches", len(heatmap_data["pitches"]))
                hand_label = f" · VS {hand_filter} BATTERS" if hand_filter != "ALL" else ""
                st.markdown(f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.6rem;color:#555;letter-spacing:0.2em;margin-bottom:0.5rem;">{total} PITCHES · {season_sel} SEASON · CATCHER\'S PERSPECTIVE{hand_label}</div>', unsafe_allow_html=True)
                render_heatmap(heatmap_data, pitch_filter, hand_filter)

                df_pitches = pd.DataFrame(heatmap_data["pitches"])
                if "pitch_name" in df_pitches.columns:
                    st.markdown('<div class="section-header">Pitch Arsenal</div>', unsafe_allow_html=True)
                    mix = df_pitches["pitch_name"].value_counts()
                    mix_pct = (mix / mix.sum() * 100).round(1)
                    cols = st.columns(min(len(mix), 5))
                    for col, (pname, pct) in zip(cols, mix_pct.items()):
                        with col:
                            st.markdown(f'<div class="stat-card"><div class="stat-label">{pname}</div><div class="stat-value" style="font-size:1.6rem;">{pct}%</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="color:#444;font-family:IBM Plex Mono,monospace;font-size:0.65rem;letter-spacing:0.15em;padding:1rem 0;">NO PITCH DATA AVAILABLE FOR THIS SEASON</div>', unsafe_allow_html=True)

            opp_logo = TEAM_LOGO_URL.format(team_id=pitcher["opponent_id"])
            st.markdown(f"""
            <div class="section-header" style="display:flex;align-items:center;gap:0.5rem;">
                <img src="{opp_logo}" style="width:18px;height:18px;object-fit:contain;opacity:0.8;" onerror="this.style.display='none'">
                VS {pitcher["opponent"].upper()} — CAREER HEAD-TO-HEAD
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Loading head-to-head stats..."):
                vs_stats = get_pitcher_vs_team(pitcher_id, pitcher["opponent_id"])

            if vs_stats:
                df_vs = pd.DataFrame(vs_stats)
                if not df_vs.empty:
                    display_cols = [c for c in ["full_name", "position", "atBats", "avg", "obp", "ops", "homeRuns", "strikeOuts", "numberOfPitches"] if c in df_vs.columns]
                    df_display = df_vs[display_cols].rename(columns={
                        "full_name": "Batter", "position": "POS", "atBats": "AB",
                        "avg": "AVG", "obp": "OBP", "ops": "OPS",
                        "homeRuns": "HR", "strikeOuts": "K", "numberOfPitches": "Pitches"
                    })
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.markdown('<div style="color:#333;font-family:IBM Plex Mono,monospace;font-size:0.65rem;letter-spacing:0.15em;">NO HEAD-TO-HEAD DATA AVAILABLE</div>', unsafe_allow_html=True)
