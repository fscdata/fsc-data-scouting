import base64
from collections import defaultdict
from matplotlib.figure import Figure
import csv
from datetime import datetime
from io import BytesIO, StringIO
from flask import Blueprint, make_response, render_template, request
from database_model import db, Team, MatchTeamData, Event, Calculation

bp = Blueprint("report", __name__, url_prefix="/report")

def pull_archived_stats(team_stats, event_id):
    """Merge archived OPR/DPR/CCWM/rank/EPA from the Calculation table into team_stats.

    Reads whatever cron/calculate_report_data.py last saved instead of calling
    TBA/Statbotics live, so report pages don't hit those APIs on every view.
    """
    archived_rows = db.session\
        .query(Calculation)\
        .filter(
            Calculation.event_id == event_id,
            Calculation.team_number.in_(team_stats.keys()))\
        .all()
    archived_by_team = {row.team_number: row for row in archived_rows}

    for team in team_stats:
        row = archived_by_team.get(team)
        team_stats[team]['opr'] = row.event_opr if row and row.event_opr is not None else 'N/A'
        team_stats[team]['dpr'] = row.event_dpr if row and row.event_dpr is not None else 'N/A'
        team_stats[team]['ccwm'] = row.event_ccwm if row and row.event_ccwm is not None else 'N/A'
        team_stats[team]['tba_rank'] = row.tba_rank if row and row.tba_rank is not None else 'N/A'
        team_stats[team]['epa'] = row.event_epa if row and row.event_epa is not None else 'N/A'

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

def build_event_team_stats(event_id, include_all_teams=False):
    if include_all_teams:
        team_summary_data = db.session\
            .query(Team.team_id, Team.team_name)\
            .order_by(Team.team_id)\
            .all()
    else:
        team_summary_data = db.session\
            .query(
                MatchTeamData.team_number,
                Team.team_name)\
            .filter(
                MatchTeamData.event_id == event_id,
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
             'human_fuel': 0,
             'avg_human': 0,
             'opr': 0,
             'dpr': 0,
             'ccwm': 0,
             'tba_rank': 0,
             'epa': 0}
            for team_data in team_summary_data}

    team_performance_data = db.session\
        .query(
            MatchTeamData.team_number,
            MatchTeamData.auto_fuel_score,
            MatchTeamData.teleop_fuel_score,
            MatchTeamData.alliance_human_fuel
        )\
        .filter(MatchTeamData.event_id == event_id, MatchTeamData.record_hidden == False)\
        .join(Team, MatchTeamData.team_number == Team.team_id)\
        .all()

    for match_record in team_performance_data:
        if match_record.team_number not in team_stats:
            continue
        team_stats[match_record.team_number]['match_count'] += 1
        team_stats[match_record.team_number]['total_fuel'] += (match_record.auto_fuel_score + match_record.teleop_fuel_score)
        if match_record.alliance_human_fuel is not None:
            team_stats[match_record.team_number]['human_fuel'] += match_record.alliance_human_fuel
    for team in team_stats:
        if team_stats[team]['match_count'] > 0:
            team_stats[team]['avg_fuel'] = round(
                team_stats[team]['total_fuel'] / team_stats[team]['match_count'],
                2)
            team_stats[team]['avg_human'] = round(
                (team_stats[team]['human_fuel'] / team_stats[team]['match_count']) / 3,
                2)
    return team_stats

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
            columns_to_exclude = ['event_id', 'calc_auto_score', 'calc_teleop_score', 'record_ip_address', 'record_hidden']
            columns = [col for col in all_match_data[0].__table__.columns if col.name not in columns_to_exclude]
            # print(f' > Column names: {[col.name for col in columns]}')

            cw.writerow([col.name for col in columns])
            cw.writerows([tuple(getattr(row, col.name) for col in columns) for row in all_match_data])

            output = make_response(si.getvalue())
            output.headers["Content-Disposition"] = f"attachment; filename={export_filename}"
            output.headers["Content-type"] = "text/csv"
            return output

@bp.route("/event/<int:event_id>")
def report_event_page(event_id):
    print(f' > Rendering team stats for event {event_id}')
    event_data = db.session\
        .query(Event)\
        .filter(Event.event_id == event_id)\
        .first()
    if event_data is None:
        return render_template(
            'error.html',
            error_message=f'No event found with ID {event_id}.')

    team_stats = build_event_team_stats(event_id, include_all_teams=False)
    team_stats = pull_archived_stats(team_stats, event_id)

    return render_template(
        'report/event_teams_page.html',
        event=event_data,
        team_stats=team_stats)

#TODO: what was this for?
# @bp.route("/match")
# def report_match_page():
#     print(' > Rendering match report page')
#     match_data = db.session\
#         .query(MatchTeamData)\
#         .filter(MatchTeamData.match_id == 5).all()
#     return render_template(
#         'report/match_report_page.html',
#         match_data=match_data)

@bp.route("/team")
def report_team_page():
    event_data = db.session\
        .query(Event.event_id,
               Event.event_name)\
        .filter(Event.event_currently_active == 1)\
        .first()
    if event_data:
        active_event_id = event_data.event_id
        active_event_name = event_data.event_name
    else:
        active_event_id = active_event_name = None

    team_number = request.args.get('number')
    if team_number is None:
        print(f' > Rendering all teams with links')
        team_stats = build_event_team_stats(active_event_id, include_all_teams=True)
        if active_event_id:
            team_stats = pull_archived_stats(team_stats, active_event_id)

        all_events = db.session\
            .query(
                Event.event_id,
                Event.event_name,
                Event.event_code,
                Event.event_year,
                Event.event_currently_active)\
            .order_by(Event.event_year.desc(), Event.event_id.desc())\
            .all()
        events_by_year = {}
        for event in all_events:
            events_by_year.setdefault(event.event_year, []).append(event)

        return render_template(
            'report/main_teams_page.html',
            team_stats=team_stats,
            active_event_name=active_event_name,
            events_by_year=events_by_year)
    else:
        print(f' > Rendering team report page for team number {team_number}')
        events_for_team = db.session\
            .query(MatchTeamData.event_id)\
            .distinct()\
            .filter(MatchTeamData.team_number == team_number,
                MatchTeamData.record_hidden == False)\
            .order_by(MatchTeamData.event_id.desc())\
            .all()
        print(events_for_team)
        if len(events_for_team) == 0:
            return render_template(
                'error.html',
                error_message=f'No scouting data found for team {team_number} in any event.')
        else:
            team_event_list = [event_id[0] for event_id in events_for_team]
            print(team_event_list)
            all_team_events = {}
            for event_id in team_event_list:
                print(event_id)
                event_info = db.session\
                    .query(Event.event_name, Event.event_year, Event.event_code, Event.event_date)\
                    .filter(Event.event_id == event_id)\
                    .first()
                event_name = event_info.event_name

                event_records = db.session\
                    .query(MatchTeamData)\
                    .filter(
                        MatchTeamData.team_number == team_number,
                        MatchTeamData.event_id == event_id,
                        MatchTeamData.record_hidden == False)\
                    .all()
                print(event_records)
                
                all_event_records = db.session\
                    .query(MatchTeamData)\
                    .filter(
                        MatchTeamData.event_id == event_id,
                        MatchTeamData.record_hidden == False)\
                    .all()
                team_climb_stats = calculate_climb_stats(event_records)

                team_summary_data = db.session\
                    .query(
                        MatchTeamData.team_number,
                        Team.team_name)\
                    .filter(
                        MatchTeamData.event_id == event_id,
                        MatchTeamData.record_hidden == False,
                        MatchTeamData.team_number == team_number)\
                    .join(Team, MatchTeamData.team_number == Team.team_id)\
                    .group_by(MatchTeamData.team_number)\
                    .all()
                print(team_summary_data)
                team_stats = {
                    team_data[0]:
                        {'team_name': team_data[1],
                        'match_count': 0,
                        'total_fuel': 0,
                        'avg_fuel': 0,
                        'human_fuel': 0,
                        'avg_human': 0,
                        'opr': 0,
                        'dpr': 0,
                        'ccwm': 0,
                        'tba_rank': 0,
                        'epa': 0}
                        for team_data in team_summary_data}
                print(team_stats)
                team_performance_data = db.session\
                    .query(
                        MatchTeamData.team_number,
                        MatchTeamData.auto_fuel_score,
                        MatchTeamData.teleop_fuel_score,
                        MatchTeamData.alliance_human_fuel
                    )\
                    .filter(
                        MatchTeamData.event_id == event_id,
                        MatchTeamData.record_hidden == False,
                        MatchTeamData.team_number == team_number)\
                    .join(Team, MatchTeamData.team_number == Team.team_id)\
                    .all()
                print(team_performance_data)

                for match_record in team_performance_data:
                    team_stats[match_record.team_number]['match_count'] += 1
                    team_stats[match_record.team_number]['total_fuel'] += (match_record.auto_fuel_score + match_record.teleop_fuel_score)
                    if match_record.alliance_human_fuel is not None:
                        team_stats[match_record.team_number]['human_fuel'] += match_record.alliance_human_fuel
                for team in team_stats:
                    if team_stats[team]['match_count'] > 0:
                        team_stats[team]['avg_fuel'] = round(
                            team_stats[team]['total_fuel'] / team_stats[team]['match_count'],
                            2)
                        team_stats[team]['avg_human'] = round(
                            (team_stats[team]['human_fuel'] / team_stats[team]['match_count']) / 3,
                            2)
                full_team_stats = pull_archived_stats(team_stats, event_id)
                # print(full_team_stats)

                matches_by_team = {}
                for r in all_event_records:
                    matches_by_team.setdefault(r.team_number, []).append(r)
                for team in matches_by_team:
                    matches_by_team[team].sort(key=lambda r: r.match_number)

                max_matches = max(len(matches) for matches in matches_by_team.values())
                event_average_scored = []
                for i in range(max_matches):
                    scores_at_index = []
                    for matches in matches_by_team.values():
                        if i < len(matches):
                            scores_at_index.append(matches[i].auto_fuel_score + matches[i].teleop_fuel_score)
                    event_average_scored.append(sum(scores_at_index) / len(scores_at_index))

                fuel_scored = []
                matches_played = []
                count = 0
                
                for record in event_records:
                    count += 1
                    fuel_scored.append(record.auto_fuel_score+record.teleop_fuel_score)
                    matches_played.append(count)
                
                # Generate figure without using pyplot
                fig = Figure()
                ax = fig.subplots()
                ax.bar(matches_played, fuel_scored)
                ax.plot(matches_played, event_average_scored[:len(matches_played)], color="red", marker="o", label="Event avg (per match)")
                
                for x, y in zip(matches_played, event_average_scored[:len(matches_played)]):
                    ax.annotate(
                        f"{y:.1f}",
                        (x, y),
                        textcoords="offset points",
                        xytext=(0, 8),  # nudge the label up 8 points so it doesn't sit on top of the dot
                        ha="center",
                        fontsize=8,
                        color="red"
                    )
                
                ax.set_xlabel("Matches Played")
                ax.set_ylabel("Fuel Scored")
                ax.legend()

                # Save to memory buffer
                buf = BytesIO()
                fig.savefig(buf, format="png")

                # Encode to Base64 string
                plot_url = base64.b64encode(buf.getbuffer()).decode("ascii")
            
                print(event_records)
                print(event_name)
                all_team_events[event_name] = {}
                all_team_events[event_name]['stats'] = full_team_stats
                all_team_events[event_name]['event_records'] = event_records
                all_team_events[event_name]['score_plot'] = plot_url
                all_team_events[event_name]['event_date'] = event_info.event_date

            return render_template(
                'report/team_report_page.html',
                team_number=team_number,
                # team_records=event_records,
                all_team_events=all_team_events)
                # team_avg_stats=full_team_stats,
                # team_climb_stats=team_climb_stats,
                # plot_url=plot_url)

@bp.route("/raw/", methods = ['POST', 'GET'])
def report_page():
    print(' > Rendering report page')
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()

    display_event_id = request.values.get('event_id')
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