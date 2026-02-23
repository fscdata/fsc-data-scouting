from flask import Blueprint, render_template

bp = Blueprint("main", __name__)

@bp.route("/")
def home_page():
    print(' > Rendering home page')
    return render_template('home_page.html')

@bp.route("/confirmed")
def confirmation_page():
    print(' > Rendering confirmation page')
    return render_template('confirm_page.html')
