import os
import sys
import base64
import requests
from flask import Flask

# Ensure project root is on sys.path so `database_model` can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from database_model import db, Event, MatchData

# Create a minimal Flask app for database access
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('SQLALCHEMY_DB_URI', 'sqlite:///scouting.db')
db.init_app(app)

first_api_username = os.environ.get('FIRST_API_USERNAME')
first_api_key = os.environ.get('FIRST_API_KEY')
if not first_api_username or not first_api_key:
    print("Error: FIRST API credentials not found in environment variables.")
    exit(1)
first_api_base_url = 'https://frc-api.firstinspires.org/v3.0'

def find_next_match_to_query(event_code: str):
    with app.app_context():
        # query events table to find event_id
        event_id = db.session.query(Event.event_id).filter(Event.event_code == event_code).scalar()
        # query maximum match_id for the given event_id
        max_match_id = db.session.query(db.func.max(MatchData.match_id)).filter(MatchData.event_id == event_id).scalar()

        if max_match_id is not None:
            print(f'Most recent match data for event {event_id}: Match {max_match_id}')
            next_match_id = max_match_id + 1
            print(f'Next match to query for event {event_id}: Match {next_match_id}')
            return next_match_id
        else:
            print(f'No match data found yet for event {event_id}.')
            return 1

def api_call_match_data(event_year, event_code, match_level, match_number):
    match_schedule_url = f'{first_api_base_url}/{event_year}/matches/{event_code}?tournamentLevel={match_level}&matchNumber={match_number}'

    single_match_scores_url = f'{first_api_base_url}/{event_year}/scores/{event_code}/{match_level}?matchNumber={match_number}'

    # encode the token in base 64
    encoded_token = base64.b64encode(bytes('fscdata:fcc8c8e6-12b2-4d89-8e14-3141f969c8d5', 'utf-8'))
    headers = {
        'Authorization' : f'Basic {encoded_token.decode("utf-8")}'
    }

    print(match_schedule_url)
    print(single_match_scores_url)
    print(headers)

    single_match_response = requests.get(single_match_scores_url, headers=headers)
    # print response status
    print(f'Status Code: {single_match_response.status_code}')
    if single_match_response.status_code == 200:
        # data = response.content.decode("utf-8")
        # convert to json for sanity
        single_match_score_data = single_match_response.json()

    schedule_response  = requests.get(match_schedule_url, headers=headers)
    print(f'Status Code: {schedule_response.status_code}')
    if schedule_response.status_code == 200:
        match_schedule_data = schedule_response.json()

    schedule_dict = None

    for match in match_schedule_data['Matches']:
        if match['matchNumber'] == match_number:
            schedule_dict = match
            break

    if not schedule_dict:
        print(f'Match {match_number} not found in schedule data, validate it is completed and posted.')
        return
    else:
        for i in range(6):
            team_record = schedule_dict['teams'][i]
            print(f"Station: {team_record['station']}, Team Number: {team_record['teamNumber']}")
            if team_record['station'] == 'Red1':
                red_1_id = team_record['teamNumber']
            elif team_record['station'] == 'Red2':
                red_2_id = team_record['teamNumber']
            elif team_record['station'] == 'Red3':
                red_3_id = team_record['teamNumber']
            elif team_record['station'] == 'Blue1':
                blue_1_id = team_record['teamNumber']
            elif team_record['station'] == 'Blue2':
                blue_2_id = team_record['teamNumber']
            elif team_record['station'] == 'Blue3':
                blue_3_id = team_record['teamNumber']

    match_dict = single_match_score_data['MatchScores'][0]

    match_number = match_dict['matchNumber']
    print(f'Match Number: {match_number}')

    match_type = match_dict['matchLevel']
    print(f'Match Type: {match_type}')

    if match_dict['alliances'][0]['alliance'] == 'Red':
        red_dict = match_dict['alliances'][0]
        blue_dict = match_dict['alliances'][1]
    else:
        red_dict = match_dict['alliances'][1]
        blue_dict = match_dict['alliances'][0]

    if not 'rp' in red_dict or not 'rp' in blue_dict:
        print('RP data not found for both alliances, validate match is completed and posted.')
        print(red_dict)
        print(blue_dict)
        return

    red_rp = red_dict['rp']
    blue_rp = blue_dict['rp']

    if not 'hubScore' in red_dict or not 'hubScore' in blue_dict:
        print('hubScore data not found for both alliances, validate match is completed and posted.')
        print(red_dict)
        print(blue_dict)
        return
    red_auto_score = red_dict['hubScore']['autoPoints']
    blue_auto_score = blue_dict['hubScore']['autoPoints']
    red_teleop_score = red_dict['hubScore']['teleopPoints']
    blue_teleop_score = blue_dict['hubScore']['teleopPoints']

    red_1_auto_climb = red_dict['autoTowerRobot1']
    blue_1_auto_climb = blue_dict['autoTowerRobot1']
    red_2_auto_climb = red_dict['autoTowerRobot2']
    blue_2_auto_climb = blue_dict['autoTowerRobot2']
    red_3_auto_climb = red_dict['autoTowerRobot3']
    blue_3_auto_climb = blue_dict['autoTowerRobot3']

    red_1_endgame_climb = red_dict['endGameTowerRobot1']
    red_2_endgame_climb = red_dict['endGameTowerRobot2']
    red_3_endgame_climb = red_dict['endGameTowerRobot3']
    blue_1_endgame_climb = blue_dict['endGameTowerRobot1']
    blue_2_endgame_climb = blue_dict['endGameTowerRobot2']
    blue_3_endgame_climb = blue_dict['endGameTowerRobot3']

    # push data to database for storage
    with app.app_context():
        event_id = db.session\
            .query(Event.event_id)\
            .filter(Event.event_code == event_code)\
            .scalar()

        match_record = MatchData(
            event_id=event_id,
            match_number=match_number,
            match_type=match_type,
            red_1_id=red_1_id,
            red_2_id=red_2_id,
            red_3_id=red_3_id,
            blue_1_id=blue_1_id,
            blue_2_id=blue_2_id,
            blue_3_id=blue_3_id,
            red_rp=red_rp,
            blue_rp=blue_rp,
            red_auto_score=red_auto_score,
            red_teleop_score=red_teleop_score,
            blue_auto_score=blue_auto_score,
            blue_teleop_score=blue_teleop_score,
            red_1_auto_climb=red_1_auto_climb,
            red_2_auto_climb=red_2_auto_climb,
            red_3_auto_climb=red_3_auto_climb,
            blue_1_auto_climb=blue_1_auto_climb,
            blue_2_auto_climb=blue_2_auto_climb,
            blue_3_auto_climb=blue_3_auto_climb,
            red_1_endgame_climb=red_1_endgame_climb,
            red_2_endgame_climb=red_2_endgame_climb,
            red_3_endgame_climb=red_3_endgame_climb,
            blue_1_endgame_climb=blue_1_endgame_climb,
            blue_2_endgame_climb=blue_2_endgame_climb,
            blue_3_endgame_climb=blue_3_endgame_climb,
        )
        db.session.add(match_record)
        db.session.commit()
        print(f'Match data for match {match_number} successfully added to database.')

if __name__ == "__main__":
    event_year = 2026
    event_code = 'WEEK0'
    match_level = 'Qualification'

    next_match_id = find_next_match_to_query(event_code = 'WEEK0')

    api_call_match_data(
        event_year = event_year,
        event_code = event_code,
        match_level = match_level,
        match_number = next_match_id)
