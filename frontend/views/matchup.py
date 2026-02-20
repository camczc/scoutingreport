"""frontend/views/matchup.py"""
import streamlit as st
import requests
import anthropic, os
from dotenv import load_dotenv

API_BASE = "http://localhost:8000"
HEADSHOT_URL = "https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{mlb_id}/headshot/67/current"


def search_player(query: str):
    try:
        resp = requests.get(f"{API_BASE}/players/search", params={"q": query}, timeout=10)
        return resp.json()
    except:
        return []


def render():
    st.markdown('<div class="logo-header">Matchup Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Batter vs Pitcher — Historical Stats & AI Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Batter</div>', unsafe_allow_html=True)
        batter_query = st.text_input("Batter", placeholder="Search batter...", key="batter_search", label_visibility="collapsed")
        batter_id = None
        batter_name = None
        if batter_query:
            results = search_player(batter_query)
            if results:
                options = {f"{r['full_name']} ({r['position']}, {r['team']})": r['mlb_id'] for r in results[:10]}
                selected = st.selectbox("Select batter", list(options.keys()), key="batter_select")
                batter_id = options[selected]
                batter_name = selected.split(" (")[0]
                # Show headshot
                st.markdown(f"""
                <img src="{HEADSHOT_URL.format(mlb_id=batter_id)}" style="width:100px;border-bottom:3px solid #c0392b;margin-top:0.5rem;"
                     onerror="this.style.display='none'">
                """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">Pitcher</div>', unsafe_allow_html=True)
        pitcher_query = st.text_input("Pitcher", placeholder="Search pitcher...", key="pitcher_search", label_visibility="collapsed")
        pitcher_id = None
        pitcher_name = None
        if pitcher_query:
            results = search_player(pitcher_query)
            pitchers = [r for r in results if r["position"] in ["SP", "RP", "P", "CL"]] or results[:10]
            if pitchers:
                options = {f"{r['full_name']} ({r['position']}, {r['team']})": r['mlb_id'] for r in pitchers[:10]}
                selected = st.selectbox("Select pitcher", list(options.keys()), key="pitcher_select")
                pitcher_id = options[selected]
                pitcher_name = selected.split(" (")[0]
                # Show headshot
                st.markdown(f"""
                <img src="{HEADSHOT_URL.format(mlb_id=pitcher_id)}" style="width:100px;border-bottom:3px solid #c0392b;margin-top:0.5rem;"
                     onerror="this.style.display='none'">
                """, unsafe_allow_html=True)

    st.markdown("---")

    if batter_id and pitcher_id:
        season = st.selectbox("Analysis Season", list(range(2024, 2019, -1)))
        analyze = st.button("Analyze Matchup", use_container_width=False)

        if analyze:
            with st.spinner("Analyzing matchup..."):
                try:
                    batter_career = requests.get(f"{API_BASE}/players/{batter_id}/stats/career", params={"group": "hitting"}, timeout=15).json()
                    pitcher_career = requests.get(f"{API_BASE}/players/{pitcher_id}/stats/career", params={"group": "pitching"}, timeout=15).json()
                    batter_info = requests.get(f"{API_BASE}/players/{batter_id}", timeout=10).json()
                    pitcher_info = requests.get(f"{API_BASE}/players/{pitcher_id}", timeout=10).json()
                except Exception as e:
                    st.error(f"Error: {e}")
                    return

            batter_season = next((s for s in batter_career if s["season"] == season), None)
            pitcher_season = next((s for s in pitcher_career if s["season"] == season), None)

            col1, col2 = st.columns(2)
            with col1:
                batter_hs = HEADSHOT_URL.format(mlb_id=batter_id)
                st.markdown(f"""
                <div style="display:flex;align-items:flex-end;gap:1rem;margin-bottom:1rem;">
                    <img src="{batter_hs}" style="width:80px;border-bottom:3px solid #c0392b;" onerror="this.style.display='none'">
                    <div class="player-name">{batter_name}</div>
                </div>
                """, unsafe_allow_html=True)
                if batter_season:
                    stats = batter_season["stats"]
                    for key, label in [("avg","AVG"),("obp","OBP"),("slg","SLG"),("ops","OPS"),("homeRuns","HR"),("strikeOuts","K")]:
                        val = stats.get(key, "—")
                        st.markdown(f'<div class="stat-card"><div class="stat-label">{label} {season}</div><div class="stat-value">{val}</div></div>', unsafe_allow_html=True)

            with col2:
                pitcher_hs = HEADSHOT_URL.format(mlb_id=pitcher_id)
                st.markdown(f"""
                <div style="display:flex;align-items:flex-end;gap:1rem;margin-bottom:1rem;">
                    <img src="{pitcher_hs}" style="width:80px;border-bottom:3px solid #c0392b;" onerror="this.style.display='none'">
                    <div class="player-name">{pitcher_name}</div>
                </div>
                """, unsafe_allow_html=True)
                if pitcher_season:
                    stats = pitcher_season["stats"]
                    for key, label in [("era","ERA"),("whip","WHIP"),("strikeOuts","K"),("walksPer9Inn","BB/9"),("wins","W"),("inningsPitched","IP")]:
                        val = stats.get(key, "—")
                        st.markdown(f'<div class="stat-card"><div class="stat-label">{label} {season}</div><div class="stat-value">{val}</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">AI Matchup Analysis</div>', unsafe_allow_html=True)

            def fmt_hitting(s):
                if not s: return "No data"
                st2 = s["stats"]
                return f"AVG {st2.get('avg','?')} | OBP {st2.get('obp','?')} | SLG {st2.get('slg','?')} | OPS {st2.get('ops','?')} | HR {st2.get('homeRuns','?')} | K {st2.get('strikeOuts','?')}"

            def fmt_pitching(s):
                if not s: return "No data"
                st2 = s["stats"]
                return f"ERA {st2.get('era','?')} | WHIP {st2.get('whip','?')} | K {st2.get('strikeOuts','?')} | BB/9 {st2.get('walksPer9Inn','?')} | K/9 {st2.get('strikeoutsPer9Inn','?')}"

            load_dotenv()
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            batter_lines = "\n".join([f"  {s['season']}: {fmt_hitting(s)}" for s in batter_career[-4:]])
            pitcher_lines = "\n".join([f"  {s['season']}: {fmt_pitching(s)}" for s in pitcher_career[-4:]])

            prompt = f"""Analyze this MLB matchup between a batter and pitcher.

BATTER: {batter_name} ({batter_info.get('position')}, {batter_info.get('team')})
Bats: {batter_info.get('bats')} | Recent stats:
{batter_lines}

PITCHER: {pitcher_name} ({pitcher_info.get('position')}, {pitcher_info.get('team')})
Throws: {pitcher_info.get('throws')} | Recent stats:
{pitcher_lines}

Analyze:
1. **Matchup Advantage** — Who has the edge and why?
2. **Key Battle** — What's the critical factor in this matchup?
3. **Batter's Approach** — What should the batter be looking for?
4. **Pitcher's Strategy** — How should the pitcher attack this hitter?
5. **Historical Context** — Any relevant trends or patterns?
6. **Prediction** — In a 10 AB sample, what outcomes would you expect?

Be specific and reference the actual stats."""

            with st.spinner("Generating matchup analysis..."):
                resp = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
            st.markdown(f'<div class="report-body">{resp.content[0].text}</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="border: 1px dashed #222; padding: 3rem; text-align: center; margin-top: 2rem;">
            <div style="font-family: Bebas Neue, sans-serif; font-size: 1.5rem; color: #333; letter-spacing: 0.1em;">
                SEARCH FOR A BATTER AND PITCHER
            </div>
            <div style="font-family: IBM Plex Mono, monospace; font-size: 0.65rem; color: #444; margin-top: 0.5rem; letter-spacing: 0.15em;">
                GET AI-POWERED MATCHUP ANALYSIS BASED ON CAREER DATA
            </div>
        </div>
        """, unsafe_allow_html=True)
