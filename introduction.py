
# received decision from gaze_decision or verbal_decision and call on the robot?



# This program receives coordinate information from who_is_speaking.py (or mp_yolo.py)
# it's for the demo where misty looks at the torso of multiple people from left to right

from mistyPy.Robot import Robot
from mistyPy.Events import Events

import openai
import re

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
import select



rob = False

stop_event = threading.Event()
task_thread = None


# TEST 
random_stop_event = threading.Event()
random_movement_thread = None

misty_ip = "192.168.0.101"
# misty = Robot(misty_ip)
begin_prompt = False
pitch = 0
yaw = 0




def set_to_default():
    url = f"http://{misty_ip}/api/display/settings"
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
    left = random.randint(-15,15)
    right = -left
    current_response = misty.MoveArms(left, right, 50, 50)



def tilt_head(pnt):
    current_response = misty.MoveHead(pitch, 20, yaw, 100, None, None)
    move_arm()



def nod(pt):
    current_response = misty.MoveHead(pitch  + 15 , 0, yaw, 99, None, None)
    move_arm()
    time.sleep(0.15)
    current_response = misty.MoveHead(pitch - 15, 0, yaw, 99, None, None)
    move_arm()
    time.sleep(0.15)
    current_response = misty.MoveHead(pitch, 0, yaw, 99, None, None)
    move_arm()

    

def speak(text):
    payload = {
        "Text": f"<speak>{text}</speak>"
        # "UtteranceId": utterance_id
    }
    current_response = requests.post(
        f"http://{misty_ip}/api/tts/speak",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )




def move_head(x, y):
    # Misty's head moves -40(up) to 25(down), pitch
    # Misty's head moves -90(left) to 90(right), yaw
    global pitch, yaw
    
    if x != "None" and y != "None":
        pitch = -40 + y * 65
        yaw = 60 - x *120
        current_response = misty.MoveHead(pitch, 0, yaw, 97, None, None)
    else:
        # do nothing, and maybe centers the head after a while?
        pitch = 0
        yaw = 0
        current_response = misty.MoveHead(pitch, 20, yaw, 97, None, None)

def gaze(pos):
    [x, y] = pos
    move_head(x, 0.7) # HERE we hardcode the height of gaze 
    move_arm()

    
def random_movements(random_stop_event):

    # TEST 
    move_arm()

    y = 0.7 # we hardcode it here
    pitch = -40 + y * 65
    x = random.uniform(0.45, 0.65)
    yaw = 60 - x *120

    current_response = misty.MoveHead(pitch, 0, yaw, 85, None, None)
    

    total_sleep = random.uniform(0.5, 3)

    elapsed = 0
    interval = 0.1  # 100ms chunks
    while elapsed < total_sleep:
        if random_stop_event.is_set():
            print("[Random Movements] Interrupted during sleep.")
            return
        time.sleep(min(interval, total_sleep - elapsed))
        elapsed += interval
    
    # current_response = misty.MoveHead(pitch, 0, yaw, 85, None, None)




def list_misty_images():
    url = f"http://{misty_ip}/api/images/list"
    response = requests.get(url)

    if response.status_code == 200:
        images = response.json().get("result", [])
        print("Images stored on Misty:")
        for img in images:
            name = img["name"]
            width = img["width"]
            height = img["height"]
            system = img["systemAsset"]
            print(f"- {name} ({width}x{height}) {'[System]' if system else '[User]'}")
    else:
        print("Failed to get image list:", response.status_code, response.text)


def display_image(image_name, alpha=1.0):
    # displays a custom image from Misty's storage.
    url = f"http://{misty_ip}/api/images/display"
    payload = {
        "FileName": image_name,
        "Alpha": alpha
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    print(f"DisplayImage response: {response.json()}")



def revert_to_default_face():
    # Clears all layers and reverts to Misty's default eyes 
    url = f"http://{misty_ip}/api/display/settings"
    payload = {
        "RevertToDefault": True
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    print(f"RevertToDefault response: {response.json()}")



def set_eyes(emotion):

    if emotion == "default":
        revert_to_default_face()
        return 
    
    emotion_dict = {
        "happy": "e_Admiration.jpg",
        "love": "e_Love.jpg",
        "surprise": "e_Surprise.jpg",
        "amazement": "e_Amazement.jpg"
    }
    display_image(emotion_dict[emotion])


def execute_tasks(tasks, stop_event):
    print("task list: ", tasks)
    for task in tasks:
        func_name = task[0]
        total_sleep = task[1]
        params = task[2]

        if stop_event.is_set():
            print("[Execution Thread] Interrupted before task.")
            break
        try:
            # print("current task: ", func_name)
            func = globals()[func_name]
            func(params)

            # Interruptible sleep in small chunks
            elapsed = 0
            interval = 0.1  # 100ms chunks
            while elapsed < total_sleep:
                if stop_event.is_set():
                    print("[Thread] Interrupted duringaze sleep.")
                    return
                time.sleep(min(interval, total_sleep - elapsed))
                elapsed += interval

        except Exception as e:
            print(f"[Thread] Error: {e}")
    return 


def generate_intervention(cmd):

    cmd_type = cmd[0]
    pnt = cmd[1]
    pt = cmd[2]


    tasks = []
    middle = (0.5, 0.6)



    if cmd_type == "hi": # this is a hard interject that requires interruptions

        hi = "Hi, I am misty! What are your names?"
        pt = (0.3, 0.6)
        pnt = (0.7, 0.6)
        # first, generate turn-requesting signals
        # look at Pt, Pnt, then Pt again  
        tasks.append(["gaze", 0.6, pt])
        tasks.append(["gaze", 0.6, pnt])
        tasks.append(["gaze", 0.6, pt]) 

        tasks.append(["speak", 1, hi])
        tasks.append(["gaze", 0.4, pnt])
        tasks.append(["tilt_head", 1, pt])

        

    elif cmd_type == "nice":
        
       
        prompt = "Nice to meet you!"

        tasks.append(["set_eyes", 0.2, "happy"])
        tasks.append(["speak", 1, prompt])
        tasks.append(["gaze", 0.5, pnt])
        tasks.append(["gaze", 0.5, pt])
        tasks.append(["tilt_head", 1, pt])
        tasks.append(["gaze", 0.5, middle])

        tasks.append(["set_eyes", 0.2, "default"])


    elif cmd_type == "intro":
        prompt = "It’s my pleasure to be the facilitator for your task today. You may think of me as a mediator for a group discussion. Sometimes I might jump in and ask you questions, other time I just observe."
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["speak", 2, prompt])


    elif cmd_type == "know":
        prompt = "I do know the correct ranking of these items based on expert advice. And I will be here to monitor your responses."
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["speak", 2, prompt])


    elif cmd_type == "thank":
        prompt = "Thank you, shall we begin?"
        tasks.append(["speak", 1.5, prompt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, pt])


    elif cmd_type == "last":
        prompt = "Thank you guys for the last discussion. You guys did a great job. "
        tasks.append(["speak", 1.5, prompt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 0.1, pt])
    
    elif cmd_type == "some":
        prompt = "You got some of the items right last time. Keep up the good work."
        tasks.append(["speak", 1.5, prompt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, pt])

    elif cmd_type == "most":
        prompt = "You got most of the items right last time. Congratulations."
        tasks.append(["speak", 1.5, prompt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, pt])

    elif cmd_type == "end":
        prompt = "You may wrap up the discussion now. thank you!"
        tasks.append(["speak", 1.5, prompt])
        tasks.append(["set_eyes", 0.2, "happy"])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["gaze", 0.5, middle])

    return tasks

     

def test_introduction():
    key = input("what kind of intervention would you like to test? : ")


   
    if key == "8":
        begin()
        return 

    test = {"1":["hi", (0.2, 0.6), (0.8, 0.6)],
            "2":["nice", (0.2, 0.6), (0.8, 0.6)],
            "3": ["intro", (0.2, 0.6), (0.8, 0.6)],
            "4": ["know", (0.2, 0.6), (0.8, 0.6)],
            "5": ["thank", (0.2, 0.6), (0.8, 0.6)],
            "6": ["last", (0.2, 0.6), (0.8, 0.6)],
            "7": ["some", (0.2, 0.6), (0.8, 0.6)],
            "8": ["most", (0.2, 0.6), (0.8, 0.6)],
            "9": ["end", (0.2, 0.6), (0.8, 0.6)]}

    tasks = generate_intervention(test[key])
    execute_tasks(tasks, stop_event)


def begin():
    prompt_to_begin = "You can begin the discussion now."
    speak(prompt_to_begin)
    move_head(0.3, 0.7)
    time.sleep(1)
    move_head(0.7, 0.7)
    time.sleep(1)
    move_head(0.5, 0.7)


if __name__ == "__main__":
    ipAddress = "192.168.0.101"
    misty = Robot(ipAddress)
    start_skill()
    while True:
        test_introduction()
   


    