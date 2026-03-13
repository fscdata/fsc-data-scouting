import os
import requests
import csv
from datetime import datetime
from io import StringIO
from flask import Blueprint, make_response, render_template, request
from database_model import db, Team, MatchTeamData, MatchData, Event, Calculation

bp = Blueprint("report", __name__, url_prefix="/report")

def pull_TBA_stats(team_stats, event_key='2026schop'):
    tba_api_key = os.environ.get('TBA_API_KEY')

    base_tba_url = 'https://www.thebluealliance.com/api/v3'

    if not tba_api_key:
        print("Error: Blue Alliance API credentials not found in environment variables.")
        exit(1)
    headers = {
        'X-TBA-Auth-Key' : tba_api_key
    }

    stats_endpoint_url = f'{base_tba_url}/event/{event_key}/oprs'
    rankings_endpoint_url = f'{base_tba_url}/event/{event_key}/rankings'

    try:
        event_stats_response = requests.get(stats_endpoint_url, headers=headers)
        if not event_stats_response.status_code == 200:
            print(f'Status Code: {event_stats_response.status_code}')
            print(' !!! api error')
            for team in team_stats:
                team_stats[team]['opr'] = 'TBA N/A'
                team_stats[team]['dpr'] = 'TBA N/A'
                team_stats[team]['ccwm'] = 'TBA N/A'
        else:
            event_stats_data = event_stats_response.json()

            tba_opr = {
                team[3:]: round(event_stats_data['oprs'][team], 2)
                for team in event_stats_data['oprs']}
            tba_dpr = {
                team[3:]: round(event_stats_data['dprs'][team], 2)
                for team in event_stats_data['dprs']}
            tba_ccwm = {
                team[3:]: round(event_stats_data['ccwms'][team], 2)
                for team in event_stats_data['ccwms']}

            for team in team_stats:
                team_stats[team]['opr'] = tba_opr[f'{team}']
                team_stats[team]['dpr'] = tba_dpr[f'{team}']
                team_stats[team]['ccwm'] = tba_ccwm[f'{team}']
    except:
        print(' !!! api error')
        for team in team_stats:
            team_stats[team]['opr'] = 'TBA N/A'
            team_stats[team]['dpr'] = 'TBA N/A'
            team_stats[team]['ccwm'] = 'TBA N/A'

    try:
        rankings_response = requests.get(rankings_endpoint_url, headers=headers)
        print(f'Status Code: {rankings_response.status_code}')
        if not rankings_response.status_code == 200:
            print('api error')
            for team in team_stats:
                team_stats[team]['tba_rank'] = 'TBA N/A'
        else:
            rankings_data = rankings_response.json()
            tba_rank = {
                team['team_key'][3:]: team['rank']
                for team in rankings_data['rankings']}
            for team in team_stats:
                team_stats[team]['tba_rank'] = tba_rank[f'{team}']
    except:
        print(' !!! api error')
        for team in team_stats:
            team_stats[team]['tba_rank'] = 'TBA N/A'

    return team_stats

def calculate_human_stats(MatchData, MatchTeamData):
    print('> Calculating human player stats for team')
    team_human_stats = {
        'match_count': 0,
        'total human': 0,
    }
    for match in MatchTeamData:
        pass


def calculate_climb_stats(MatchTeamData):
    print(f'> Calculating climb stats for team')
    # do some math to calculate average climb level and success rate for the team
    team_climb_stats = {
        'match_count': 0,
        'auto_climb_try': 0,
        'auto_climbed': 0,
        'endgame_climb_try': 0,
        'endgame_climbed': 0,
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
    event_data = db.session\
        .query(Event.event_id,
               Event.event_name,
               Event.event_code)\
        .filter(Event.event_currently_active == 1)\
        .first()
    active_event_id = event_data.event_id
    active_event_name = event_data.event_name
    active_event_code = event_data.event_code

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
                 'avg_fuel': 0,
                 'opr': 0,
                 'dpr': 0,
                 'ccwm': 0,
                 'tba_rank': 0}
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
        full_team_stats = pull_TBA_stats(team_stats, active_event_code.lower())

        return render_template(
            'report/main_teams_page.html',
            team_stats=full_team_stats,
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
        .order_by(
            MatchTeamData.match_number,
            MatchTeamData.team_number)\
        .all()
    return render_template(
        'report/report_raw_matchdata.html',
        match_data=all_match_data,
        event_list=event_list,
        display_event_name=display_event_name)