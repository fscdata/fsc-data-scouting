from flask import Blueprint, render_template
from database_model import db, MatchTeamData, MatchAllianceData, Calculation

bp = Blueprint("report", __name__, url_prefix="/report")

@bp.route("/")
def report_page():
    print(' > Rendering report page')
    match_data = db.session.query(MatchTeamData).all()
    return render_template('report/main_report_page.html', match_data=match_data)

@bp.route("/event")
def report_event_page():
    print(' > Rendering calculated data')
    event_match_data = db.session.query(MatchTeamData)\
        .join(MatchAllianceData, MatchTeamData.match_id == MatchAllianceData.match_id)\
        .filter(MatchAllianceData.event_id == 1).all()
    aggregate_data = db.session.query(Calculation)\
        .filter(Calculation.calculation_name == 'event_climb')\
        .first()
    print(f' > Aggregate data for event 1: {aggregate_data.calculation_value}')
    return render_template('report/main_report_page.html', match_data=event_match_data, aggregate_data=aggregate_data)
