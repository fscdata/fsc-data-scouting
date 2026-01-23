# all fields in table:
full_field_list = ['match_number', 'team_number', 'notes', 'start_position', 'auto_leave', 'auto_score_preload', 'auto_reefL1', 'auto_reefL2', 'auto_reefL3', 'auto_reefL4', 'auto_algae_knockoff', 'auto_score_algae_net', 'auto_score_algae_proc', 'auto_astop', 'auto_failed', 'teleop_score_algae_net', 'teleop_score_algae_proc', 'teleop_algae_knockoff', 'teleop_reefL1', 'teleop_reefL2', 'teleop_reefL3', 'teleop_reefL4', 'teleop_coral_miss', 'parked', 'coopertition', 'RP_auto', 'RP_coral', 'RP_barge', 'tipped', 'broken', 'REDcarded', 'YELLOWcarded', 'TECHfoul']

class SQL_Templates():
    def __init__(self):
        print('init templates')
        self.get_short_score = "SELECT report_id, match_number, team_number FROM results ORDER BY match_number DESC"
        self.get_full_score = f"SELECT report_id, {','.join(full_field_list)} FROM results ORDER BY match_number, team_number"
        self.get_climb_score = "SELECT event, match_number, team_number, parked, climb_shallow, climb_deep FROM climb ORDER BY match_number ASC"

    def get_csv_score(self, main_match_id):
        return f"SELECT {','.join(full_field_list)} FROM results WHERE match_number >= {main_match_id} ORDER BY match_number, team_number"

    def api_collected_matches(self, event_name):
        return f"SELECT max(match_number) FROM climb WHERE event = '{event_name}'"

    def get_team_scores(self, team_number):
        return f"SELECT * FROM results WHERE team_number={team_number}"

    def enter_new_climb_record(self, climb_data):
        print(climb_data)
        return f"""
            INSERT INTO climb (
                'event', 'match_number', 'team_number', 'parked', 'climb_shallow', 'climb_deep'
            )
            VALUES (
                "{climb_data[0]}",
                "{climb_data[1]}",
                "{climb_data[2]}",
                "{climb_data[3]}",
                "{climb_data[4]}",
                "{climb_data[5]}"
            )
        """

    def enter_new_scout_record(self, scout_data):
        return f"""
            INSERT INTO results (
                {','.join(full_field_list)}
            )
            VALUES (
                "{scout_data['match_number']}",
                "{scout_data['team_number']}",
                "{scout_data['notes']}",
                "{scout_data['start_position']}",
                "{scout_data['auto_leave']}",
                "{scout_data['auto_score_preload']}",
                "{scout_data['auto_reefL1']}",
                "{scout_data['auto_reefL2']}",
                "{scout_data['auto_reefL3']}",
                "{scout_data['auto_reefL4']}",
                "{scout_data['auto_algae_knockoff']}",
                "{scout_data['auto_score_algae_net']}",
                "{scout_data['auto_score_algae_proc']}",
                "{scout_data['auto_astop']}",
                "{scout_data['auto_failed']}",
                "{scout_data['teleop_score_algae_net']}",
                "{scout_data['teleop_score_algae_proc']}",
                "{scout_data['teleop_algae_knockoff']}",
                "{scout_data['teleop_reefL1']}",
                "{scout_data['teleop_reefL2']}",
                "{scout_data['teleop_reefL3']}",
                "{scout_data['teleop_reefL4']}",
                "{scout_data['teleop_coral_miss']}",
                "{scout_data['parked']}",
                "{scout_data['coopertition']}",
                "{scout_data['RP_auto']}",
                "{scout_data['RP_coral']}",
                "{scout_data['RP_barge']}",
                "{scout_data['tipped']}",
                "{scout_data['broken']}",
                "{scout_data['REDcarded']}",
                "{scout_data['YELLOWcarded']}",
                "{scout_data['TECHfoul']}"
            )
        """