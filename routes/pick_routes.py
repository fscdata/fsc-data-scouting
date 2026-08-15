from flask import Blueprint, render_template
from database_model import db, Team, MatchTeamData, MatchData, Event, Calculation
from routes.report_routes import pull_archived_stats

bp = Blueprint("pick", __name__, url_prefix="/pick-list")

@bp.route("/")
def pick_landing_page():
    print(' > Rendering pick landing page')

    event_data = db.session\
        .query(Event.event_id,
               Event.event_name)\
        .filter(Event.event_currently_active == 1)\
        .first()
    active_event_id = event_data.event_id
    active_event_name = event_data.event_name

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
        .filter(MatchTeamData.event_id == active_event_id, MatchTeamData.record_hidden == False)\
        .join(Team, MatchTeamData.team_number == Team.team_id)\
        .all()

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
    full_team_stats = pull_archived_stats(team_stats, active_event_id)
    
    return render_template('pick_list/main_pick_page.html', 
                            team_stats=full_team_stats,
                            active_event_name=active_event_name)