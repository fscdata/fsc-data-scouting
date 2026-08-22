from flask import Blueprint, render_template
from database_model import db, Event

bp = Blueprint("main", __name__)

@bp.route("/")
def home_page():
    active_event_id = db.session\
        .query(Event.event_id)\
        .filter(Event.event_currently_active == 1)\
        .scalar()
    
    print(' > Rendering home page')
    return render_template(
        'home_page.html',
        active_event_id=active_event_id)

@bp.route("/confirmed")
def confirmation_page():
    print(' > Rendering confirmation page')
    return render_template('confirm_page.html')
