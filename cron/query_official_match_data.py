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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    'SQLALCHEMY_DB_URI', f"sqlite:///{os.path.join(ROOT_DIR, 'instance', 'scouting.db')}")
db.init_app(app)

first_api_base_url = 'https://frc-api.firstinspires.org/v3.0'

def get_api_token():
    '''
    Helper function to retrieve and encode FIRST API credentials for authentication.
    Returns:
        dict: Headers containing the Authorization token for API requests.
    '''
    first_api_username = os.environ.get('FIRST_API_USERNAME')
    first_api_key = os.environ.get('FIRST_API_KEY')
    if not first_api_username or not first_api_key:
        print("Error: FIRST API credentials not found in environment variables.")
        exit(1)
    # encode the token in base 64
    encoded_token = base64.b64encode(bytes(f'{first_api_username}:{first_api_key}', 'utf-8'))
    headers = {
        'Authorization' : f'Basic {encoded_token.decode("utf-8")}'
    }

    return headers

def find_active_event():
    with app.app_context():
        # find active event in database and get event_id and event_code
        event_id = db.session\
            .query(Event.event_id)\
            .filter(Event.event_currently_active == True)\
            .scalar()
        event_code = db.session\
            .query(Event.event_code )\
            .filter(Event.event_currently_active == True)\
            .scalar()
    return event_id, event_code

def find_next_match_to_query():
    event_id, event_code = find_active_event()

    with app.app_context():
        # query maximum match_id in local database for the given event_id
        max_match_id = db.session\
            .query(db.func.max(MatchData.match_id))\
            .filter(MatchData.event_id == event_id, MatchData.red_rp != None)\
            .scalar()

        if max_match_id is not None:
            print(f'Most recent match results for event {event_id}: Match {max_match_id}')
            next_match_id = max_match_id + 1
            print(f'Next match to query for event {event_id}: Match {next_match_id}')
            return next_match_id
        else:
            print(f'No match results found yet for event {event_id}.')
            return 1

def api_call_match_data(event_year, match_level, match_number):
    event_id, event_code = find_active_event()

    with app.app_context():
        existing_match = db.session.query(MatchData).filter_by(event_id=event_id, match_number=match_number).first()
        if not existing_match:
            print(f'No existing match record found for match {match_number}, unable to update match results. Please check that match schedule data has been properly ingested for this match.')
        else:
            single_match_scores_url = f'{first_api_base_url}/{event_year}/scores/{event_code}/{match_level}?matchNumber={match_number}'
            headers = get_api_token()
            print(single_match_scores_url)

            single_match_response = requests.get(single_match_scores_url, headers=headers)
            # print response status
            print(f'Status Code: {single_match_response.status_code}')
            if single_match_response.status_code == 200:
                # data = response.content.decode("utf-8")
                # convert to json for sanity
                single_match_score_data = single_match_response.json()

            if len(single_match_score_data['MatchScores']) == 0:
                print(f'Match {match_number} not found in score data, validate it is completed and posted.')
                return

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
            if red_rp is None:
                red_rp = 0
            blue_rp = blue_dict['rp']
            if blue_rp is None:
                blue_rp = 0

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

            # update database record for the match with the new data
            existing_match.red_rp = red_rp
            existing_match.blue_rp = blue_rp
            existing_match.red_auto_score = red_auto_score
            existing_match.red_teleop_score = red_teleop_score
            existing_match.blue_auto_score = blue_auto_score
            existing_match.blue_teleop_score = blue_teleop_score
            existing_match.red_1_auto_climb = red_1_auto_climb
            existing_match.red_2_auto_climb = red_2_auto_climb
            existing_match.red_3_auto_climb = red_3_auto_climb
            existing_match.blue_1_auto_climb = blue_1_auto_climb
            existing_match.blue_2_auto_climb = blue_2_auto_climb
            existing_match.blue_3_auto_climb = blue_3_auto_climb
            existing_match.red_1_endgame_climb = red_1_endgame_climb
            existing_match.red_2_endgame_climb = red_2_endgame_climb
            existing_match.red_3_endgame_climb = red_3_endgame_climb
            existing_match.blue_1_endgame_climb = blue_1_endgame_climb
            existing_match.blue_2_endgame_climb = blue_2_endgame_climb
            existing_match.blue_3_endgame_climb = blue_3_endgame_climb
            db.session.commit()
            print(f'Match data for match {match_number} successfully updated in database.')

if __name__ == "__main__":
    event_year = 2026
    match_level = 'Qualification'

    next_match_id = find_next_match_to_query()

    api_call_match_data(
        event_year = event_year,
        match_level = match_level,
        match_number = next_match_id)
