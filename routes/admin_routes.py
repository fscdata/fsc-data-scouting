import os
import base64
import requests
from flask import Blueprint, render_template, request, redirect
# import the shared basic_auth instance from extensions to avoid circular imports
from extensions import basic_auth
from database_model import db, Event, Team, MatchData, MatchTeamData

bp = Blueprint("admin", __name__, url_prefix="/admin")

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

def find_next_match_to_query():
    event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == True)\
        .scalar()

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

def api_call_match_data(match_number, match_level = 'Qualification'):
    event_info = db.session\
        .query(Event.event_id, Event.event_code, Event.event_year)\
        .filter(Event.event_currently_active == True)\
        .all()
    print(event_info)
    event_id = event_info[0][0]
    event_code = event_info[0][1]
    event_year = event_info[0][2]

    existing_match = db.session\
        .query(MatchData)\
        .filter(
            MatchData.event_id == event_id,
            MatchData.match_number == match_number)\
        .first()
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
        match_type = match_dict['matchLevel']

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

def request_match_data(event_id: int, match_number: int):
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

def enhance_match_team_data():
    event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == True)\
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
        auto_climb_dict, endgame_climb_dict = request_match_data(event_id, match_number)
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

''' app routes '''

@bp.route("/")
@basic_auth.required
def admin_index():
    return render_template('admin/admin_navigation.html')

@bp.route("/maintenance_frc_teams")
@basic_auth.required
def admin_maintenance_frc_teams():
    print(' > Rendering admin FRC teams maintenance page')
    team_data = db.session.query(Team.team_id, Team.team_name).all()
    return render_template(
        'admin/maintenance_frc_teams.html',
        team_data=team_data)

@bp.route("/addto_frc_teams", methods=['POST'])
@basic_auth.required
def add_new_team():
    if request.method == 'POST':
        print(request.form)
        form_dict = request.form.to_dict(flat=False)
        print(form_dict)

        new_team_data = {
            'team_id': int(request.form.get('team_number', 0)),
            'team_name': request.form.get('team_name', ''),
        }

        valid_keys = [c.name for c in Team.__table__.columns]
        filtered_data = {k: v for k, v in new_team_data.items() if k in valid_keys}

        new_team_record = Team(**filtered_data)

        db.session.add(new_team_record)
        db.session.commit()

        print(f' > Successfully added team to database')
        return redirect('/admin/maintenance_frc_teams')

@bp.route("/update_frc_teams")
@basic_auth.required
def update_frc_teams():
    team_number = request.args.get('team', 0)
    print(f' > Attempting to remove team {team_number}')
    db.session.query(Team).filter(Team.team_id == team_number).delete()
    db.session.commit()
    print(f' > Successfully removed team {team_number}')
    return redirect('/admin/maintenance_frc_teams')

'''
Admin routes for maintaining Active Events table
'''
@bp.route("/maintenance_active_events")
@basic_auth.required
def admin_maintenance_active_events():
    print(' > Rendering admin active events maintenance page')
    event_data = db.session.query(Event.event_id, Event.event_code, Event.event_name, Event.event_date, Event.event_currently_active).all()
    return render_template('admin/maintenance_active_events.html', event_data=event_data)

@bp.route("/addto_active_events", methods=['POST'])
@basic_auth.required
def add_new_active_event():
    if request.method == 'POST':
        print(request.form)
        form_dict = request.form.to_dict(flat=False)
        print(form_dict)

        # capture fields from form
        new_event_data = {
            'event_code': request.form.get('event_code', ''),
            'event_name': request.form.get('event_name', ''),
            'event_date': request.form.get('event_date', ''),
            'event_year': int(request.form.get('event_year', 2026)),
            'event_currently_active': False,
        }

        # Filter out keys that are not in the Event model
        valid_keys = [c.name for c in Event.__table__.columns]
        filtered_data = {k: v for k, v in new_event_data.items() if k in valid_keys}

        new_event_record = Event(**filtered_data)

        db.session.add(new_event_record)
        db.session.commit()

        print(f' > Successfully added event to database')
        return redirect('/admin/maintenance_active_events')

@bp.route("/update_events")
@basic_auth.required
def update_events():
    event_id = request.args.get('event', 0)
    print(f' > Attempting to remove event {event_id}')
    db.session.query(Event).filter(Event.event_id == event_id).delete()
    db.session.commit()
    print(f' > Successfully removed event {event_id}')
    return redirect('/admin/maintenance_active_events')

@bp.route("/toggle_active_events")
@basic_auth.required
def toggle_active_events():
    event_id = request.args.get('event', 0)
    print(f' > Toggle event {event_id} active status')
    event = db.session.query(Event).filter(Event.event_id == event_id).first()
    if event is None:
        print(f' > Event {event_id} not found in database')
        return redirect('/admin/maintenance_active_events')
    if event.event_currently_active:
        # If the event is currently active, set it to inactive
        db.session.query(Event).filter(Event.event_id == event_id).update({Event.event_currently_active: False})
        db.session.commit()
        print(f' > Successfully deactivated event {event_id}')
        return redirect('/admin/maintenance_active_events')
    if not event.event_currently_active:
        # If the event is currently inactive, set it to active
        db.session.query(Event).filter(Event.event_id == event_id).update({Event.event_currently_active: True})
        db.session.commit()
        print(f' > Successfully activated event {event_id}')
        return redirect('/admin/maintenance_active_events')

'''
trigger external jobs
'''
@bp.route("/do_some_math")
@basic_auth.required
def trigger_calculate_report_data():
    print(' > Triggering job to calculate report data')
    # kick off external script to calculate report data
    os.system('python cron/calculate_report_data.py')
    return redirect('/admin/')

@bp.route("/query_official_data")
@basic_auth.required
def trigger_query_official_data():
    active_event_data = db.session\
        .query(Event.event_id, Event.event_code, Event.event_name, Event.event_date, Event.event_currently_active)\
        .filter(Event.event_currently_active == True)\
        .all()
    event_match_data = db.session\
        .query(
            MatchData.match_number,
            MatchData.red_1_id,
            MatchData.red_2_id,
            MatchData.red_3_id,
            MatchData.blue_1_id,
            MatchData.blue_2_id,
            MatchData.blue_3_id,
            MatchData.red_rp,
            MatchData.blue_rp)\
        .filter(MatchData.event_id.in_([event.event_id for event in active_event_data]))\
        .all()
    print(event_match_data)
    return render_template(
        'admin/query_official_data.html',
        active_event_data=active_event_data,
        event_match_data=event_match_data)

@bp.route("/trigger_query_schedule")
@basic_auth.required
def trigger_query_schedule():
    active_event_year = db.session\
        .query(Event.event_year)\
        .filter(Event.event_currently_active == True)\
        .scalar()

    print(' > Triggering job to query official match schedule data from FIRST API')
    api_call_schedule_data(
        event_year = active_event_year,
        match_level = 'Qualification')
    return redirect('/admin/query_official_data')

@bp.route("/trigger_query_match_data")
@basic_auth.required
def trigger_query_match_data():
    print(' > Triggering job to query official match result data from FIRST API')

    next_match_number = find_next_match_to_query()
    api_call_match_data(
        match_number = next_match_number,
        match_level = 'Qualification')
    enhance_match_team_data()
    return redirect('/admin/query_official_data')