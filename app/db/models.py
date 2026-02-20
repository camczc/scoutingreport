"""app/db/models.py"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON, UniqueConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = "sr_players"
    id = Column(Integer, primary_key=True)
    mlb_id = Column(Integer, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    position = Column(String)
    team = Column(String)
    team_id = Column(Integer)
    bats = Column(String)
    throws = Column(String)
    birth_date = Column(String)
    birth_city = Column(String)
    birth_country = Column(String)
    height = Column(String)
    weight = Column(Integer)
    debut = Column(String)
    active = Column(String, default="Y")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PlayerSeason(Base):
    __tablename__ = "sr_player_seasons"
    id = Column(Integer, primary_key=True)
    mlb_id = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    team = Column(String)
    stat_group = Column(String)  # hitting, pitching, fielding
    stats = Column(JSON)
    __table_args__ = (UniqueConstraint("mlb_id", "season", "team", "stat_group"),)

class ScoutingReport(Base):
    __tablename__ = "sr_scouting_reports"
    id = Column(Integer, primary_key=True)
    mlb_id = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    report = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("mlb_id", "season"),)
