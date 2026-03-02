from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Team(db.Model):
    __tablename__ = 'frc_teams'
    team_id = Column(Integer, primary_key=True)
    team_name = Column(String(100), nullable=False)

class Event(db.Model):
    __tablename__ = 'events'
    event_id = Column(Integer, primary_key=True)
    event_code = Column(String(10), nullable=False)
    event_name = Column(String(100), nullable=False)
    event_date = Column(String(20), nullable=False)
    event_year = Column(Integer, nullable=False)
    event_currently_active = Column(Boolean, nullable=False)

class MatchTeamData(db.Model):
    __tablename__ = 'match_team_data'
    record_id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'))
    match_number = Column(Integer)
    team_number = Column(Integer)
    auto_fuel_score = Column(Integer)
    auto_climb_try = Column(Boolean)
    auto_climbed = Column(Integer)
    auto_traveled = Column(String(50))
    teleop_fuel_score = Column(Integer)
    teleop_traveled = Column(String(50))
    endgame_climb_try = Column(Boolean)
    endgame_climb_level = Column(Integer)
    strategy_active_scored = Column(Boolean)
    strategy_active_ferrying = Column(Boolean)
    strategy_active_defense = Column(Boolean)
    strategy_inactive_scored = Column(Boolean)
    strategy_inactive_ferrying = Column(Boolean)
    strategy_inactive_defense = Column(Boolean)
    strategy_defense_actions = Column(Integer)
    match_fouls = Column(Integer)
    match_tipped = Column(Boolean)
    match_broken = Column(Boolean)
    match_beached = Column(Boolean)
    match_carded = Column(Boolean)
    match_disabled = Column(Boolean)
    match_absent = Column(Boolean)
    calc_auto_score = Column(Integer)
    calc_teleop_score = Column(Integer)
    record_ip_address = Column(String(20))
    record_hidden = Column(Boolean, default=False)

class MatchData(db.Model):
    __tablename__ = 'match_data'
    match_id = Column(Integer, primary_key=True)
    event_id = Column(Integer)
    match_type = Column(String(50))
    match_number = Column(Integer)
    red_1_id = Column(Integer, ForeignKey('frc_teams.team_id'))
    red_2_id = Column(Integer, ForeignKey('frc_teams.team_id'))
    red_3_id = Column(Integer, ForeignKey('frc_teams.team_id'))
    blue_1_id = Column(Integer, ForeignKey('frc_teams.team_id'))
    blue_2_id = Column(Integer, ForeignKey('frc_teams.team_id'))
    blue_3_id = Column(Integer, ForeignKey('frc_teams.team_id'))
    red_rp = Column(Integer)
    blue_rp = Column(Integer)
    red_auto_score = Column(Integer)
    red_teleop_score = Column(Integer)
    blue_auto_score = Column(Integer)
    blue_teleop_score = Column(Integer)
    red_1_auto_climb = Column(Integer)
    red_2_auto_climb = Column(Integer)
    red_3_auto_climb = Column(Integer)
    blue_1_auto_climb = Column(Integer)
    blue_2_auto_climb = Column(Integer)
    blue_3_auto_climb = Column(Integer)
    red_1_endgame_climb = Column(Integer)
    red_2_endgame_climb = Column(Integer)
    red_3_endgame_climb = Column(Integer)
    blue_1_endgame_climb = Column(Integer)
    blue_2_endgame_climb = Column(Integer)
    blue_3_endgame_climb = Column(Integer)

class Calculation(db.Model):
    __tablename__ = 'calculated_data'
    record_id = Column(Integer, primary_key=True)
    team_number = Column(Integer, ForeignKey('frc_teams.team_id'))
    event_id = Column(Integer)
    event_climb = Column(Integer)
    event_avg_score = Column(Integer)
    event_epa = Column(Integer)
    event_opr = Column(Integer)
    event_dpr = Column(Integer)
    event_ccwm = Column(Integer)