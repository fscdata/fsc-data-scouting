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

def api_call_schedule_data(event_year, match_level = 'Qualification'):
    # push data to database for storage
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

        # call FIRST API to get match schedule data for the event
        match_schedule_url = f'{first_api_base_url}/{event_year}/matches/{event_code}?tournamentLevel={match_level}'
        print(match_schedule_url)

        headers = get_api_token()

        schedule_response  = requests.get(match_schedule_url, headers=headers)
        print(f'Status Code: {schedule_response.status_code}')
        if schedule_response.status_code == 200:
            match_schedule_data = schedule_response.json()

        for match in match_schedule_data['Matches']:
            match_number = match['matchNumber']
            print(f' > Processing match {match_number} from schedule data')
            for i in range(6):
                team_record = match['teams'][i]
                # print(f"Station: {team_record['station']}, Team Number: {team_record['teamNumber']}")
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

            # structure data into MatchData object and push to database
            match_record = MatchData(
                event_id=event_id,
                match_number=match_number,
                match_type=match_level,
                red_1_id=red_1_id,
                red_2_id=red_2_id,
                red_3_id=red_3_id,
                blue_1_id=blue_1_id,
                blue_2_id=blue_2_id,
                blue_3_id=blue_3_id
            )

            db.session.add(match_record)
            db.session.commit()
            print(f'Match data for match {match_number} successfully added to database.')

if __name__ == "__main__":
    event_year = 2026
    match_level = 'Qualification'

    api_call_schedule_data(event_year = event_year)
