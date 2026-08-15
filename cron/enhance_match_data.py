import os
import sys
import base64
import requests
from flask import Flask

# Ensure project root is on sys.path so `database_model` can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from database_model import db, Event, MatchData, MatchTeamData

# Create a minimal Flask app for database access
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    'SQLALCHEMY_DB_URI', f"sqlite:///{os.path.join(ROOT_DIR, 'instance', 'scouting.db')}")
db.init_app(app)

def request_match_data(event_code: str, match_number: int):
    # query MatchData for team climb results for a given match_number and event_id
    with app.app_context():
        event_id = db.session\
            .query(Event.event_id)\
            .filter(Event.event_code == event_code)\
            .scalar()
        match_climbs = db.session\
            .query(
                MatchData.red_1_id,
                MatchData.red_2_id,
                MatchData.red_3_id,
                MatchData.blue_1_id,
                MatchData.blue_2_id,
                MatchData.blue_3_id,
                # MatchData.red_rp,
                # MatchData.blue_rp,
                MatchData.red_1_auto_climb,
                MatchData.red_2_auto_climb,
                MatchData.red_3_auto_climb,
                MatchData.blue_1_auto_climb,
                MatchData.blue_2_auto_climb,
                MatchData.blue_3_auto_climb,
                MatchData.red_1_endgame_climb,
                MatchData.red_2_endgame_climb,
                MatchData.red_3_endgame_climb,
                MatchData.blue_1_endgame_climb,
                MatchData.blue_2_endgame_climb,
                MatchData.blue_3_endgame_climb)\
            .filter(
                MatchData.event_id == event_id,
                MatchData.match_number == match_number)\
            .first()
        if match_climbs is None:
            print(f'! Match number {match_number} not found for event {event_code}')
            auto_climb_dict = None
            endgame_climb_dict = None
        else:
            auto_climb_dict = {
                match_climbs.red_1_id: match_climbs.red_1_auto_climb,
                match_climbs.red_2_id: match_climbs.red_2_auto_climb,
                match_climbs.red_3_id: match_climbs.red_3_auto_climb,
                match_climbs.blue_1_id: match_climbs.blue_1_auto_climb,
                match_climbs.blue_2_id: match_climbs.blue_2_auto_climb,
                match_climbs.blue_3_id: match_climbs.blue_3_auto_climb,
            }
            endgame_climb_dict = {
                match_climbs.red_1_id: match_climbs.red_1_endgame_climb,
                match_climbs.red_2_id: match_climbs.red_2_endgame_climb,
                match_climbs.red_3_id: match_climbs.red_3_endgame_climb,
                match_climbs.blue_1_id: match_climbs.blue_1_endgame_climb,
                match_climbs.blue_2_id: match_climbs.blue_2_endgame_climb,
                match_climbs.blue_3_id: match_climbs.blue_3_endgame_climb,
            }
        # TODO: include in MatchTeamData?
        # team_rp_dict = {
        #     match_climbs.red_1_id: match_climbs.red_rp,
        #     match_climbs.red_2_id: match_climbs.red_rp,
        #     match_climbs.red_3_id: match_climbs.red_rp,
        #     match_climbs.blue_1_id: match_climbs.blue_rp,
        #     match_climbs.blue_2_id: match_climbs.blue_rp,
        #     match_climbs.blue_3_id: match_climbs.blue_rp,
        # }
        
        return auto_climb_dict, endgame_climb_dict

def find_team_records_needing_climb_data(event_code: str):
    with app.app_context():
        event_id = db.session\
            .query(Event.event_id)\
            .filter(Event.event_code == event_code)\
            .scalar()
        team_match_needs_enhancing = db.session\
            .query(
                MatchTeamData.match_number,
                MatchTeamData.team_number)\
            .filter(
                MatchTeamData.auto_climbed == None,
                MatchTeamData.event_id == event_id)\
            .all()
        print(team_match_needs_enhancing)
        for match_number, team_number in team_match_needs_enhancing:
            print(match_number, team_number)
            auto_climb_dict, endgame_climb_dict = request_match_data(event_code, match_number)
            if not team_number in auto_climb_dict or not auto_climb_dict or not endgame_climb_dict:
                print(f'No climb data found for team {team_number} in match {match_number}, validate match data is correct and complete.')
            else:
                climb_result = auto_climb_dict[team_number]
                endgame_climb_result = endgame_climb_dict[team_number]
                print(f'Updating MatchTeamData for match {match_number} and team {team_number} with climb result {climb_result} and endgame climb result {endgame_climb_result}')
                db.session.query(MatchTeamData)\
                    .filter(
                        MatchTeamData.event_id == event_id,
                        MatchTeamData.match_number == match_number,
                        MatchTeamData.team_number == team_number)\
                    .update({
                        MatchTeamData.auto_climbed: climb_result,
                        MatchTeamData.endgame_climb_level: endgame_climb_result
                    })
        db.session.commit()

if __name__ == "__main__":
    find_team_records_needing_climb_data(event_code='WEEK0')
    request_match_data(event_code='WEEK0', match_number=1)