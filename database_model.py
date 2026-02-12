from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Team(db.Model):
    __tablename__ = 'frc_teams'
    team_id = Column(Integer, primary_key=True)
    team_name = Column(String(100), nullable=False)

    @classmethod
    def from_integer(cls, integer_value):
        return cls(is_active=bool(integer_value))

class MatchTeamData(db.Model):
    __tablename__ = 'match_data'
    record_id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('event_match.match_id'))
    team_number = Column(Integer, ForeignKey('frc_teams.team_id'))
    auto_fuel_score = Column(Integer)
    auto_climb_try = Column(Boolean)
    auto_climbed = Column(Integer)
    auto_traveled = Column(Boolean)
    teleop_fuel_score = Column(Integer)
    teleop_traveled = Column(String(50))
    teleop_climb_try = Column(Boolean)
    teleop_climb_level = Column(Integer)
    match_fouls = Column(Integer)
    match_card = Column(String(10))
    match_tipped = Column(Boolean)
    match_broke = Column(Boolean)
    match_disabled = Column(Boolean)
    match_absent = Column(Integer)
    calc_auto_score = Column(Integer)
    calc_teleop_score = Column(Integer)

class MatchAllianceData(db.Model):
    __tablename__ = 'event_match'
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


# Utility function to convert integers to booleans
def convert_int_to_bool(record_dict):
    # Convert specific keys from integer to boolean
    for key, value in record_dict.items():
        if isinstance(value, int):
            record_dict[key] = bool(value)
    return record_dict