"""app/services/scout.py - Claude-powered scouting reports"""
import logging
from anthropic import Anthropic
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import ScoutingReport

logger = logging.getLogger(__name__)
client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _format_hitting(stats: dict) -> str:
    lines = []
    if stats.get("avg"): lines.append(f"AVG: {stats['avg']}")
    if stats.get("obp"): lines.append(f"OBP: {stats['obp']}")
    if stats.get("slg"): lines.append(f"SLG: {stats['slg']}")
    if stats.get("ops"): lines.append(f"OPS: {stats['ops']}")
    if stats.get("homeRuns") is not None: lines.append(f"HR: {stats['homeRuns']}")
    if stats.get("rbi") is not None: lines.append(f"RBI: {stats['rbi']}")
    if stats.get("runs") is not None: lines.append(f"R: {stats['runs']}")
    if stats.get("hits") is not None: lines.append(f"H: {stats['hits']}")
    if stats.get("stolenBases") is not None: lines.append(f"SB: {stats['stolenBases']}")
    if stats.get("strikeOuts") is not None: lines.append(f"K: {stats['strikeOuts']}")
    if stats.get("walks") is not None: lines.append(f"BB: {stats['walks']}")
    if stats.get("gamesPlayed") is not None: lines.append(f"G: {stats['gamesPlayed']}")
    return " | ".join(lines)


def _format_pitching(stats: dict) -> str:
    lines = []
    if stats.get("era"): lines.append(f"ERA: {stats['era']}")
    if stats.get("whip"): lines.append(f"WHIP: {stats['whip']}")
    if stats.get("wins") is not None: lines.append(f"W: {stats['wins']}")
    if stats.get("losses") is not None: lines.append(f"L: {stats['losses']}")
    if stats.get("saves") is not None: lines.append(f"SV: {stats['saves']}")
    if stats.get("strikeOuts") is not None: lines.append(f"K: {stats['strikeOuts']}")
    if stats.get("inningsPitched"): lines.append(f"IP: {stats['inningsPitched']}")
    if stats.get("strikeoutsPer9Inn"): lines.append(f"K/9: {stats['strikeoutsPer9Inn']}")
    if stats.get("walksPer9Inn"): lines.append(f"BB/9: {stats['walksPer9Inn']}")
    if stats.get("gamesStarted") is not None: lines.append(f"GS: {stats['gamesStarted']}")
    return " | ".join(lines)


class ScoutService:
    def __init__(self, db: Session):
        self.db = db

    def generate_report(
        self,
        player: dict,
        career_stats: list,
        stat_group: str,
        season: int,
        question: str = None,
    ) -> str:
        # Check cache
        cached = self.db.query(ScoutingReport).filter(
            ScoutingReport.mlb_id == player["mlb_id"],
            ScoutingReport.season == season,
        ).first()
        if cached and not question:
            return cached.report

        # Build stat lines
        recent = [s for s in career_stats if s["season"] >= season - 4]
        stat_lines = []
        for s in recent:
            formatted = _format_pitching(s["stats"]) if stat_group == "pitching" else _format_hitting(s["stats"])
            stat_lines.append(f"  {s['season']} ({s.get('team','')}) — {formatted}")

        prompt = f"""You are a professional MLB scout writing a detailed scouting report.

PLAYER: {player['full_name']}
POSITION: {player.get('position', 'Unknown')}
TEAM: {player.get('team', 'Unknown')}
BATS/THROWS: {player.get('bats', '?')}/{player.get('throws', '?')}
HEIGHT/WEIGHT: {player.get('height', '?')} / {player.get('weight', '?')} lbs
MLB DEBUT: {player.get('debut', 'Unknown')}

RECENT STATS ({stat_group.upper()}):
{chr(10).join(stat_lines) if stat_lines else 'No stats available'}

{"USER QUESTION: " + question if question else ""}

Write a professional scouting report with these sections:

## Overview
2-3 sentences on who this player is and their role.

## Strengths
3 specific, data-backed strengths.

## Weaknesses / Areas of Concern
2-3 honest weaknesses or red flags.

## Statistical Trends
Analysis of how their numbers have trended over recent seasons.

## Role & Value
What role do they fill? Starting caliber, platoon, depth? Contract value assessment.

## Comparable Players
2 comps — one current player, one historical.

## Bottom Line
One paragraph summary. Would you sign this player? What's a fair contract?

Be specific, analytical, and honest. Reference the actual stats. Avoid generic platitudes."""

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        report = response.content[0].text

        # Cache if no custom question
        if not question:
            existing = self.db.query(ScoutingReport).filter(
                ScoutingReport.mlb_id == player["mlb_id"],
                ScoutingReport.season == season,
            ).first()
            if existing:
                existing.report = report
            else:
                self.db.add(ScoutingReport(
                    mlb_id=player["mlb_id"],
                    season=season,
                    report=report,
                ))
            self.db.commit()

        return report
