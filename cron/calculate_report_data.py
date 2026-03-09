import os
import sys
from flask import Flask

# Ensure project root is on sys.path so `database_model` can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from database_model import db, Event, MatchData, MatchTeamData, Calculation

# Create a minimal Flask app for database access
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('SQLALCHEMY_DB_URI', 'sqlite:///scouting.db')
db.init_app(app)

def do_some_math():
    with app.app_context():
        event_id = db.session\
            .query(Event.event_id)\
            .filter(Event.event_currently_active == True)\
            .scalar()
        event_team_list = db.session\
            .query(MatchTeamData.team_number)\
            .filter(MatchTeamData.event_id == event_id)\
            .distinct()\
            .all()
        teams_to_update = db.session\
            .query(Calculation.team_number)\
            .filter(Calculation.event_id == event_id)\
            .all()
        teams_to_add = set(team[0] for team in event_team_list) - set(team[0] for team in teams_to_update)
        print(f'Teams to add calculations for: {teams_to_add}')

        for team_number in teams_to_add:
            print(f"Inserting row for team {team_number}")
            new_calculation = Calculation(
                event_id=event_id,
                team_number=team_number
            )
            db.session.add(new_calculation)
        db.session.commit()

        for team_number in event_team_list:
            print(f'Calculating data for team {team_number[0]}')
            # do some math here to calculate average climb level and success rate for the team
            team_climbs = db.session\
                .query(
                    MatchTeamData.team_number,
                    MatchTeamData.auto_climb_try,
                    MatchTeamData.auto_climbed,
                    MatchTeamData.endgame_climb_try,
                    MatchTeamData.endgame_climb_level)\
                .filter(MatchTeamData.event_id == event_id)\
                .all()
            team_climb_stats = {}
            for match in team_climbs:
                team_num = match.team_number
                if team_num in team_climb_stats:
                    team_climb_stats[team_num]['match_count'] += 1
                    prev_auto_climb_try = team_climb_stats[team_num]['auto_climb_try']
                    prev_auto_climbed = team_climb_stats[team_num]['auto_climbed']
                    prev_endgame_climb_try = team_climb_stats[team_num]['endgame_climb_try']
                    prev_endgame_climb_level = team_climb_stats[team_num]['endgame_climb_level']
                    if match.auto_climb_try is not None:
                        team_climb_stats[team_num]['auto_climb_try'] = prev_auto_climb_try + 1
                    if match.auto_climbed is not None:
                        team_climb_stats[team_num]['auto_climbed'] = prev_auto_climbed + 1
                    if match.endgame_climb_try is not None:
                        team_climb_stats[team_num]['endgame_climb_try'] = prev_endgame_climb_try + 1
                    if match.endgame_climb_level is not None:
                        team_climb_stats[team_num]['endgame_climb_level'] = prev_endgame_climb_level + 1
                else:
                    team_climb_stats[team_num] = {
                        'match_count': 0,
                        'auto_climb_try': 0,
                        'auto_climbed': 0,
                        'endgame_climb_try': 0,
                        'endgame_climbed': 0
                    }
                    team_climb_stats[team_num]['match_count'] = 1
                    if match.auto_climb_try is not None:
                        team_climb_stats[team_num]['auto_climb_try'] = prev_auto_climb_try + 1
                    if match.auto_climbed is not None:
                        team_climb_stats[team_num]['auto_climbed'] = prev_auto_climbed + 1
                    if match.endgame_climb_try is not None:
                        team_climb_stats[team_num]['endgame_climb_try'] = prev_endgame_climb_try + 1
                    if match.endgame_climb_level is not None:
                        team_climb_stats[team_num]['endgame_climbed'] = prev_endgame_climb_level + 1
            for team_num in team_climb_stats:
                if team_climb_stats[team_num]['auto_climb_try'] > 0:
                    team_climb_stats[team_num]['auto_climb_success'] = team_climb_stats[team_num]['auto_climbed'] / team_climb_stats[team_num]['auto_climb_try']
                else:
                    team_climb_stats[team_num]['auto_climb_success'] = None

                if team_climb_stats[team_num]['endgame_climb_try'] > 0:
                    team_climb_stats[team_num]['endgame_climb_success'] = team_climb_stats[team_num]['endgame_climbed'] / team_climb_stats[team_num]['endgame_climb_try']
                else:
                    team_climb_stats[team_num]['endgame_climb_success'] = None


            avg_climb_level = db.session.query(db.func.avg(MatchTeamData.endgame_climb_level))\
                .filter(MatchTeamData.event_id == event_id, MatchTeamData.team_number == team_number[0])\
                .scalar()
            db.session.query(Calculation)\
                .filter(Calculation.event_id == event_id, Calculation.team_number == team_number[0])\
                .update({Calculation.event_climb: avg_climb_level})
        db.session.commit()

if __name__ == "__main__":
    do_some_math()