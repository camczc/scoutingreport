"""app/api/players.py"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.mlb import MLBService
from app.services.scout import ScoutService

router = APIRouter()

@router.get("/search")
def search_players(q: str, db: Session = Depends(get_db)):
    svc = MLBService(db)
    return svc.search_players(q)

@router.get("/{mlb_id}")
def get_player(mlb_id: int, db: Session = Depends(get_db)):
    svc = MLBService(db)
    try:
        player = svc.get_or_fetch_player(mlb_id)
        return {
            "mlb_id": player.mlb_id,
            "full_name": player.full_name,
            "position": player.position,
            "team": player.team,
            "bats": player.bats,
            "throws": player.throws,
            "birth_date": player.birth_date,
            "height": player.height,
            "weight": player.weight,
            "debut": player.debut,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{mlb_id}/stats/career")
def get_career_stats(mlb_id: int, group: str = "hitting", db: Session = Depends(get_db)):
    svc = MLBService(db)
    svc.get_or_fetch_player(mlb_id)
    return svc.get_career_stats(mlb_id, group)

@router.get("/{mlb_id}/stats/season")
def get_season_stats(mlb_id: int, season: int = 2024, group: str = "hitting", db: Session = Depends(get_db)):
    svc = MLBService(db)
    svc.get_or_fetch_player(mlb_id)
    if group == "pitching":
        return svc.get_pitching_stats(mlb_id, [season])
    return svc.get_hitting_stats(mlb_id, [season])

@router.get("/{mlb_id}/report")
def get_report(mlb_id: int, season: int = 2024, question: str = None, db: Session = Depends(get_db)):
    mlb_svc = MLBService(db)
    scout_svc = ScoutService(db)
    player = mlb_svc.get_or_fetch_player(mlb_id)
    player_dict = {
        "mlb_id": player.mlb_id,
        "full_name": player.full_name,
        "position": player.position,
        "team": player.team,
        "bats": player.bats,
        "throws": player.throws,
        "height": player.height,
        "weight": player.weight,
        "debut": player.debut,
    }
    stat_group = "pitching" if player.position in ["SP", "RP", "P", "CL"] else "hitting"
    career = mlb_svc.get_career_stats(mlb_id, stat_group)
    report = scout_svc.generate_report(player_dict, career, stat_group, season, question)
    return {"report": report, "stat_group": stat_group}
