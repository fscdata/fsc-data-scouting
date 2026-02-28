import csv
from datetime import datetime
from io import StringIO
from flask import Blueprint, make_response, render_template, request
from database_model import db, MatchTeamData, MatchData, Event, Calculation

bp = Blueprint("report", __name__, url_prefix="/report")

@bp.route("/")
def report_landing_page():
    print(' > Rendering report landing page')
    return render_template('report/main_report_page.html')

@bp.route("/export/")
def export_data_page():
    print(' > Rendering CSV export page')
    event_list = db.session.query(Event.event_id, Event.event_code, Event.event_currently_active).all()
    return render_template(
        'report/export_page.html',
        event_list=event_list)


@bp.route("/export/generate_CSV", methods = ['POST', 'GET'])
def deliver_csv_file():
    if request.method == 'POST':
        min_match_id = int(request.form.get('min_match_id', 0))
        event_id = request.form.get('event_id')
        timestamp = datetime.now().strftime('%y%m%d-%H%M')
        export_filename = f'fscdata_export_{timestamp}.csv'
        si = StringIO()
        cw = csv.writer(si)

        all_match_data = db.session\
            .query(MatchTeamData)\
            .filter(MatchTeamData.event_id == event_id, MatchTeamData.match_id >= min_match_id).all()
        
        print(all_match_data)
        
        print(f' > Exporting {len(all_match_data)} records to CSV file {export_filename}')
        if not all_match_data:
            print(' > No data to export')
        else:
            columns = [col for col in all_match_data[0].__table__.columns if col.name != 'match_team_id']
            print(f' > Column names: {[col.name for col in columns]}')

            cw.writerow([col.name for col in columns])
            cw.writerows([tuple(getattr(row, col.name) for col in columns) for row in all_match_data])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename={export_filename}"
        output.headers["Content-type"] = "text/csv"
        return output

@bp.route("/event")
def report_event_page():
    print(' > Rendering calculated data')
    event_match_data = db.session\
        .query(MatchTeamData)\
        .join(MatchData, MatchTeamData.match_id == MatchData.match_id)\
        .filter(MatchData.event_id == 1).all()
    aggregate_data = db.session.query(Calculation)\
        .filter(Calculation.calculation_name == 'event_climb')\
        .first()
    print(f' > Aggregate data for event 1: {aggregate_data.calculation_value}')
    return render_template(
        'report/main_report_page.html',
        match_data=event_match_data,
        aggregate_data=aggregate_data)

@bp.route("/raw/", methods = ['POST', 'GET'])
def report_page():
    print(' > Rendering report page')
    active_event_id = db.session.query(Event.event_id).filter(Event.event_currently_active == 1).scalar()
    
    display_event_id = request.form.get('event_id')
    if not display_event_id:
        print(' > No event ID provided, defaulting to active event')
        display_event_id = active_event_id

    display_event_name = db.session.query(Event.event_name).filter(Event.event_id == display_event_id).scalar()

    event_list = db.session.query(Event.event_id, Event.event_code, Event.event_currently_active).all()

    all_match_data = db.session\
        .query(MatchTeamData)\
        .filter(MatchTeamData.event_id == display_event_id)\
        .all()
    return render_template(
        'report/report_raw_matchdata.html',
        match_data=all_match_data,
        event_list=event_list,
        display_event_name=display_event_name)

@bp.route("/match")
def report_match_page():
    print(' > Rendering match report page')
    match_data = db.session\
        .query(MatchTeamData)\
        .filter(MatchTeamData.match_id == 5).all()
    return render_template(
        'report/match_report_page.html',
        match_data=match_data)

@bp.route("/team")
def report_team_page():
    print(' > Rendering team report page')
    team = db.session\
        .query(MatchTeamData)\
        .filter(MatchTeamData.match_id == 5).all()
    aggregate_data = db.session.query(Calculation)\
        .filter(Calculation.calculation_name == 'event_climb')\
        .first()
    return render_template(
        'report/team_report_page.html',
        team=team,
        aggregate_data=aggregate_data)