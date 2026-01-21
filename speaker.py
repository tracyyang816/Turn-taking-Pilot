
"""
Speaker class: 
takes in- 
    positions of participants, 
    lip_distances of participants,
    angles of sound,
    and time stamps?
    
calculates:
    range (one time setting)
    whether is talking
    total speaking time
    speaking activity list

calculated later in intervention.py:
    dominance of the speaker
    """
    
import numpy as np



class Speaker():

    def __init__(self, speaker_id):
        self.speaker_id = speaker_id
        self.is_talking = False  # Whether the speaker is talking or not
        self.total = 0 # Total speaking time 
        self.dominant = False # whether is dominant

        self.position = None  # Store the current position of the speaker
        self.range = [0, 0] # Angle of speaker relative to the robot

        # self.lip_distances = []  # List to store lip distances variation
        self.lip_moved = False

        # TEST
        self.speaking_activity = []  # Store speaking activity (timestamps)

        self.cur_turn_len = 0
        self.silence = 0

        # TEST
        self.time_passed = 0

    # set position of the speaker 
    def set_position_and_range(self, position):
        # TEST
        self.time_passed = 0
        self.position = position
        if position[0] > 0.5:
            self.range = [190, 360]
            self.speaker_id = "Player 2"
            # self.speaker_id = ""
        else:
            self.range = [0, 170]
            self.speaker_id = "Player 1"
            # self.speaker_id = ""

    # update lip distance for variability calculation
    def update_lip_movement(self, lip_moved):
        self.lip_moved = lip_moved
    
    # check if participant is speaking via lip movement variability
    def check_if_talking(self, angles): # the list of all doa in the past segment 
        
        if self.lip_moved or any(self.range[0] <= angle <= self.range[1] for angle in angles):
            self.is_talking = True
            self.total += 0.2
            self.cur_turn_len += 0.2
            self.recent_turn_len = self.cur_turn_len
        else:
            self.is_talking = False
            self.silence += 0.2
            if self.silence > 0.6:
                self.cur_turn_len = 0
        # print(self.is_talking, self.total, self.range)

        # TEST 
        self.time_passed += 0.2
        self.speaking_activity.append((self.time_passed, self.is_talking))
        return self.is_talking


