import os
import urllib.parse

from flask import Flask
from flask_basicauth import BasicAuth
# BasicAuth still imported here for type hints if needed (extensions initializes it)

from flask_migrate import Migrate  # Add this import
from database_model import db, Event

# import extension instances
from extensions import basic_auth, migrate

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

app.config['BASIC_AUTH_USERNAME'] = 'admin'
app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'default_password')
app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()

# initialize extensions with the app
db.init_app(app)
basic_auth.init_app(app)
migrate.init_app(app, db)

# Register blueprints
from routes.main_routes import bp as main_bp
from routes.scout_routes import bp as scout_bp
from routes.report_routes import bp as report_bp
from routes.admin_routes import bp as admin_bp
from routes.info_routes import bp as info_bp
from routes.pick_routes import bp as pick_bp

app.register_blueprint(main_bp)
app.register_blueprint(scout_bp)
app.register_blueprint(report_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(info_bp)
app.register_blueprint(pick_bp)
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
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))