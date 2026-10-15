"""Database schema. All SQLAlchemy table definitions live here."""
from sqlalchemy import Boolean, Column, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    player_id = Column(String(64), primary_key=True)
    name = Column(String(80), nullable=False)
    team_type = Column(String(12), nullable=False)
    registered_date = Column(String(10), nullable=False)
    team_id = Column(String(64), nullable=False, default="legacy")
    __table_args__ = (Index("uq_players_team_name_ci", team_id, func.lower(name), unique=True),)

class TrainingSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String(64), nullable=False, index=True)
    date = Column(String(10), nullable=False)
    duration_minutes = Column(Float, nullable=False)
    rpe = Column(Float, nullable=False)

class Checkin(Base):
    __tablename__ = "checkins"
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String(64), nullable=False, index=True)
    date = Column(String(10), nullable=False)
    sleep = Column(Integer, nullable=False)
    energy = Column(Integer, nullable=False)
    soreness = Column(Integer, nullable=False)
    stress = Column(Integer, nullable=False)
    pain = Column(Boolean, nullable=False)
    pain_area = Column(Text, nullable=True)


class CheckinLink(Base):
    __tablename__ = "checkin_links"
    token = Column(String(64), primary_key=True)
    player_id = Column(String(64), nullable=False, unique=True, index=True)


class Coach(Base):
    __tablename__ = "coaches"
    google_sub = Column(String(255), primary_key=True)
    email = Column(String(320), nullable=False, unique=True)
    display_name = Column(String(160), nullable=False)
    adult_confirmed_at = Column(String(40), nullable=True)
    authorization_confirmed_at = Column(String(40), nullable=True)

class Team(Base):
    __tablename__ = "teams"
    team_id = Column(String(64), primary_key=True)
    coach_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    team_type = Column(String(12), nullable=False)
    terms_accepted_at = Column(String(40), nullable=False)


class OpenTeamSession(Base):
    __tablename__ = "open_team_sessions"
    session_id = Column(String(64), primary_key=True)
    team_id = Column(String(64), nullable=False, index=True)
    date = Column(String(10), nullable=False)
    duration_minutes = Column(Float, nullable=False)
    is_open = Column(Boolean, nullable=False, default=True)
