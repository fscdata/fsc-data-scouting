from __future__ import print_function

import os
import urllib.parse

from flask import Flask
from flask_migrate import Migrate  # Add this import
from database_model import db, Event

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def get_db_uri():
    """Constructs the database URI from environment variables."""
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")

    # If the instance connection name is present, connect via the Cloud SQL Auth Proxy
    if instance_connection_name:
        parsed_pwd = urllib.parse.quote_plus(db_pass)
        # The format for a Unix socket connection is:
        # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?host=/cloudsql/<instance_connection_name>
        # Note the empty host before the slash and the host parameter in the query string.
        return (
            f"mysql+pymysql://{db_user}:{parsed_pwd}@/"
            f"{db_name}?unix_socket=/cloudsql/{instance_connection_name}"
        )

    # Fallback for local development (e.g., using a local SQLite database)
    return os.environ.get('SQLALCHEMY_DB_URI', 'sqlite:///scouting.db')

## Flask app setup and routes
app = Flask(__name__)
app.secret_key = 'frc2815'

this_folder = os.path.dirname(os.path.abspath(__file__))
current_score_db = os.path.join(this_folder, 'Hartsville_2025_Scouting.db')

base_api_url = 'https://www.thebluealliance.com/api/v3/match'
event_name = '2025sccmp' # '2025schar' # '2025sccha' # '2025sccmp'
event_abbreviations = {
    '2025schar' : 'Hartsville',
    '2025sccha' : 'N Charleston',
    '2025sccmp' : 'Anderson'
}
api_url = f'{base_api_url}/{event_name}'

headers = {
    'X-TBA-Auth-Key' : '0mJNhkqRGiHXLgRGkHccltHLMWEbCYPmhhjodOzdG5kSk7ISFf6JYIWwVD8fFWlC'
}

def db_query(sql, db_file):
    # print(sql)
    with sqlite3.connect(db_file) as conn:
        cur = conn.cursor()
        cur.execute(sql)
        data_returned = cur.fetchall()
    conn.close()
    return data_returned

def db_commit(sql, db_file):
    # print(sql)
    with sqlite3.connect(db_file) as conn:
        try:
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            msg = 'handled record successfully'
        except Exception as err:
            msg = f'error occurred: {err}'
            conn.rollback()
    conn.close()
    print(msg)
    return msg

def summarize(score_data):
    summary = {}
    for record in score_data:
        match = record[1]
        team = record[2]
        if match not in summary:
            summary[match] = []
        summary[match].append(team)
    return(summary)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))
            
def ping_blue_alliance():
    max_qual_match = 75
    # max_final_match = 3
    print(sql.api_collected_matches(event_name))
    max_match_so_far = db_query(sql.api_collected_matches(event_name), current_score_db)[0][0]
    # print(max_match_so_far)
    if max_match_so_far is None:
        min_qual_match = 1
    else:
        min_qual_match = int(max_match_so_far) + 1
    if max_qual_match - min_qual_match > 3:
        max_qual_match = min_qual_match + 1
    print(f'querying blue alliance API for match {min_qual_match} through {max_qual_match}')

    for match in range(min_qual_match, max_qual_match + 1):
        url = f'{api_url}_qm{match}'
        print(url)

        result = requests.get(url, headers=headers)
        if result.status_code == 200:
            score_result = result.json()
            rows = alliance_stats(score_result, match)
            for row in rows:
                print(row)
                add_data_msg = db_commit(sql.enter_new_climb_record(row), current_score_db)
                if 'error' in add_data_msg:
                    print(f'FAILED to add climb data report')
                else:
                    print(f'successfully added climb data report')

def alliance_stats(score_result, match_num):
    rows = []
    for alliance in ['blue', 'red']:
        for member in [1, 2, 3]:
            if 'score_breakdown' in score_result:
                print(score_result)
                if score_result['score_breakdown'] is not None:
                    team = score_result['alliances'][alliance]['team_keys'][member - 1].strip('frc')
                    endgame = score_result['score_breakdown'][alliance][f'endGameRobot{member}']
                    # row = [match_num, team, parked, shallow_climb, deep_climb]
                    if endgame == 'DeepCage':
                        row = [event_name, match_num, team, 1, 0, 1]
                    elif endgame == 'DeepCage':
                        row = [event_name, match_num, team, 1, 1, 0]
                    elif endgame == 'Parked':
                        row = [event_name, match_num, team, 1, 0, 0]
                    else:
                        row = [event_name, match_num, team, 0, 0, 0]
                    rows.append(row)
    return rows

sql = SQL_Templates()

all_teams = []

# print(get_db_uri())
app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()
db.init_app(app)  # Initialize the SQLAlchemy database with the app

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Register blueprints
from routes.main_routes import bp as main_bp
from routes.scout_routes import bp as scout_bp
from routes.report_routes import bp as report_bp
from routes.admin_routes import bp as admin_bp
from routes.info_routes import bp as info_bp

app.register_blueprint(main_bp)
app.register_blueprint(scout_bp)
app.register_blueprint(report_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(info_bp)
##

## Main execution of app
@app.cli.command("init-db")
def init_db():
    """Initialize the database with migrations (creates tables if needed, applies pending migrations)."""
    # Import model classes to register with SQLAlchemy metadata
    from database_model import Team, Event, MatchTeamData, MatchData, Calculation

    # Run inside the app context
    with app.app_context():
        try:
            # Create tables if they don't exist (for initial setup)
            db.create_all()
            print("Initialized the database (tables created if missing).")
        except Exception as e:
            print(f"Error initializing the database: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
