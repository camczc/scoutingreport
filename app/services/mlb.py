"""app/services/mlb.py - MLB Stats API data layer"""
import logging
import statsapi
from sqlalchemy.orm import Session
from app.db.models import Player, PlayerSeason

logger = logging.getLogger(__name__)

STAT_FIELDS_HITTING = [
    "gamesPlayed","atBats","runs","hits","doubles","triples","homeRuns",
    "rbi","stolenBases","caughtStealing","walks","strikeOuts","avg","obp",
    "slg","ops","leftOnBase","plateAppearances","sacBunts","sacFlies",
    "hitByPitch","groundOuts","airOuts","groundIntoDoublePlay",
]

STAT_FIELDS_PITCHING = [
    "gamesPlayed","gamesStarted","wins","losses","era","inningsPitched",
    "hits","runs","earnedRuns","homeRuns","walks","strikeOuts","whip",
    "strikeoutsPer9Inn","walksPer9Inn","hitsPer9Inn","avg","obp","slg","ops",
    "saves","saveOpportunities","holds","blownSaves","completeGames","shutouts",
    "qualityStarts","battersFaced","strikes","balls",
]


class MLBService:
    def __init__(self, db: Session):
        self.db = db

    def search_players(self, query: str) -> list:
        """Search MLB players by name."""
        try:
            results = statsapi.lookup_player(query)
            return [
                {
                    "mlb_id": p["id"],
                    "full_name": p["fullName"],
                    "position": p.get("primaryPosition", {}).get("abbreviation", ""),
                    "team": p.get("currentTeam", {}).get("name", ""),
                    "active": p.get("active", True),
                }
                for p in results
            ]
        except Exception as e:
            logger.error(f"Player search failed: {e}")
            return []

    def get_or_fetch_player(self, mlb_id: int) -> Player:
        """Get player from DB or fetch from MLB API."""
        player = self.db.query(Player).filter(Player.mlb_id == mlb_id).first()
        if player:
            return player

        try:
            data = statsapi.get("person", {"personId": mlb_id})
            p = data["people"][0]
            player = Player(
                mlb_id=mlb_id,
                full_name=p.get("fullName", ""),
                first_name=p.get("firstName", ""),
                last_name=p.get("lastName", ""),
                position=p.get("primaryPosition", {}).get("abbreviation", ""),
                team=p.get("currentTeam", {}).get("name", ""),
                team_id=p.get("currentTeam", {}).get("id"),
                bats=p.get("batSide", {}).get("code", ""),
                throws=p.get("pitchHand", {}).get("code", ""),
                birth_date=p.get("birthDate", ""),
                birth_city=p.get("birthCity", ""),
                birth_country=p.get("birthCountry", ""),
                height=p.get("height", ""),
                weight=p.get("weight"),
                debut=p.get("mlbDebutDate", ""),
                active="Y" if p.get("active") else "N",
            )
            self.db.add(player)
            self.db.commit()
            self.db.refresh(player)
            return player
        except Exception as e:
            logger.error(f"Failed to fetch player {mlb_id}: {e}")
            raise

    def get_hitting_stats(self, mlb_id: int, seasons: list[int]) -> list[dict]:
        """Get hitting stats for multiple seasons."""
        results = []
        for season in seasons:
            cached = self.db.query(PlayerSeason).filter(
                PlayerSeason.mlb_id == mlb_id,
                PlayerSeason.season == season,
                PlayerSeason.stat_group == "hitting"
            ).first()
            if cached:
                results.append({"season": season, "stats": cached.stats, "team": cached.team})
                continue
            try:
                data = statsapi.player_stat_data(mlb_id, group="hitting", type="season", sportId=1)
                for s in data.get("stats", []):
                    if s.get("season") == str(season):
                        stats = {k: s.get(k) for k in STAT_FIELDS_HITTING if k in s}
                        team = s.get("team", {}).get("name", "") if isinstance(s.get("team"), dict) else ""
                        row = PlayerSeason(
                            mlb_id=mlb_id, season=season, team=team,
                            stat_group="hitting", stats=stats
                        )
                        try:
                            self.db.merge(row)
                            self.db.commit()
                        except Exception:
                            self.db.rollback()
                        results.append({"season": season, "stats": stats, "team": team})
                        break
            except Exception as e:
                logger.warning(f"No hitting stats for {mlb_id} season {season}: {e}")
        return results

    def get_pitching_stats(self, mlb_id: int, seasons: list[int]) -> list[dict]:
        """Get pitching stats for multiple seasons."""
        results = []
        for season in seasons:
            cached = self.db.query(PlayerSeason).filter(
                PlayerSeason.mlb_id == mlb_id,
                PlayerSeason.season == season,
                PlayerSeason.stat_group == "pitching"
            ).first()
            if cached:
                results.append({"season": season, "stats": cached.stats, "team": cached.team})
                continue
            try:
                data = statsapi.player_stat_data(mlb_id, group="pitching", type="season", sportId=1)
                for s in data.get("stats", []):
                    if s.get("season") == str(season):
                        stats = {k: s.get(k) for k in STAT_FIELDS_PITCHING if k in s}
                        team = s.get("team", {}).get("name", "") if isinstance(s.get("team"), dict) else ""
                        row = PlayerSeason(
                            mlb_id=mlb_id, season=season, team=team,
                            stat_group="pitching", stats=stats
                        )
                        try:
                            self.db.merge(row)
                            self.db.commit()
                        except Exception:
                            self.db.rollback()
                        results.append({"season": season, "stats": stats, "team": team})
                        break
            except Exception as e:
                logger.warning(f"No pitching stats for {mlb_id} season {season}: {e}")
        return results

    def get_career_stats(self, mlb_id: int, stat_group: str = "hitting") -> list[dict]:
        """Get full career stats across all seasons."""
        try:
            data = statsapi.player_stat_data(mlb_id, group=stat_group, type="yearByYear", sportId=1)
            results = []
            for s in data.get("stats", []):
                season = s.get("season")
                if not season:
                    continue
                fields = STAT_FIELDS_HITTING if stat_group == "hitting" else STAT_FIELDS_PITCHING
                stat_data = s.get("stats", s)
                stats = {k: stat_data.get(k) for k in fields if k in stat_data}
                team = s.get("team", {}).get("name", "") if isinstance(s.get("team"), dict) else ""
                results.append({"season": int(season), "stats": stats, "team": team})
            return sorted(results, key=lambda x: x["season"])
        except Exception as e:
            logger.error(f"Career stats failed for {mlb_id}: {e}")
            return []

    def get_game_log(self, mlb_id: int, season: int, stat_group: str = "hitting") -> list[dict]:
        """Get game-by-game log for a season."""
        try:
            data = statsapi.player_stat_data(mlb_id, group=stat_group, type="gameLog", sportId=1)
            results = []
            for s in data.get("stats", []):
                if s.get("season") != str(season):
                    continue
                game = {
                    "date": s.get("date", ""),
                    "opponent": s.get("opponent", {}).get("name", "") if isinstance(s.get("opponent"), dict) else "",
                    "home_away": s.get("isHome", True),
                }
                fields = STAT_FIELDS_HITTING if stat_group == "hitting" else STAT_FIELDS_PITCHING
                game.update({k: s.get(k) for k in fields if k in s})
                results.append(game)
            return results
        except Exception as e:
            logger.warning(f"Game log failed: {e}")
            return []
