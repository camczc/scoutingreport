"""app/api/games.py - Today's games, pitcher heatmaps, vs-team stats"""
import logging
import statsapi
import requests
import io
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db
from app.services.mlb import MLBService

router = APIRouter()
logger = logging.getLogger(__name__)

SAVANT_BASE = "https://baseballsavant.mlb.com/statcast_search/csv"


@router.get("/today")
def get_today_games():
    """Get today's MLB schedule with probable pitcher IDs."""
    try:
        today = "2025-09-19"
        r = requests.get(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={"date": today, "sportId": 1, "hydrate": "probablePitcher"},
            timeout=10
        )
        data = r.json()
        results = []
        for date in data.get("dates", []):
            for game in date.get("games", []):
                away = game["teams"]["away"]
                home = game["teams"]["home"]
                away_pitcher = away.get("probablePitcher", {})
                home_pitcher = home.get("probablePitcher", {})
                results.append({
                    "game_id": game.get("gamePk"),
                    "game_datetime": game.get("gameDate"),
                    "game_type": game.get("gameType"),
                    "status": game.get("status", {}).get("detailedState"),
                    "venue_name": game.get("venue", {}).get("name", ""),
                    "away_name": away.get("team", {}).get("name", ""),
                    "away_id": away.get("team", {}).get("id"),
                    "home_name": home.get("team", {}).get("name", ""),
                    "home_id": home.get("team", {}).get("id"),
                    "away_probable_pitcher": away_pitcher.get("fullName", ""),
                    "away_pitcher_id": away_pitcher.get("id"),
                    "home_probable_pitcher": home_pitcher.get("fullName", ""),
                    "home_pitcher_id": home_pitcher.get("id"),
                })
        return results
    except Exception as e:
        logger.error(f"Schedule fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pitcher-heatmap/{mlb_id}")
def get_pitcher_heatmap(mlb_id: int, season: int = 2024):
    """Fetch pitcher's pitch location data from MLB game feeds."""
    try:
        # Get team ID for this pitcher
        player_data = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{mlb_id}",
            params={"hydrate": "currentTeam"},
            timeout=10
        ).json()
        team_id = player_data.get("people", [{}])[0].get("currentTeam", {}).get("id")
        if not team_id:
            return {"pitches": [], "total_pitches": 0}

        # Get team's games for the season
        sched = requests.get(
            "https://statsapi.mlb.com/api/v1/schedule",
            params={
                "teamId": team_id,
                "startDate": f"{season}-04-01",
                "endDate": f"{season}-10-15",
                "sportId": 1,
                "gameType": "R"
            },
            timeout=10
        ).json()

        game_pks = []
        for date in sched.get("dates", []):
            for game in date.get("games", []):
                game_pks.append(game.get("gamePk"))

        # Sample up to 12 games spread across the season
        if len(game_pks) > 12:
            step = len(game_pks) // 12
            game_pks = game_pks[::step][:12]

        pitches = []
        for gp in game_pks:
            try:
                game_data = statsapi.get("game", {"gamePk": gp})
                plays = game_data.get("liveData", {}).get("plays", {}).get("allPlays", [])
                for play in plays:
                    pitcher_id = play.get("matchup", {}).get("pitcher", {}).get("id")
                    if pitcher_id != mlb_id:
                        continue
                    for event in play.get("playEvents", []):
                        if not event.get("isPitch"):
                            continue
                        pd = event.get("pitchData", {})
                        coords = pd.get("coordinates", {})
                        px = coords.get("pX")
                        pz = coords.get("pZ")
                        if px is None or pz is None:
                            continue
                        pitches.append({
                            "plate_x": px,
                            "plate_z": pz,
                            "pitch_name": event.get("details", {}).get("type", {}).get("description", ""),
                            "start_speed": pd.get("startSpeed"),
                            "zone": pd.get("zone"),
                            "description": event.get("details", {}).get("description", ""),
                        })
            except Exception as ge:
                logger.warning(f"Game {gp} failed: {ge}")
                continue

        return {"pitches": pitches, "total_pitches": len(pitches)}

    except Exception as e:
        logger.error(f"Heatmap failed for {mlb_id}: {e}")
        return {"pitches": [], "total_pitches": 0, "error": str(e)}


@router.get("/pitcher-vs-team/{pitcher_id}/{team_id}")
def get_pitcher_vs_team(pitcher_id: int, team_id: int, db: Session = Depends(get_db)):
    """Get pitcher's career stats vs each batter on a team's roster."""
    try:
        # Get active roster
        roster_data = statsapi.get("team_roster", {"teamId": team_id, "rosterType": "active"})
        roster = roster_data.get("roster", [])

        results = []
        for player in roster:
            pid = player.get("person", {}).get("id")
            pname = player.get("person", {}).get("fullName", "")
            pos = player.get("position", {}).get("abbreviation", "")

            if pos in ["SP", "RP", "P", "CL"]:
                continue

            try:
                r = requests.get(
                    f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats",
                    params={
                        "stats": "vsPlayerTotal",
                        "opposingPlayerId": pid,
                        "group": "pitching",
                        "sportId": 1,
                    },
                    timeout=10
                )
                data = r.json()
                splits = []
                for stat_group in data.get("stats", []):
                    if stat_group.get("type", {}).get("displayName") == "vsPlayerTotal":
                        splits = stat_group.get("splits", [])
                        break

                if not splits:
                    continue

                s = splits[0].get("stat", {})
                ab = s.get("atBats", 0)
                if ab < 3:
                    continue

                results.append({
                    "mlb_id": pid,
                    "full_name": pname,
                    "position": pos,
                    "atBats": ab,
                    "hits": s.get("hits", 0),
                    "homeRuns": s.get("homeRuns", 0),
                    "walks": s.get("baseOnBalls", 0),
                    "strikeOuts": s.get("strikeOuts", 0),
                    "avg": s.get("avg", ".000"),
                    "obp": s.get("obp", ".000"),
                    "slg": s.get("slg", ".000"),
                    "ops": s.get("ops", ".000"),
                    "numberOfPitches": s.get("numberOfPitches", 0),
                })
            except Exception as inner_e:
                logger.warning(f"Could not get {pname} vs pitcher {pitcher_id}: {inner_e}")
                continue

        return sorted(results, key=lambda x: x["atBats"], reverse=True)

    except Exception as e:
        logger.error(f"Pitcher vs team failed: {e}")
        return []
