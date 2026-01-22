
import numpy as np
from speaker import Speaker


# GazeDecision is called whenever a change in talker occurs, or when a gaze shift is intended 
class GazeDecision:
    def __init__(self, speaker1, speaker2, min_gaze = 3, max_gaze = 5):
        self.min_gaze = min_gaze  # minimum gaze duration
        self.max_gaze = max_gaze  # maximum gaze duration

        self.speaker1 = speaker1 # (ADD: in the study design make it the left)
        self.speaker2 = speaker2

        self.pt = speaker1
        self.pnt = speaker2

        self.pa = speaker1

        # CHANGE: Just added these so the program doesn't crash
        # while sending payload to the interface
        self.dom = self.speaker1
        self.non_dom = self.speaker2 # non-dominant participant

        self.silence = 0
        self.overlap = 0
        self.speech_ratio = 1


        self.gaze_tasks = []
        self.cur_task_length = 0
        self.cur_task_execution = 0

        self.segment_duration = 0.2
 


    def update_speaker(self): # ADD: think about when both participants are talking
        

        if self.speaker1.cur_turn_len > self.speaker2.cur_turn_len:
            self.pt = self.speaker1
            self.pnt = self.speaker2
            self.silence = 0

            if self.speaker2.is_talking: 
                self.overlap += self.segment_duration
            
            else:
                self.overlap = 0

        elif self.speaker1.cur_turn_len < self.speaker2.cur_turn_len:
            self.pt = self.speaker2
            self.pnt = self.speaker1
            self.silence = 0

            if self.speaker1.is_talking: 
                self.overlap += self.segment_duration
            else:
                self.overlap = 0

        else: # could be either are talking or both are talking
            # self.pt = None (instead of None, we just make it the same as last self.pt)
            self.silence += self.segment_duration
    

    def compute_speech_ratio(self):
        # if either speaker has not spoken yet, just assume right now it is balanced
        # there is not a dominant or non-dominant speaker yet 
        if self.speaker2.total == 0 or self.speaker1.total == 0:
            self.speech_ratio = 1.0  
            return 1.0

        self.speech_ratio = self.speaker1.total / self.speaker2.total
        if self.speech_ratio > 1:
            self.dom = self.speaker1
            self.non_dom = self.speaker2
        else: 
            self.dom = self.speaker2
            self.non_dom = self.speaker1

        return self.speech_ratio

 
    # Borrowed from Sarah's code 
    def calculate_gaze_time(self):
        change_time = 1 - self.speech_ratio
        change_time = max(change_time, (self.min_gaze - self.max_gaze) / 3.0)
        gaze_time = np.random.uniform (self.min_gaze + change_time, self.max_gaze + change_time)
        return gaze_time
    

    def gaze_decision(self, speaker1, speaker2):
        self.speaker1 = speaker1
        self.speaker2 = speaker2

        self.update_speaker()
        self.compute_speech_ratio()
        
        if self.pt is None: 
            # ADD : maybe make misty do something even if nobody has spoken yet
            print("self.pt is None")
            return None

        # Just for debugging purposes
        # if self.pa is None:
        #     print("self.pa is None")
        # else:
        #     print("self. pt = ", str(self.pt.speaker_id), "self. pa = ", str(self.pa.speaker_id))
            
        if self.pa is not self.pt:

            if self.pa is None:
                print("self.pa is None")
            else:
                print("self. pt = ", str(self.pt.speaker_id), "self. pa = ", str(self.pa.speaker_id) + "\n")

            # a speaker change has happened
            # first, stop all current behaviors
            print("Speaker switched, " + str(self.pt.speaker_id) + " is now speaking.")
            self.cur_task_execution = 0
            self.cur_task_length = 0
            self.gaze_tasks = []
        
        
        else:
            if self.cur_task_execution >= self.cur_task_length:
                self.pa = None
                print ("no speaker change but task is finished. ")
                # no speaker change but task finished
                self.cur_task_execution = 0
                self.cur_task_length = 0
                self.gaze_tasks = []
            
            else:
                # no speaker change, and task unfinished, finish executing current gaze tasks
                self.cur_task_execution += self.segment_duration
                return None 

        gaze_time = self.calculate_gaze_time()

        # only if a speaker change has happenend or current tasks finished 
        try: 
            
            # no dominant speaker yet
            if self.speech_ratio == 1:
                self.pa = self.pt
                self.gaze_tasks.append((gaze_time, self.pt.position))
                self.gaze_tasks.append((gaze_time, self.pnt.position))
                self.cur_task_length = gaze_time * 2


            # if the non domoninant speaker is talking, gaze the the non_dom speaker longer
            elif self.silence > 4 or self.pt is self.non_dom:
                self.pt = self.non_dom # assume self.pt is non_dom when silence exceeds 4 seconds
                self.pa = self.non_dom

                # start looking at the non-dominant speaker first 
                # print("None dominant", self.speech_ratio)
                self.gaze_tasks.append((gaze_time, self.non_dom.position))
            
                if self.speech_ratio > 1: 
                    self.gaze_tasks.append((gaze_time / self.speech_ratio, self.dom.position))
                    self.gaze_tasks.append((gaze_time, self.non_dom.position))
                    self.cur_task_length = gaze_time * (1 + 1/self.speech_ratio)
                else:
                    self.gaze_tasks.append((gaze_time * self.speech_ratio, self.dom.position))
                    self.gaze_tasks.append((gaze_time, self.non_dom.position)) 
                    self.cur_task_length = gaze_time * (1 + self.speech_ratio)


            # if the dominant speaker is talking, gaze is distributed equally
            elif self.pt is self.dom:
                self.pa = self.dom
                # start looking at the dominant speaker first

                # print("dominant", self.speech_ratio)
                self.gaze_tasks.append((gaze_time, self.dom.position))
                self.gaze_tasks.append((gaze_time, self.non_dom.position))

                # calculate how long the current gaze task would take 
                self.cur_task_length = gaze_time * 2
            

        except AttributeError: 
            # there is not a dominant speaker yet, just distribute gaze equally
            print("Attribute error.")
            return None

        return self.gaze_tasks
