import os
import sys
from datetime import datetime
from flask import Flask
import requests

# Ensure project root is on sys.path so `database_model` can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from database_model import db, Event, MatchData, MatchTeamData, Calculation

# Create a minimal Flask app for database access
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('SQLALCHEMY_DB_URI', 'sqlite:///scouting.db')
db.init_app(app)

def fetch_tba_event_stats(event_key: str):
    """Bulk-fetch OPR/DPR/CCWM/rank for every team at an event from TBA.

    Returns {team_number: {'opr', 'dpr', 'ccwm', 'rank'}}, only including
    teams TBA has data for. Returns {} on any API failure.
    """
    tba_api_key = os.environ.get('TBA_API_KEY')
    base_tba_url = 'https://www.thebluealliance.com/api/v3'
    if not tba_api_key:
        print("Error: Blue Alliance API credentials not found in environment variables.")
        return {}

    headers = {'X-TBA-Auth-Key': tba_api_key}
    tba_stats = {}

    try:
        oprs_response = requests.get(f'{base_tba_url}/event/{event_key}/oprs', headers=headers)
        if oprs_response.status_code == 200:
            oprs_data = oprs_response.json()
            for team_key in oprs_data.get('oprs', {}):
                team_num = int(team_key[3:])
                tba_stats.setdefault(team_num, {})
                tba_stats[team_num]['opr'] = round(oprs_data['oprs'][team_key], 2)
                tba_stats[team_num]['dpr'] = round(oprs_data.get('dprs', {}).get(team_key, 0), 2)
                tba_stats[team_num]['ccwm'] = round(oprs_data.get('ccwms', {}).get(team_key, 0), 2)
        else:
            print(f'Status Code: {oprs_response.status_code}')
            print(' !!! TBA oprs api error')
    except requests.RequestException:
        print(' !!! TBA oprs api error')

    try:
        rankings_response = requests.get(f'{base_tba_url}/event/{event_key}/rankings', headers=headers)
        if rankings_response.status_code == 200:
            rankings_data = rankings_response.json()
            for team in rankings_data.get('rankings', []):
                team_num = int(team['team_key'][3:])
                tba_stats.setdefault(team_num, {})
                tba_stats[team_num]['rank'] = team['rank']
        else:
            print(f'Status Code: {rankings_response.status_code}')
            print(' !!! TBA rankings api error')
    except requests.RequestException:
        print(' !!! TBA rankings api error')

    return tba_stats

def fetch_statbotics_epa(event_key: str):
    """Bulk-fetch each team's EPA at an event from Statbotics.

    Returns {team_number: epa}. The Statbotics v3 API is public and needs no
    API key. Returns {} on any API failure.
    """
    stats_endpoint_url = 'https://api.statbotics.io/v3/team_events'

    try:
        response = requests.get(stats_endpoint_url, params={'event': event_key, 'limit': 1000})
        if response.status_code != 200:
            print(f'Status Code: {response.status_code}')
            print(' !!! statbotics api error')
            return {}

        team_events = response.json()
        return {
            team_event['team']: team_event['epa']
            for team_event in team_events
            if team_event.get('epa') is not None
        }
    except requests.RequestException:
        print(' !!! statbotics api error')
        return {}

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
                if team_num not in team_climb_stats:
                    team_climb_stats[team_num] = {
                        'match_count': 0,
                        'auto_climb_try': 0,
                        'auto_climbed': 0,
                        'endgame_climb_try': 0,
                        'endgame_climbed': 0
                    }
                team_climb_stats[team_num]['match_count'] += 1
                if match.auto_climb_try is not None:
                    team_climb_stats[team_num]['auto_climb_try'] += 1
                if match.auto_climbed is not None:
                    team_climb_stats[team_num]['auto_climbed'] += 1
                if match.endgame_climb_try is not None:
                    team_climb_stats[team_num]['endgame_climb_try'] += 1
                if match.endgame_climb_level is not None:
                    team_climb_stats[team_num]['endgame_climbed'] += 1
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

        event_info = db.session\
            .query(Event.event_year, Event.event_code)\
            .filter(Event.event_id == event_id)\
            .first()
        if event_info:
            event_key = f'{event_info.event_year}{event_info.event_code.lower()}'
            print(f'> Fetching archived stats for event {event_key}')
            tba_stats = fetch_tba_event_stats(event_key)
            statbotics_epa = fetch_statbotics_epa(event_key)
            now = datetime.utcnow()

            for team_number in event_team_list:
                team_num = team_number[0]
                update_values = {Calculation.last_updated: now}
                if team_num in tba_stats:
                    update_values[Calculation.event_opr] = tba_stats[team_num].get('opr')
                    update_values[Calculation.event_dpr] = tba_stats[team_num].get('dpr')
                    update_values[Calculation.event_ccwm] = tba_stats[team_num].get('ccwm')
                    update_values[Calculation.tba_rank] = tba_stats[team_num].get('rank')
                if team_num in statbotics_epa:
                    update_values[Calculation.event_epa] = statbotics_epa[team_num]
                db.session.query(Calculation)\
                    .filter(Calculation.event_id == event_id, Calculation.team_number == team_num)\
                    .update(update_values)
            db.session.commit()

if __name__ == "__main__":
    do_some_math()