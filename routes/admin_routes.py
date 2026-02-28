from flask import Blueprint, render_template, request, redirect
from database_model import db, Event, Team

bp = Blueprint("admin", __name__, url_prefix="/admin")

'''
Admin routes for maintaining FRC Teams database table
'''
@bp.route("/maintenance_frc_teams")
def admin_maintenance_frc_teams():
    print(' > Rendering admin FRC teams maintenance page')
    team_data = db.session.query(Team.team_id, Team.team_name).all()
    return render_template('admin/maintenance_frc_teams.html', team_data=team_data)

@bp.route("/addto_frc_teams", methods=['POST'])
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
def admin_maintenance_active_events():
    print(' > Rendering admin active events maintenance page')
    event_data = db.session.query(Event.event_id, Event.event_code, Event.event_name, Event.event_date, Event.event_currently_active).all()
    return render_template('admin/maintenance_active_events.html', event_data=event_data)

@bp.route("/addto_active_events", methods=['POST'])
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
def update_events():
    event_id = request.args.get('event', 0)
    print(f' > Attempting to remove event {event_id}')
    db.session.query(Event).filter(Event.event_id == event_id).delete()
    db.session.commit()
    print(f' > Successfully removed event {event_id}')
    return redirect('/admin/maintenance_active_events')

@bp.route("/toggle_active_events")
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