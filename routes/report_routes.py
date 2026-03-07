import csv
from datetime import datetime
from io import StringIO
from flask import Blueprint, make_response, render_template, request
from database_model import db, Team, MatchTeamData, MatchData, Event, Calculation

bp = Blueprint("report", __name__, url_prefix="/report")

def calculate_climb_stats(MatchTeamData):
    print(f'> Calculating climb stats for team')
    # do some math to calculate average climb level and success rate for the team
    team_climb_stats = {
        'match_count': 0,
        'auto_climb_try': 0,
        'auto_climbed': 0,
        'endgame_climb_try': 0,
        'endgame_climbed': 0
    }
    for match in MatchTeamData:
        team_climb_stats['match_count'] += 1
        prev_auto_climb_try = team_climb_stats['auto_climb_try']
        prev_auto_climbed = team_climb_stats['auto_climbed']
        prev_endgame_climb_try = team_climb_stats['endgame_climb_try']
        prev_endgame_climbed = team_climb_stats['endgame_climbed']
        if match.auto_climb_try:
            team_climb_stats['auto_climb_try'] = prev_auto_climb_try + 1
            if match.auto_climbed != 'None':
                team_climb_stats['auto_climbed'] = prev_auto_climbed + 1
        if match.endgame_climb_try:
            team_climb_stats['endgame_climb_try'] = prev_endgame_climb_try + 1
            if match.endgame_climb_level != 'None':
                team_climb_stats['endgame_climbed'] = prev_endgame_climbed + 1

    if team_climb_stats['auto_climb_try'] > 0:
        successes = team_climb_stats['auto_climbed']
        tries = team_climb_stats['auto_climb_try']
        team_climb_stats['auto_climb_success'] = successes / tries
    else:
        team_climb_stats['auto_climb_success'] = 'Not applicable'
    if team_climb_stats['endgame_climb_try'] > 0:
        successes = team_climb_stats['endgame_climbed']
        tries = team_climb_stats['endgame_climb_try']
        team_climb_stats['endgame_climb_success'] = successes / tries
    else:
        team_climb_stats['endgame_climb_success'] = 'Not applicable'
    return team_climb_stats

@bp.route("/")
def report_landing_page():
    print(' > Rendering report landing page')
    return render_template('report/main_report_page.html')

@bp.route("/export/")
def export_data_page():
    print(' > Rendering CSV export page')
    event_list = db.session\
        .query(
            Event.event_id,
            Event.event_code,
            Event.event_currently_active)\
        .all()
    return render_template(
        'report/export_page.html',
        event_list=event_list)


@bp.route("/export/generate_CSV", methods = ['POST', 'GET'])
def deliver_csv_file():
    if request.method == 'POST':
        if request.remote_addr:
            print(f'Captured IP address: {request.remote_addr}')
        else:
            print('No IP address found in request')

        min_match_id = int(request.form.get('min_match_id', 0))
        event_id = request.form.get('event_id')
        timestamp = datetime.now().strftime('%y%m%d-%H%M')
        export_filename = f'fscdata_export_{timestamp}.csv'
        si = StringIO()
        cw = csv.writer(si)

        all_match_data = db.session\
            .query(MatchTeamData)\
            .filter(
                MatchTeamData.event_id == event_id,
                MatchTeamData.match_number >= min_match_id,
                MatchTeamData.record_hidden == False)\
            .all()

        print(f' > Exporting {len(all_match_data)} records to CSV file {export_filename}')
        if not all_match_data:
            error_message = 'No match data has been scouted yet, the CSV is empty. Please try again later.'
            print(f' ! {error_message}')
            return render_template('error.html', error_message=error_message)
        else:
            # drop metadata columns that aren't needed for export
            columns_to_exclude = ['event_id', 'record_ip_address', 'record_hidden']
            columns = [col for col in all_match_data[0].__table__.columns if col.name not in columns_to_exclude]
            # print(f' > Column names: {[col.name for col in columns]}')

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
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()
    active_event_name = db.session\
        .query(Event.event_name)\
        .filter(Event.event_currently_active == 1)\
        .scalar()
    team_number = request.args.get('number')
    if team_number is None:
        print(f' > Rendering all teams with links')
        print(active_event_id)
        print(active_event_name)
        team_summary_data = db.session\
            .query(
                MatchTeamData.team_number,
                Team.team_name)\
            .filter(
                MatchTeamData.event_id == active_event_id,
                MatchTeamData.record_hidden == False)\
            .join(Team, MatchTeamData.team_number == Team.team_id)\
            .group_by(MatchTeamData.team_number)\
            .all()
        team_stats = {
            team_data[0]:
                {'team_name': team_data[1],
                 'match_count': 0,
                 'total_fuel': 0,
                 'avg_fuel': 0}
                for team_data in team_summary_data}
        team_performance_data = db.session\
            .query(
                MatchTeamData.team_number,
                MatchTeamData.auto_fuel_score,
                MatchTeamData.teleop_fuel_score
            )\
            .filter(MatchTeamData.event_id == active_event_id, MatchTeamData.record_hidden == False)\
            .join(Team, MatchTeamData.team_number == Team.team_id)\
            .all()

        for match_record in team_performance_data:
            team_stats[match_record.team_number]['match_count'] += 1
            team_stats[match_record.team_number]['total_fuel'] += (match_record.auto_fuel_score + match_record.teleop_fuel_score)
        for team in team_stats:
            if team_stats[team]['match_count'] > 0:
                team_stats[team]['avg_fuel'] = round(
                    team_stats[team]['total_fuel'] / team_stats[team]['match_count'],
                    2)

        return render_template(
            'report/main_teams_page.html',
            team_stats=team_stats,
            active_event_name=active_event_name)
    else:
        print(f' > Rendering team report page for team number {team_number}')
        team_records = db.session\
            .query(MatchTeamData)\
            .filter(
                MatchTeamData.team_number == team_number,
                MatchTeamData.event_id == active_event_id,
                MatchTeamData.record_hidden == False)\
            .all()
        print(team_records)
        team_climb_stats = calculate_climb_stats(team_records)
        return render_template(
            'report/team_report_page.html',
            team_records=team_records,
            team_climb_stats=team_climb_stats)

@bp.route("/raw/", methods = ['POST', 'GET'])
def report_page():
    print(' > Rendering report page')
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()

    display_event_id = request.form.get('event_id')
    if not display_event_id:
        print(' > No event ID provided, defaulting to active event')
        display_event_id = active_event_id

    display_event_name = db.session.query(Event.event_name).filter(Event.event_id == display_event_id).scalar()

    event_list = db.session\
        .query(Event.event_id,
               Event.event_code,
               Event.event_currently_active)\
        .all()

    all_match_data = db.session\
        .query(MatchTeamData)\
        .filter(
            MatchTeamData.event_id == display_event_id,
            MatchTeamData.record_hidden == False)\
        .all()
    return render_template(
        'report/report_raw_matchdata.html',
        match_data=all_match_data,
        event_list=event_list,
        display_event_name=display_event_name)