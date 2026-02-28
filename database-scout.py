import sqlite3


# Open database
conn = sqlite3.connect('Hartsville_2025_Scouting.db')

# Create tables
match_results_create = '''
    CREATE TABLE results
    ( 
        report_id INTEGER PRIMARY KEY,
        team_number INTEGER,
        match_number INTEGER,
        notes TEXT,
        start_position TEXT,
        auto_leave INTEGER,
        auto_score_preload INTEGER,
        auto_reefL1 INTEGER,
        auto_reefL2 INTEGER,
        auto_reefL3 INTEGER,
        auto_reefL4 INTEGER,
        auto_algae_knockoff INTEGER,
        auto_score_algae_net INTEGER,
        auto_score_algae_proc INTEGER,
        auto_astop INTEGER,
        auto_failed INTEGER,
        teleop_score_algae_net INTEGER,
        teleop_score_algae_proc INTEGER,
        teleop_algae_knockoff INTEGER,
        teleop_reefL1 INTEGER,
        teleop_reefL2 INTEGER,
        teleop_reefL3 INTEGER,
        teleop_reefL4 INTEGER,
        teleop_coral_miss INTEGER,
        parked INTEGER,
        coopertition INTEGER,
        RP_auto INTEGER,
        RP_coral INTEGER,
        RP_barge INTEGER,
        tipped INTEGER,
        broken INTEGER,
        REDcarded INTEGER,
        YELLOWcarded INTEGER,
        TECHfoul INTEGER
    )
'''

climb_results_create = '''
    CREATE TABLE climb
    ( 
        climb_id INTEGER PRIMARY KEY,
        event TEXT,
        match_number INTEGER,
        team_number INTEGER,
        parked INTEGER,
        climb_shallow INTEGER,
        climb_deep INTEGER
    )
'''

conn.execute(match_results_create)
conn.execute(climb_results_create)

conn.close()