import sqlite3
import sys

try:
    record_id = sys.argv[1]

    conn = sqlite3.connect('Hartsville_2025_Scouting.db') #formerly 2024

    match_results_drop_row = f"DELETE FROM results WHERE report_id = '{record_id}';"

    print(match_results_drop_row)
    cur = conn.cursor()
    cur.execute(match_results_drop_row)
    data_returned = cur.fetchall()
    conn.commit()

    conn.close()
except Exception as err:
    print('could not get record_id?')
    print(err)