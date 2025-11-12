
from speaker import Speaker

class VerbalDecision:
    def __init__(self, speaker1, speaker2):
    
        self.speaker1 = speaker1 # (ADD: in the study design make it the left)
        self.speaker2 = speaker2

        self.pt = None # participant currently talking 
        self.pa = None
        self.dom = None
        self.non_dom = None # non-dominant participant

        self.silence = 0
        self.overlap = 0
        self.speech_ratio = 1
        self.last = 0
        self.total_seconds_passed = 0
        self.segment_duration = 0.2


    def update_speaker(self): # ADD: think about when both participants are talking

        if self.speaker1.cur_turn_len > self.speaker2.cur_turn_len:
            self.pt = self.speaker1
            self.silence = 0

            if self.speaker2.is_talking: 
                self.overlap += self.segment_duration

        elif self.speaker1.cur_turn_len < self.speaker2.cur_turn_len:
            self.pt = self.speaker2
            self.silence = 0

            if self.speaker1.is_talking: 
                self.overlap += self.segment_duration

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
        if self.speech_ratio > 0:
            self.dom = self.speaker1
            self.non_dom = self.speaker2
        else: 
            self.dom = self.speaker2
            self.non_dom = self.speaker1

        return self.speech_ratio


    def intervene(self, speaker1, speaker2):
        # right now speech ratio is two sided 
        # ADD: do a manipulation check midway, perhaps after 2 minutes?

        # return the type of intervention: "soft" does not require turn-requesting signal, "hard" does
        # the second item returned is the position of speaker that needs help

        self.speaker1 = speaker1
        self.speaker2 = speaker2
        self.total_seconds_passed += self.segment_duration
        self.last += self.segment_duration

        self.update_speaker()
        self.compute_speech_ratio()

        try:
            if self.non_dom.recent_turn_len > 2.5 and self.silence > 0.4 and self.silence < 2:
                    self.pa = self.non_dom
                    return ["backchannel", self.non_dom.position, self.dom.position]
            


            if self.total_seconds_passed > 10 and self.last > 30:
                # print(self.silence) # CHANGE depending on segment duration
                if self.silence > 2: # if there is an extended period of silence 
                    # soft interject to the non-dominant
                    self.pa = self.non_dom

                    wizard = input("Proceed with the [Open-ended] interjection? (y/n) : ")
                    if wizard == "y":
                        self.last = 0
                        return ["openended", self.non_dom.position, self.dom.position]
                    else:
                        self.last -= 7
                        return None

                    # return ["soft", self.non_dom.position, self.dom.position]

                    
                elif self.speech_ratio > 2: # severe imbalance, speaker1 is talking a lot
                    if self.pt == self.dom:
                        self.pa = self.non_dom
                        
                        wizard = input("Proceed with the [Hard Interupt] interjection? (y/n) : ")
                        if wizard == "y":
                            self.last = 0
                            return ["hard", self.non_dom.position, self.dom.position]
                        else:
                            self.last -= 7
                            return None
                    


                elif self.speech_ratio < 0.5: # severe imbalance, speaker2 is talking alot
                    if self.pt == self.dom:
                        self.pa = self.non_dom

                        wizard = input("Proceed with the [Hard Interrupt] interjection? (y/n) : ")
                        if wizard == "y":
                            self.last = 0
                            return ["hard", self.non_dom.position, self.dom.position]
                        else:
                            self.last -= 7
                            return None

        except AttributeError:
            print("AttributeError.")




        return None