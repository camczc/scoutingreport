"""frontend/views/search.py"""
import streamlit as st
import requests

API_BASE = "http://localhost:8000"
HEADSHOT_URL = "https://img.mlbstatic.com/mlb-photos/image/upload/v1/people/{mlb_id}/headshot/67/current"

def render():
    st.markdown('<div class="logo-header">Player Search</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">MLB Stats Database — All Active & Historical Players</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search", placeholder="Search by name — e.g. Aaron Judge, Shohei Ohtani, Sandy Koufax...", label_visibility="collapsed")
    with col2:
        search = st.button("Search", use_container_width=True)

    if query and (search or query):
        with st.spinner("Searching..."):
            try:
                resp = requests.get(f"{API_BASE}/players/search", params={"q": query}, timeout=10)
                results = resp.json()
            except Exception as e:
                st.error(f"API error: {e}")
                return

        if not results:
            st.warning("No players found.")
            return

        st.markdown(f'<div class="section-header">{len(results)} Results</div>', unsafe_allow_html=True)

        for p in results[:20]:
            col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
            with col1:
                st.markdown(f'<div style="font-family: Bebas Neue, sans-serif; font-size: 1.3rem; color: #e8e0d0; letter-spacing: 0.05em;">{p["full_name"]}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div style="font-family: IBM Plex Mono, monospace; font-size: 0.75rem; color: #c0392b; padding-top: 0.3rem;">{p["position"]}</div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div style="font-family: IBM Plex Mono, monospace; font-size: 0.75rem; color: #888; padding-top: 0.3rem;">{p["team"] or "Free Agent"}</div>', unsafe_allow_html=True)
            with col4:
                if st.button("View", key=f"view_{p['mlb_id']}"):
                    st.session_state["selected_player_id"] = p["mlb_id"]
                    st.session_state["selected_player_name"] = p["full_name"]
                    st.session_state["page"] = "stats"
                    st.rerun()
            st.markdown('<hr style="margin: 0.4rem 0; border-color: #1a1a1a;">', unsafe_allow_html=True)
    else:
        # Featured players
        st.markdown('<div class="section-header">Featured Players</div>', unsafe_allow_html=True)
        featured = [
            ("Aaron Judge", 592450), ("Shohei Ohtani", 660271), ("Mookie Betts", 605141),
            ("Freddie Freeman", 518692), ("Ronald Acuña Jr.", 660670), ("Juan Soto", 665742),
            ("Gerrit Cole", 543037), ("Spencer Strider", 675911), ("Zack Wheeler", 554430),
            ("Fernando Tatis Jr.", 665487), ("Corbin Carroll", 682998), ("Gunnar Henderson", 683002),
        ]
        cols = st.columns(4)
        for i, (name, mlb_id) in enumerate(featured):
            with cols[i % 4]:
                headshot_url = HEADSHOT_URL.format(mlb_id=mlb_id)
                st.markdown(f"""
                <div class="stat-card" style="cursor:pointer; min-height: 80px; display:flex; align-items:center; gap:0.75rem; padding:0.75rem 1rem;">
                    <img src="{headshot_url}" style="width:50px;height:60px;object-fit:cover;object-position:center 15%;border-bottom:2px solid #c0392b;flex-shrink:0;"
                         onerror="this.style.display='none'">
                    <div>
                        <div class="stat-label">MLB ID {mlb_id}</div>
                        <div style="font-family: Bebas Neue, sans-serif; font-size: 1.1rem; color: #e8e0d0; line-height: 1.2;">{name}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Select", key=f"feat_{mlb_id}"):
                    st.session_state["selected_player_id"] = mlb_id
                    st.session_state["selected_player_name"] = name
                    st.session_state["page"] = "stats"
                    st.rerun()
