from flask import Blueprint, render_template, request, redirect
from database_model import db, MatchData, MatchTeamData, Event

bp = Blueprint("scout", __name__, url_prefix="/scout")

# @bp.route("/", methods=['GET', 'POST'])
# def scout_page():
#     active_event_id = db.session.query(Event.event_id).filter(Event.event_currently_active == 1).scalar()
#     if active_event_id is None:
#         error_message = 'No active event found. Please find a Scouting Alliance admin to set an active event. (CONTACT PFISTER.)'
#         print(f' ! {error_message}')
#         return render_template('error.html', error_message=error_message)
#     print(' > Rendering scout page')
#     return render_template('scout_page.html')

@bp.route('/')
def scout_landing_page():
    # ask scouter what they are scouting and in what match number
    print(' > Rendering scouter routing page')
    return render_template('scout/scout_routing_page.html')

@bp.route('/robot_data', methods=['POST'])
def scout_a_robot():
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()
    # ensure an event is active and ready to be scouted, error page if not
    if active_event_id is None:
        error_message = 'No active event found. Please find a Scouting Alliance admin to set an active event. (CONTACT PFISTER.)'
        print(f' ! {error_message}')
        return render_template('error.html', error_message=error_message)
    if request.method == 'POST':
        form_dict = request.form.to_dict(flat=False)

        specified_match_number = form_dict['match_number'][0]
        alliance_position = form_dict['alliance_bot'][0]

        team_numbers_in_match = db.session\
            .query(MatchData.red_1_id,
                MatchData.red_2_id,
                MatchData.red_3_id,
                MatchData.blue_1_id,
                MatchData.blue_2_id,
                MatchData.blue_3_id)\
            .filter(MatchData.event_id == active_event_id,
                    MatchData.match_number == int(specified_match_number))\
            .all()[0]
        if alliance_position == 'red_1':
            specified_team_number = team_numbers_in_match[0]
        elif alliance_position == 'red_2':
            specified_team_number = team_numbers_in_match[1]
        elif alliance_position == 'red_3':
            specified_team_number = team_numbers_in_match[2]
        elif alliance_position == 'blue_1':
            specified_team_number = team_numbers_in_match[3]
        elif alliance_position == 'blue_2':
            specified_team_number = team_numbers_in_match[4]
        elif alliance_position == 'blue_3':
            specified_team_number = team_numbers_in_match[5]

        return render_template(
            'scout/scout_robot_page.html',
            match_number=specified_match_number,
            team_number=specified_team_number)

@bp.route('/human_data', methods=['POST'])
def scout_a_human():
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()
    # ensure an event is active and ready to be scouted, error page if not
    if active_event_id is None:
        error_message = 'No active event found. Please find a Scouting Alliance admin to set an active event. (CONTACT PFISTER.)'
        print(f' ! {error_message}')
        return render_template('error.html', error_message=error_message)
    if request.method == 'POST':
        form_dict = request.form.to_dict(flat=False)
        specified_match_number = form_dict['match_number'][0]
        specified_alliance = form_dict['alliance_human'][0].strip('_human')

        print(specified_alliance)

        return render_template(
            'scout/scout_human_page.html',
            match_number=specified_match_number,
            alliance=specified_alliance)

@bp.route('/add_human_data', methods=['POST'])
def add_scout_data_human():
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()
    print(f'Active event ID for new scouting record: {active_event_id}')

    if request.method == 'POST':
        form_dict = request.form.to_dict(flat=False)

        # capture and validate fields from form
        required_fields = ['match_number', 'alliance', 'human_fuel_score']
        for field in required_fields:
            if field not in form_dict:
                error_message = f'Missing required field: {field}'
                print(f' ! {error_message}')
                return render_template('error.html', error_message=error_message)
        if not form_dict['match_number'][0].isdigit():
            error_message = f'Match number must be a positive integer (such as 1) and not include letters or spaces --- user entered {form_dict["match_number"][0]}. Please hit "Back," check your inputs, and try again.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)
        if not form_dict['alliance'][0] in ('red', 'blue'):
            error_message = f'Alliance must be either blue or red --- user entered {form_dict["alliance"][0]}. Please hit "Back," check your inputs, and try again.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)
        validated_form_data = {
            'event_id': active_event_id,
            'match_number': int(form_dict['match_number'][0], 0),
            'alliance': form_dict['alliance'][0],
            'human_fuel_score': int(form_dict['human_fuel_score'][0], 0),}

        if not validated_form_data:
            error_message = 'Data validation failed, please hit "Back," check your inputs, and try again.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)

        try:
            existing_match = db.session\
                .query(MatchData)\
                .filter(
                    MatchData.event_id == active_event_id,
                    MatchData.match_number == validated_form_data['match_number'])\
                .first()
            if validated_form_data['alliance'] == 'blue':
                existing_match.blue_human_score = validated_form_data['human_fuel_score']
            elif validated_form_data['alliance'] == 'red':
                existing_match.red_human_score = validated_form_data['human_fuel_score']
            else:
                error_message = f'Alliance can either be blue or red, not {validated_form_data["alliance"]}. please hit "Back," check your inputs, and try again.'
                print(f' ! {error_message}')
                return render_template('error.html', error_message=error_message)
            db.session.commit()

            print(f' > Successfully added scouting record to database')
            return redirect('/confirmed')
        except Exception as e:
            db.session.rollback()
            error_message = f'An error occurred while adding the record to the database: {str(e)}. Please hit "Back," check your inputs, and try again. If you have seen this multiple times CONTACT PFISTER.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)

@bp.route('/add_data', methods=['POST'])
def add_scout_data_robot():
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()
    print(f'Active event ID for new scouting record: {active_event_id}')

    if request.method == 'POST':
        form_dict = request.form.to_dict(flat=False)

        # capture and validate fields from form
        required_fields = ['match_number', 'team_number', 'auto_fuel_score', 'auto_climb_try', 'teleop_fuel_score', 'endgame_climb_try']
        for field in required_fields:
            if field not in form_dict:
                error_message = f'Missing required field: {field}'
                print(f' ! {error_message}')
                return render_template('error.html', error_message=error_message)
        if not form_dict['match_number'][0].isdigit():
            error_message = f'Match number must be a positive integer (such as 1) and not include letters or spaces --- user entered {form_dict["match_number"][0]}. Please hit "Back," check your inputs, and try again.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)
        if not form_dict['team_number'][0].isdigit():
            error_message = f'Team number must be a positive integer (such as 123) and not include letters or spaces  --- user entered {form_dict["team_number"][0]}. Please hit "Back," check your inputs, and try again.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)
        validated_form_data = {
                'event_id': active_event_id,
                'match_number': int(form_dict['match_number'][0], 0),
                'team_number': int(form_dict['team_number'][0], 0),
                'auto_fuel_score': int(form_dict['auto_fuel_score'][0], 0),
                'auto_climb_try': bool(int(form_dict['auto_climb_try'][0], 0)),
                # 'auto_traveled': bool(int(form_dict['auto_traveled'][0], 0)),
                'teleop_fuel_score': int(form_dict['teleop_fuel_score'][0], 0),
                # 'teleop_traveled': bool(int(form_dict['teleop_traveled'][0], 0)),
                'endgame_climb_try': bool(int(form_dict['endgame_climb_try'][0], 0)),
                'strategy_active_scored': 1 if 'active_scored' in form_dict else 0,
                'strategy_active_ferrying': 1 if 'active_ferrying' in form_dict else 0,
                'strategy_active_defense': 1 if 'active_defense' in form_dict else 0,
                'strategy_inactive_scored': 1 if 'inactive_scored' in form_dict else 0,
                'strategy_inactive_ferrying': 1 if 'inactive_ferrying' in form_dict else 0,
                'strategy_inactive_defense': 1 if 'inactive_defense' in form_dict else 0,
                'strategy_defense_actions': int(form_dict['strat_defense'][0], 0),
                'match_tipped':  1 if 'tipped' in form_dict else 0,
                'match_broken':  1 if 'broken' in form_dict else 0,
                'match_beached':  1 if 'beached' in form_dict else 0,
                'match_carded':  1 if 'carded' in form_dict else 0,
                'match_disabled':  1 if 'disabled' in form_dict else 0,
                'match_absent':  1 if 'absent' in form_dict else 0,
            }
        print(validated_form_data)

        if not validated_form_data:
            error_message = 'Data validation failed, please hit "Back," check your inputs, and try again.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)
    
        # set records to None (or 0 if boolean) if no data is present
        new_record_data = {}
        for key, value in validated_form_data.items():
            print(f'Processing field {key} with value {value} and type {type(value)}')
            if value == '' or value is None:
                new_record_data[key] = None
            elif isinstance(value, bool):
                new_record_data[key] = int(value)
            else:
                new_record_data[key] = value

        new_match_record = MatchTeamData(**new_record_data)

        # add IP address of submitter
        if request.remote_addr:
            new_match_record.record_ip_address = request.remote_addr
            print(f'Captured IP address: {request.remote_addr}')
        else:
            new_match_record.record_ip_address = '0.0.0.0'
            print('No IP address found in request')

        # commit new record to database with error handling
        try:
            db.session.add(new_match_record)
            db.session.commit()

            print(f' > Successfully added scouting record to database')
            return redirect('/confirmed')
        except Exception as e:
            db.session.rollback()
            error_message = f'An error occurred while adding the record to the database: {str(e)}. Please hit "Back," check your inputs, and try again. If you have seen this multiple times CONTACT PFISTER.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)