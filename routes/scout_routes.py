from flask import Blueprint, render_template, request, redirect
from database_model import db, MatchTeamData

bp = Blueprint("scout", __name__, url_prefix="/scout")

@bp.route("/")
def scout_page():
    print(' > Rendering scout page')
    return render_template('scout_page.html')

@bp.route('/add_data', methods=['POST'])
def add_new():
    if request.method == 'POST':
        print(request.form)
        form_dict = request.form.to_dict(flat=False)
        print(form_dict)

        # capture fields from form
        new_record_data = {
            'match_id': int(request.form.get('match_number', 0)),
            'team_number': int(request.form.get('team_number', 0)),
            'auto_fuel_score': int(request.form.get('auto_score_preload', 0)),
            'auto_climb_try': bool(int(request.form.get('auto_climb', 0))),
            'teleop_fuel_score': int(request.form.get('teleop_score_fuel', 0)),
            'teleop_climb_try': bool(int(request.form.get('endgame_climb', 0))),
            'match_tipped': 'tipped' in request.form,
            'match_broke': 'broken' in request.form,
        }

        # Filter out keys that are not in the MatchTeamData model
        valid_keys = [c.name for c in MatchTeamData.__table__.columns]
        filtered_data = {k: v for k, v in new_record_data.items() if k in valid_keys}

        new_match_record = MatchTeamData(**filtered_data)

        db.session.add(new_match_record)
        db.session.commit()

        print(f' > Successfully added scouting record to database')
        return redirect('/confirmed')
