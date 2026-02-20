from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.scout import ScoutingService
from app.models.schemas import ScoutingReportRequest

router = APIRouter(prefix="/scout", tags=["scout"])

@router.post("/{mlb_id}")
def generate_report(mlb_id: int, req: ScoutingReportRequest, db: Session = Depends(get_db)):
    svc = ScoutingService(db)
    report = svc.generate_report(
        mlb_id=mlb_id,
        season=req.season or 2024,
        question=req.question,
        force_regenerate=req.force_regenerate or False,
    )
    return {"mlb_id": mlb_id, "season": req.season, "report": report}

@router.get("/{mlb_id}")
def get_report(mlb_id: int, season: int = 2024, db: Session = Depends(get_db)):
    from app.db.models import ScoutingReport
    report = (
        db.query(ScoutingReport)
        .filter(ScoutingReport.mlb_id == mlb_id, ScoutingReport.season == season)
        .first()
    )
    if not report:
        return {"mlb_id": mlb_id, "season": season, "report": None}
    return {"mlb_id": mlb_id, "season": season, "report": report.report_text}
