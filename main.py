from __future__ import print_function

import os
import os.path
import random
import requests

# from io import BytesIO
# from matplotlib.figure import Figure

from flask import Flask
from flask import flash
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for
from flask import *
from werkzeug.utils import secure_filename
from io import StringIO
import datetime
import csv
import sqlite3

from sql_data import SQL_Templates

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

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

@app.route("/")
def scout_page():
    print('in scout page')
    return render_template('scout_page.html')

@app.route("/confirmed")
def confirmation_page():
    print('confirming data received')
    photo_list = ['alex', 'brooks', 'ella', 'jeremiah', 'tyra'] #CHANGE THESE TO CURRENT DRIVE TEAM
    photo_id = random.randrange(0, len(photo_list))
    photo_name = f'{photo_list[photo_id]}.png'
    return render_template(
        'confirm_page.html',
        photo_name=photo_name
    )

@app.route("/rejected")
def error_page():
    print('confirming data WAS NOT RECEIVED')
    return render_template('error_page.html')

@app.route("/admin/check_data")
def admin_check_data():
    score_data = db_query(sql.get_short_score, current_score_db)
    # print(score_data)
    match_summary = summarize(score_data)
    return render_template(
        'admin_light.html',
        score_data=score_data,
        match_summary=match_summary
    )

@app.route("/admin/full_data")
def admin_show_all_data():
    score_data = db_query(sql.get_full_score, current_score_db)
    # if len(score_data) > 0:
        # print(score_data[0])
    return render_template(
        'admin_export.html',
        score_data=score_data
    )

@app.route("/admin/climb_data")
def admin_show_climb_data():
    ping_blue_alliance()
    event_list = []
    summary_data = {}
    summary_deep_data = {}
    climb_data = db_query(sql.get_climb_score, current_score_db)
    if len(climb_data) > 0:
        for match in climb_data:
            event_name = event_abbreviations[match[0]]
            team_number = match[2]
            parked = match[3]
            shallow = match[4]
            deep = match[5]
            if event_name not in event_list:
                event_list.append(event_name)
            if event_name not in summary_data:
                summary_data[event_name] = {}
                summary_deep_data[event_name] = {}
            if team_number not in summary_data[event_name] and (parked > 0 or shallow > 0 or deep > 0):
                summary_data[event_name][team_number] = {}
                summary_data[event_name][team_number]['number'] = team_number
                summary_data[event_name][team_number]['times_parked'] = 0
                summary_data[event_name][team_number]['times_shallow'] = 0
                summary_data[event_name][team_number]['times_deep'] = 0
            if (parked > 0 or shallow > 0 or deep > 0):
                summary_data[event_name][team_number]['times_parked'] += parked
                summary_data[event_name][team_number]['times_shallow'] += shallow
                summary_data[event_name][team_number]['times_deep'] += deep
            if team_number not in summary_deep_data[event_name] and deep > 0:
                summary_deep_data[event_name][team_number] = {}
                summary_deep_data[event_name][team_number]['number'] = team_number
                summary_deep_data[event_name][team_number]['times_deep'] = 0
            if deep > 0:
                summary_deep_data[event_name][team_number]['times_deep'] += deep

    return render_template(
        'admin_climb.html',
        event_list=event_list,
        summary_deep_data=summary_deep_data,
        summary_data=summary_data,
        climb_data=climb_data
    )

@app.route("/view_team/<team_id>")
def admin_show_team_data(team_id):
    team_scores = db_query(sql.get_team_scores(team_id), current_score_db)
    for score in team_scores:
        print(score)
    return render_template(
        'view_team.html',
        team_scores=team_scores
    )

@app.route("/admin/export_to_csv", methods = ['POST', 'GET'])
def admin_export_data():
    min_match_id = request.form['min_match_id'] if 'min_match_id' in request.form else 0
    if not min_match_id:
        min_match_id = 0
    timestamp = datetime.datetime.now().strftime('%y%m%d-%H%M')
    export_filename = f'score_export_{timestamp}.csv'
    si = StringIO()
    cw = csv.writer(si)
    conn = sqlite3.connect(current_score_db)
    cursor = conn.cursor()
    sql_string = sql.get_csv_score(min_match_id)
    print(sql_string)
    cursor.execute(sql_string)
    cw.writerow([i[0] for i in cursor.description])
    cw.writerows(cursor)
    conn.close()
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={export_filename}"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/scout/add_data', methods = ['POST', 'GET'])
def add_new():
    if request.method == 'POST':
        print(request.form)

        scout_data = {
            'team_number': request.form['team_number'],
            'match_number': request.form['match_number'],
            'notes': request.form['notes'],

            #AUTO-AUTO-AUTO
            'start_position': request.form['start_position'],
            'auto_leave': 1 if 'auto_leave' in request.form else 0,
            'auto_score_preload': 1 if 'auto_score_preload' in request.form else 0,
            'auto_reefL1': request.form['auto_reefL1'],
            'auto_reefL2': request.form['auto_reefL2'],
            'auto_reefL3': request.form['auto_reefL3'],
            'auto_reefL4': request.form['auto_reefL4'],
            'auto_algae_knockoff': request.form['auto_algae_knockoff'],
            'auto_score_algae_net': request.form['auto_score_algae_net'],
            'auto_score_algae_proc': request.form['auto_score_algae_proc'],
            'auto_astop': 1 if 'auto_astop' in request.form else 0,
            'auto_failed': 1 if 'auto_failed' in request.form else 0,

            #TELEOP-TELEOP-TELEOP
            'teleop_score_algae_net': request.form['teleop_score_algae_net'],
            'teleop_score_algae_proc': request.form['teleop_score_algae_proc'],
            'teleop_algae_knockoff': request.form['teleop_algae_knockoff'],
            'teleop_reefL1': request.form['teleop_reefL1'],
            'teleop_reefL2': request.form['teleop_reefL2'],
            'teleop_reefL3': request.form['teleop_reefL3'],
            'teleop_reefL4': request.form['teleop_reefL4'],
            'teleop_coral_miss': request.form['teleop_coral_miss'],

            # ENDGAME-ENDGAME-ENDGAME
            'parked': 1 if 'parked' in request.form else 0,

            # OTHER INFO
            'coopertition': 1 if 'coopertition' in request.form else 0,
            'RP_auto': 1 if 'RP_auto' in request.form else 0,
            'RP_coral': 1 if 'RP_coral' in request.form else 0,
            'RP_barge': 1 if 'RP_barge' in request.form else 0,
            'tipped': 1 if 'tipped' in request.form else 0,
            'broken': 1 if 'broken' in request.form else 0,
            'REDcarded': 1 if 'REDcarded' in request.form else 0,
            'YELLOWcarded': 1 if 'YELLOWcarded' in request.form else 0,
            'TECHfoul': 1 if 'TECHfoul' in request.form else 0
        }

        add_data_msg = db_commit(sql.enter_new_scout_record(scout_data), current_score_db)
        if 'error' in add_data_msg:
            print(f'FAILED to add scouting report')
            return redirect('/rejected')
        else:
            print(f'successfully added scouting report')
            return redirect('/confirmed')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)