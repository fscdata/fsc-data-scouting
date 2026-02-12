import os
from pprint import pprint

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from database_model import db, Team, MatchTeamData, MatchAllianceData, Calculation, convert_int_to_bool

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

## Database setup
SQLALCHEMY_DATABASE_URI = 'sqlite:///scouting.db' # os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///scouting.db')
##

## Flask app setup and routes
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
db.init_app(app)  # Initialize the SQLAlchemy database with the app

@app.route("/")
def scout_page():
    print(' > Rendering scout page')
    return render_template('scout_page.html')

@app.route("/confirmed")
def confirmation_page():
    print(' > Rendering confirmation page')
    return render_template('confirm_page.html')

@app.route('/scout/add_data', methods = ['POST'])
def add_new():
    if request.method == 'POST':
        print(request.form)

        # capture fields from form
        new_record_data = {
            'match_id': request.form.get('match_number'),
            'team_number': request.form.get('team_number'),
            'auto_fuel_score': request.form.get('auto_score_preload'), #TODO: fix form fields
            'auto_climb_try': int(request.form.get('auto_climb')),
            'teleop_fuel_score': request.form.get('teleop_score_fuel'),
            'teleop_climb_try': int(request.form.get('endgame_climb')),
            'match_tipped': 1 if 'tipped' in request.form else 0,
            'match_broke': 1 if 'broken' in request.form else 0,
        }

        # structure fields for database insertion
        processed_data = convert_int_to_bool(new_record_data)
        new_match_record = MatchTeamData(**processed_data)

        db.session.add(new_match_record)
        db.session.commit()

        print(f' > Successfully added scouting record to database')
        return redirect('/confirmed')
##

## Main execution of app
if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Create database tables as needed

    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))