# to run with Misty announcing the beginning prompt, python3 baseline_intervention.py -p
from mistyPy.Robot import Robot
from mistyPy.Events import Events


import mediapipe as mp
import numpy as np

import time
import socket
import random

import json
from collections import defaultdict
import threading 
import sys
import requests




stop_event = threading.Event()
gaze_task_thread = None


ipAddress = "192.168.0.100"
misty = Robot(ipAddress)

def set_to_default():
    url = f"http://{ipAddress}/api/display/settings"
    payload = {
        "RevertToDefault": True
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))

def start_skill():
    current_response = misty.MoveArms(90, 90)
    print(current_response)
    print(current_response.status_code)
    print(current_response.json())
    print(current_response.json()["result"])
    set_to_default()


def move_arm():

    left = random.randint(-10,10)
    right = -left
    current_response = misty.MoveArms(left, right, 50, 50)

def move_head():
    
    y = 0.6 # we hardcode it here
    pitch = -40 + y * 65
    x = random.uniform(0.45, 0.65)
    yaw = 60 - x *120
    
    current_response = misty.MoveHead(pitch, 0, yaw, 85, None, None)

def random_movements():
    while True:
        move_arm()
        move_head()
        pause = random.uniform(0.5, 3)
        time.sleep(pause)




def speak(text):
    payload = {
        "Text": f"<speak>{text}</speak>"
        # "UtteranceId": utterance_id
    }
    current_response = requests.post(
        f"http://{ipAddress}/api/tts/speak",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )


def begin():
    prompt_to_begin ="Thank you guys. Now, you may discuss with your partner and agree on a shared ranking for the items."
    speak(prompt_to_begin)

if __name__ == "__main__":
    sim = "-s" in sys.argv
    begin_prompt = "-p" in sys.argv
    if not sim:
        misty = Robot(ipAddress)
        start_skill()

    if begin_prompt:
        begin()
    
    random_movements()


