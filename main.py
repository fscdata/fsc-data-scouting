import os
from dotenv import load_dotenv

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

load_dotenv()  # Loads environment variables from .env file

# Accessing the variables
database_uri = os.getenv('SQLALCHEMY_DATABASE_URI')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.route("/")
def scout_page():
    print(' > in scout page')
    return f"Hello, World! Database instance: {database_uri}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))