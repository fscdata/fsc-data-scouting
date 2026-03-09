from flask import Blueprint, render_template, request, redirect

bp = Blueprint("info", __name__, url_prefix="/info")

'''
Info routes for info pages
'''
@bp.route("/")
def info_general():
    print(' > Rendering general info page')
    return render_template('info/info_general.html')

@bp.route("/dictionary")
def info_dictionary():
    print(' > Rendering info dictionary page')
    return render_template('info/info_dictionary.html')

@bp.route("/how-to-scout")
def info_how_to_scout():
    print(' > Rendering info how to scout page')
    return render_template('info/info_how_to_scout.html')