"""app/models/schemas.py"""
from pydantic import BaseModel
from typing import Optional

class PlayerSearchResult(BaseModel):
    mlb_id: int
    full_name: str
    position: str
    team: str
    active: bool

class ReportRequest(BaseModel):
    mlb_id: int
    season: int = 2024
    question: Optional[str] = None
