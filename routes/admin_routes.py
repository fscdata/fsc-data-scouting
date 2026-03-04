import os
from flask import Blueprint, render_template, request, redirect
# import the shared basic_auth instance from extensions to avoid circular imports
from extensions import basic_auth
from database_model import db, Event, Team, MatchData

bp = Blueprint("admin", __name__, url_prefix="/admin")

# basic_auth instance is configured in the main application module

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
    print(' > Triggering job to query official match schedule data from FIRST API')
    # kick off external script to query official match schedule data from FIRST API
    os.system('python cron/query_official_schedule.py')
    return redirect('/admin/query_official_data')

@bp.route("/trigger_query_match_data")
@basic_auth.required
def trigger_query_match_data():
    print(' > Triggering job to query official match result data from FIRST API')
    # kick off external script to query official match result data from FIRST API
    os.system('python cron/query_official_match_data.py')
    return redirect('/admin/query_official_data')