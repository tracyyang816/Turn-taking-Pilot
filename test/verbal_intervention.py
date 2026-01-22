
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
import os
from dotenv import load_dotenv

load_dotenv()






stop_event = threading.Event()
task_thread = None


# TEST 
random_stop_event = threading.Event()
random_movement_thread = None

misty_ip = "192.168.0.100"
# misty = Robot(misty_ip)
begin_prompt = False

openai.api_key = os.getenv("OPENAI_API_KEY")
pitch = 0
yaw = 0

transcription_file = "transcripts.txt"


question = ""
last_line_idx = 0



prompts = [
    ["That's a great point", "how do you see it?" ],
    ["I really like that insight" , "what's your take on that?"],
    ["Thanks for sharing that.","what about you? any thoughts?"],
    ["Hmmm, that's an interesting perspective.", "do you agree or see it differently?"]
    ]  



questions = [' What do you think is the biggest challenge we’ll face out here?', ' How would you handle staying warm if things get really tough?', ' What’s one skill you think is super important for surviving in the subarctic?']



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

    global questions, prompts, backchannel_prompts, question
    
    print(cmd)
    cmd_type = cmd[0]
    pnt = cmd[1]
    pt = cmd[2]

    tasks = []

    if cmd_type == "hard": # this is a hard interject that requires interruptions

        # first, generate turn-requesting signals
        # look at Pt, Pnt, then Pt again  
        tasks.append(["gaze", 0.7, pt])
        tasks.append(["gaze", 0.7, pnt])
        tasks.append(["gaze", 0.7, pt]) 

        # Say to pt prompt[0], nod
        # turn to pnt
        # say prompt[1], tilt head and stay until they start speaking
        # after they start speaking, turn to previous pt/ current pnt (not implemented)
        prompt = random.choice(prompts)
        prompts.remove(prompt)

        tasks.append(["nod", 0.8, pt])
        
        tasks.append(["speak", 1.5, prompt[0]])
        tasks.append(["gaze", 0.5, pnt])

        tasks.append(["speak", 1.5, prompt[1]])
        tasks.append(["tilt_head", 0, pnt])


    elif cmd_type == "soft": 
        
        # look at dom then non_dom
        # say prompt[1], tilt head and stay until they start speaking
        # after they start speaking, turn to previous pt/ current pnt (not implemented)
        prompt = random.choice(prompts)
        prompts.remove(prompt)
        tasks.append(["gaze", 0.7, pt])
        tasks.append(["gaze", 0.7, pnt ])
        tasks.append(["speak", 1.5, prompt[1]])
        tasks.append(["tilt_head", 0, pnt])

    # MAYBE: in the end of the turn, back channel and turn to the other participant for response?

    elif cmd_type == "backchannel":
        prompt = random.choice(backchannel_prompts)
        backchannel_prompts.remove(prompt)

        tasks.append(["gaze", 1, pnt])
        tasks.append(["nod", 1, pnt])
        tasks.append(["speak", 2, prompt])
        

    elif cmd_type == "openended":
        
        buffer = "I have a quick question for you...."

        prompt = random.choice(questions)
        questions.remove(prompt)
        tasks.append(["speak", 1, buffer])
        tasks.append(["set_eyes", 0.2, "happy"])
        tasks.append(["speak", 1, prompt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["tilt_head", 4, pnt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["set_eyes", 0.2, "default"])

    elif cmd_type == "generate":
        
        last_transcription = ""
        with open("transcripts.txt", "r") as file:
            lines = file.readlines()
            last_line_idx = len(lines)
            last_four = lines[-4:]  # Get the last 3 lines
            for line in last_four:
                last_transcription += line
        questions = generate_turn_taking_questions(last_transcription) 

        prompt = random.choice(questions)
        questions.remove(prompt)
        question = prompt
        tasks.append(["gaze", 0.7, pnt])
        tasks.append(["speak", 1.5, prompt])
        tasks.append(["tilt_head", 3, pnt])
        tasks.append(["gaze", 1, pt])

    return tasks



def receiver_program():
    global task_thread, stop_event, begin_prompt
    global random_movement_thread, random_stop_event
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = socket.gethostname()
    port = 5000

    server_socket.bind((host, port))
    server_socket.listen(1)
    print("Server listening for connections...")

    conn, address = server_socket.accept()
    print(f"Connection established with {address}")
    

    if begin_prompt:
        begin()

    while True:
        ready, _, _ = select.select([conn], [], [], 0.1)
    
        if ready:
            data = conn.recv(1024).decode()
        else:
            data = None

        if not data:
            # if data == None, continue / finish executing current list
            # make the robot more animate here, and default head to be centered

            # TEST
            if task_thread and task_thread.is_alive(): # if still executing task, just skip random_movements
                continue

            if not (random_movement_thread and random_movement_thread.is_alive()):
                print("[Receiver] No data — starting random movement.")
                random_stop_event.clear()
                random_movement_thread = threading.Thread(
                    target=random_movements, args=(random_stop_event,), daemon=True)
                random_movement_thread.start()
            continue
        
        
        # if data is not None, it means new tasks are generated
        try:
            cmd = json.loads(data)
            
       
            if len(cmd) > 0:
                print("[Receiver] New commands received!")

                # TEST
                # Stop random movement if it's running
                if random_movement_thread and random_movement_thread.is_alive():
                    print("[Receiver] Stopping random movement.")
                    random_stop_event.set()
                    random_movement_thread.join()

                tasks = generate_intervention(cmd)

                # If there's a running thread, interrupt it
                if task_thread and task_thread.is_alive():
                    print("[Receiver] Interrupting current tasks...")
                    stop_event.set()
                    task_thread.join()

                # Clear interrupt and start new task
                stop_event.clear()
                task_thread = threading.Thread(target=execute_tasks, args=(tasks, stop_event))
                task_thread.start()

        except json.JSONDecodeError:
            print("[Receiver] Failed to decode JSON")
            
      
        except TypeError:
            print("[Receiver] TypeError in received data, continue current execution")

            # TEST
            if task_thread and task_thread.is_alive(): # if still executing task, just skip random_movements
                continue

            if not (random_movement_thread and random_movement_thread.is_alive()):
                print("[Receiver] No data — starting random movement.")
                random_stop_event.clear()
                random_movement_thread = threading.Thread(
                    target=random_movements, args=(random_stop_event,), daemon=True)
                random_movement_thread.start()
            continue
        
           
    conn.close()
     

def test_intervention():
    key = input("what kind of intervention would you like to test? : ")

    dom = input("who is more dominant? ")

    if dom == "l":
        dom = (0.3, 0.6)
        non_dom = (0.7, 0.6)
    else: 
        non_dom = (0.3, 0.6)
        dom = (0.7, 0.6)

    test = {"hard":["hard", non_dom, dom],
            "soft":["soft", non_dom, dom],
            "backchannel": ["backchannel", non_dom, dom],
            "openended": ["openended", non_dom, dom]}
    tasks = generate_intervention(test[key])
    execute_tasks(tasks, stop_event)









# NLP INTEGRATION FROM HERE

def generate_turn_taking_questions(transcription): # input is transcription of convo
    prompt = f"""You are a helpful conversation facilitator robot. Based on the following transcription of a two-person conversation in the context of a subarctic survival activity, generate a few short, open-ended questions that can help mediate turn-taking. Focus on encouraging exploration of both perspectives and continued dialogue, use an informal tone. Only output the most approariate three questions.

            Transcription:
            {transcription}

            Questions:"""

    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )

    questions = response['choices'][0]['message']['content'].strip()
    questions_list = split_questions(questions)
    return questions_list



def generate_followup_questions(transcription): # input is transcription of convo
    prompt = f"""You are a helpful conversation facilitator robot. Based on the following transcription of a two-person conversation in the context of a subarctic survival activity, generate a few short follow-up questions that support continued deeper discussion. Use an informal tone. Only output the most approariate three questions.

            Question you just asked: {question}
            Transcription of their conversation after:
            {transcription}

            Follow-up questions:"""

    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )

    questions = response['choices'][0]['message']['content'].strip()
    followup_list = split_questions(questions)
    return followup_list


def split_questions(text):
    questions = re.findall(r'[^?]+\?', text) # this regex finds sentences ending with a question mark
    return [q.strip()[2:] for q in questions]

def begin():
    prompt_to_begin = "Thank you, you can begin the discussion now."
    speak(prompt_to_begin)
    move_head(0.3, 0.7)
    time.sleep(1)
    move_head(0.7, 0.7)
    time.sleep(1)
    move_head(0.5, 0.7)


if __name__ == "__main__":
    sim = "-c" in sys.argv
    begin_prompt = "-p" in sys.argv
    ipAddress = "192.168.0.100"
    if not sim:
        misty = Robot(ipAddress)
        start_skill()
    # list_misty_images()
    # receiver_program()
    # test_intervention()
    # display_image("e_Admiration.jpg")

    # TEST NLP INTEGRATION
    

    time.sleep(30)

    last_transcription = ""
    with open("transcripts.txt", "r") as file:
        lines = file.readlines()
        last_four = lines[last_line_idx:]  # Get the last 3 lines
        for line in last_four:
            last_transcription += line
    questions_list = generate_followup_questions(last_transcription)
    print(questions_list)

    