from flask import Blueprint, render_template, request, redirect
from database_model import db, MatchTeamData, Event

bp = Blueprint("scout", __name__, url_prefix="/scout")

@bp.route("/", methods=['GET', 'POST'])
def scout_page():
    active_event_id = db.session.query(Event.event_id).filter(Event.event_currently_active == 1).scalar()
    if active_event_id is None:
        error_message = 'No active event found. Please find a Scouting Alliance admin to set an active event. (CONTACT PFISTER.)'
        print(f' ! {error_message}')
        return render_template('error.html', error_message=error_message)
    print(' > Rendering scout page')
    return render_template('scout_page.html')

@bp.route('/add_data', methods=['POST'])
def add_new():
    active_event_id = db.session.query(Event.event_id).filter(Event.event_currently_active == 1).scalar()
    print(f'Active event ID for new scouting record: {active_event_id}')

    if request.method == 'POST':
        # print(request.form)
        form_dict = request.form.to_dict(flat=False)
        print(form_dict)

        # capture fields from form

        required_fields = ['match_number', 'team_number', 'auto_fuel_score', 'auto_climb_try', 'auto_traveled', 'teleop_fuel_score', 'teleop_traveled', 'endgame_climb_try']
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
                'event_id': 1,
                'match_id': int(form_dict['match_number'][0], 0),
                'team_number': int(form_dict['team_number'][0], 0),
                'auto_fuel_score': int(form_dict['auto_fuel_score'][0], 0),
                'auto_climb_try': bool(int(form_dict['auto_climb_try'][0], 0)),
                'auto_traveled': bool(int(form_dict['auto_traveled'][0], 0)),
                'teleop_fuel_score': int(form_dict['teleop_fuel_score'][0], 0),
                'teleop_traveled': bool(int(form_dict['teleop_traveled'][0], 0)),
                'endgame_climb_try': bool(int(form_dict['endgame_climb_try'][0], 0)),
                'match_tipped':  1 if 'tipped' in form_dict else 0,
                'match_broke':  1 if 'broke' in form_dict else 0,
                'match_card':  1 if 'carded' in form_dict else 0,
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
            if value == '' or value is None:
                new_record_data[key] = None
            elif isinstance(value, bool):
                new_record_data[key] = int(value)

        # Filter out keys that are not in the MatchTeamData model
        valid_keys = [c.name for c in MatchTeamData.__table__.columns]
        filtered_data = {k: v for k, v in new_record_data.items() if k in valid_keys}

        new_match_record = MatchTeamData(**filtered_data)

        db.session.add(new_match_record)
        db.session.commit()

        print(f' > Successfully added scouting record to database')
        return redirect('/confirmed')
