import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

@app.route("/")
def scout_page():
    print(' > in scout page')
    instance = os.environ.get("fsc-db-dev-instance", "INSTANCE Not Found")[:5]
    username = os.environ.get("fsc-db-dev-username", "USERNAME Not Found")[:5]
    password = os.environ.get("fsc-db-dev-password", "PASSWORD Not Found")[:5]
    public_ip = os.environ.get("fsc-db-dev-public-ip", "PUBLIC_IP Not Found")[:5]
    print(instance, "...")
    print(username, "...")
    print(password, "...")
    print(public_ip, "...")
    return f"Hello, World! Database instance: {instance}, Username: {username}, Password: {password}, Public IP: {public_ip}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))