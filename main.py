import os
import urllib.parse

from flask import Flask
from database_model import db

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

# print(get_db_uri())
app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()
db.init_app(app)  # Initialize the SQLAlchemy database with the app

# Register blueprints
from routes.main_routes import bp as main_bp
from routes.scout_routes import bp as scout_bp
from routes.report_routes import bp as report_bp
from routes.admin_routes import bp as admin_bp

app.register_blueprint(main_bp)
app.register_blueprint(scout_bp)
app.register_blueprint(report_bp)
app.register_blueprint(admin_bp)
##

## Main execution of app
@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    # import model classes to register with SQLAlchemy metadata
    from database_model import Team, Event, MatchTeamData, MatchAllianceData, Calculation

    # Run create_all inside the app context to ensure proper configuration
    with app.app_context():
        try:
            db.create_all()
            print("Initialized the database.")
        except Exception as e:
            print(f"Error initializing the database: {e}")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))