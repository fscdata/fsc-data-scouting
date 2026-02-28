from flask import Blueprint, render_template, request, redirect
from database_model import db, MatchTeamData, Event

bp = Blueprint("scout", __name__, url_prefix="/scout")

@bp.route("/")
def scout_page():
    active_event_id = db.session.query(Event.event_id).filter(Event.event_currently_active == 1).scalar()
    print(f'Active event ID for new scouting record: {active_event_id}')
    if active_event_id is None:
        error_message = 'No active event found. Please find a Scouting Alliance admin to set an active event.'
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
        new_record_data = {
            'event_id': active_event_id,
            'match_id': int(request.form.get('match_number', 0)),
            'team_number': int(request.form.get('team_number', 0)),
            'auto_fuel_score': int(request.form.get('auto_fuel_score', 0)),
            'auto_climb_try': bool(int(request.form.get('auto_climb_try', 0))),
            'auto_traveled': bool(int(request.form.get('auto_traveled', 0))),
            'teleop_fuel_score': int(request.form.get('teleop_fuel_score', 0)),
            'teleop_traveled': bool(int(request.form.get('teleop_traveled', 0))),
            'teleop_climb_try': bool(int(request.form.get('teleop_climb_try', 0))),
            'match_tipped': 'tipped' in request.form,
            'match_broke': 'broken' in request.form,
            'match_card': 'carded' in request.form,
            'match_disabled': 'disabled' in request.form,
            'match_absent': 'absent' in request.form,
        }
        print(new_record_data)
    
        # set records to None (or 0 if boolean) if no data is present
        for key, value in new_record_data.items():
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
