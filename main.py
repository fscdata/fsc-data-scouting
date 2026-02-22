import os

from flask import Flask, render_template, request, redirect
from database_model import db, Team, MatchTeamData, MatchAllianceData, Calculation

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

## Database setup
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DB_URI', 'sqlite:///scouting.db')
##

## Flask app setup and routes
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
db.init_app(app)  # Initialize the SQLAlchemy database with the app

@app.route("/")
def home_page():
    print(' > Rendering home page')
    return render_template('home_page.html')

@app.route("/confirmed")
def confirmation_page():
    print(' > Rendering confirmation page')
    return render_template('confirm_page.html')

## scouting pages
@app.route("/scout/")
def scout_page():
    print(' > Rendering scout page')
    return render_template('scout_page.html')

@app.route('/scout/add_data', methods = ['POST'])
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
    
## admin pages
@app.route("/admin/maintenance_frc_teams")
def admin_maintenance_frc_teams():
    print(' > Rendering admin FRC teams maintenance page')
    team_data = db.session.query(Team.team_id, Team.team_name).all()
    return render_template('admin/maintenance_frc_teams.html', team_data=team_data)

@app.route("/admin/addto_frc_teams", methods=['POST'])
def add_new_team():
    if request.method == 'POST':
        print(request.form)
        form_dict = request.form.to_dict(flat=False)
        print(form_dict)

        # capture fields from form
        new_team_data = {
            'team_id': int(request.form.get('team_number', 0)),
            'team_name': request.form.get('team_name', ''),
        }

        # Filter out keys that are not in the Team model
        valid_keys = [c.name for c in Team.__table__.columns]
        filtered_data = {k: v for k, v in new_team_data.items() if k in valid_keys}

        new_team_record = Team(**filtered_data)

        db.session.add(new_team_record)
        db.session.commit()

        print(f' > Successfully added team to database')
        return redirect('/admin/maintenance_frc_teams')

@app.route("/admin/update_frc_teams")
def update_frc_teams():
    team_number = request.args.get('team', 0)
    print(f' > Attempting to remove team {team_number}')
    db.session.query(Team).filter(Team.team_id == team_number).delete()
    db.session.commit()
    print(f' > Successfully removed team {team_number}')
    return redirect('/admin/maintenance_frc_teams')

##

## Main execution of app
@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    db.create_all()
    print("Initialized the database.")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))