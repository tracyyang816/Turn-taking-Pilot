
# received decision from gaze_decision or verbal_decision and call on the robot?



# This program receives coordinate information from who_is_speaking.py (or mp_yolo.py)
# it's for the demo where misty looks at the torso of multiple people from left to right

from mistyPy.Robot import Robot
from mistyPy.Events import Events


# import mediapipe as mp
import numpy as np

import time
import socket
import random

import json
from collections import defaultdict
import threading 
import sys
import requests
import openai
import re
import os

from dotenv import load_dotenv
load_dotenv()

pitch = 0
yaw = 0


stop_event = threading.Event()
pause_event = threading.Event()
run_gaze_event = threading.Event()
run_gaze_event.set

gaze_task_thread = None
# ADD
pause_listener = None


misty_ip = "10.214.154.217"

items_round = "1"
items_list_verbose= {"1": ["Safety razor shaving kit with mirror",
    "An operating 4-battery flashlight",
    "3 pairs of snowshoes",
    "One aircraft inner tube for a 14-inch wheel (punctured)",
    "250 ft (76 m) of 1⁄4-inch braided nylon rope, 50 lb. test"],
    
    "2": ["A gallon can of maple syrup",
    "A hand axe",
    "13 wood matches in a metal screwtop, waterproof container",
    "A sleeping bag per person",
    "A piece of heavy-duty canvas"
    ],
    
    "3": ["A book entitled Northern Star Navigation",
    "A wind-up alarm clock",
    "A bottle of water purification tablets",
    "A magnetic compass",
    "1/5 gallon Bacardi rum"
    ]}


items_list= {"1": ["Safety razor with mirror",
    "A flashlight",
    "3 pairs of snowshoes",
    "Punctured aircraft inner tube",
    "Nylon rope"],
    
    "2": ["Maple syrup",
    "A hand axe",
    "Wood matches with water proof container",
    "Sleeping bags",
    "Heavy-duty canvas"
    ],
    
    "3": ["A book entitled Northern Star Navigation",
    "An alarm clock",
    "Water purification tablets",
    "A magnetic compass",
    "A Bacardi rum"
    ]}
openai.api_key = os.getenv("OPENAI_API_KEY")




backchannel_prompts = [
    "Uh huh",
    "You're right",
    "I see",
    "Yeah, ok",
    "I hear you",
    "I agree",
    "That's a great point"
  
]


extra_item_list = [ "Loaded point four five caliber pistol",
    "Family size chocolate bars for each person",
    "Ball of steel wool",
    "Cigarette lighter without fluid"]


nudges = ["It’s time to start concluding your discussion. Please try to reach an agreement.",
    "Let’s move toward wrapping up. Can you come to a shared decision?",
    "Please finalize your thoughts and try to reach a consensus.",
    "Hey, let’s work on finding common ground and wrapping up."]

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




def move_arm(pos= 0):
    # 0 = straight forward, 90 = straight down, -90 straight up
    if pos == 0:
        left = random.randint(60,80)
        right = random.randint(60,80)
    
    elif pos > 0.5: # looking right 
        left = random.randint(65,75)
        right = random.randint(25,45)

    else:
        left = random.randint(25,45)
        right = random.randint(65,75)

    current_response = misty.MoveArms(left, right, 85)



def tilt_head(pnt):
    current_response = misty.MoveHead(pitch, 20, yaw, 100, None, asynch=True)
    move_arm()



def nod(pt):
    current_response = misty.MoveHead(pitch  + 15 , 0, yaw, 99, None, asynch=True)
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



def sleep(pause):
    current_response = misty.MoveHead(-35, -15, -12, 90, None, None)

def move_head(x, y):
    # Misty's head moves -40(up) to 25(down), pitch
    # Misty's head moves -90(left) to 90(right), yaw
    global pitch, yaw
    
    y = 0.6
    if x != "None" and y != "None":
        pitch = -40 + y * 65
        yaw = 60 - x *120
        current_response = misty.MoveHead(pitch, 0, yaw, 95, None, None)

        # print(current_response)
        # print(current_response.status_code)
        # print(current_response.json())

    else:
        # do nothing, and maybe centers the head after a while?
        pitch = 0
        yaw = 0
        current_response = misty.MoveHead(pitch, 20, yaw, 95, None, None)


def gaze(pos):
    [x, y] = pos
    move_head(x, 0.7) # HERE we hardcode the height of gaze 
    move_arm()



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
        "amazement": "e_Amazement.jpg",
        "sleep":"e_SleepingZZZ.jpg",
        "look left": "e_ContentLeft.jpg",
        "look right": "e_ContentRight.jpg",
        "concerned": "e_ApprehensionConcerned.jpg"
    }
    display_image(emotion_dict[emotion])



def random_movements():

    left = random.randint(60,80)
    right = random.randint(60,80)
    current_response = misty.MoveArms(left, right, 80)

    y = 0.6 # we hardcode it here
    pitch = -40 + y * 65
    x = random.uniform(0.45, 0.65)
    yaw = 60 - x *120
    current_response = misty.MoveHead(pitch, 0, yaw, 85, None, None)

    pause = random.uniform(0.1, 1)
    time.sleep(pause)


def begin():
    prompt_to_begin = "Now discuss the new items together and decide on a shared list."
    speak(prompt_to_begin)

def split_questions(text):
    questions = re.findall(r'[^?]+\?', text) # this regex finds sentences ending with a question mark
    return [q.strip()[2:] for q in questions]

def generate_turn_taking_questions(transcription): # input is transcription of convo
    # prompt = f"""You are a helpful conversation facilitator robot. Based on the following transcription of a two-person conversation in the context of a subarctic survival activity, generate a few short, open-ended questions that can help mediate turn-taking. Focus on encouraging exploration of both perspectives and continued dialogue, use an informal tone. Only output the most approariate three questions.

    #         Transcription:
    #         {transcription}

    #         Questions:"""

    prompt = prompt = f"""
You are a helpful and informal conversation facilitator robot assisting two participants in a subarctic survival activity. They are working together to rank a list of survival items in order of importance and come to an agreement. Your job is to help the conversation move forward by asking short, open-ended, and productive questions that:

- Encourage equal participation and turn-taking
- Prompt reflection on specific items, their functions, or challenges
- Surface differing viewpoints in a non-confrontational way

You will be given a recent snippet of their conversation and the current list of survival items under discussion. Use this information to generate three relevant questions based on the following **example templates**, the blanks and [challenge] are items you should dynamically infer from the conversation:

### Template Types

**Item Comparison Questions**  
- “Do you think ___ is more crucial than ____ if [specific scenario or challenge] happens?”  
- “If we had to choose between ____ and ____, which one do you think would help us more with [challenge]?”

**Function-Based Questions**  
- “What do you think is the most useful thing about the _____ in this situation?”  
- “How exactly do you see the ____ helping us deal with [survival challenge]?”  
- “Could the ____ be used for more than one thing out there?”

**Challenge-Oriented Questions**  
- “What’s the biggest danger we need to be ready for first — is it [challenge1] or [challenge2]?”  
- “How prepared do you feel we’d be for [challenge] with the items we’ve ranked so far?”

**Perspective-Eliciting Questions**  
- “What made you put ____ higher/lower on the list — just curious?”  
- “Do you see the _____ differently?"
- “Has your view on the _____ changed after talking about it?”

Below is the current transcription and item list. Use them to generate three specific and relevant questions based on the above templates. Only output the top 3 questions.

Transcription:
{transcription}


Questions:
"""

# "You haven't talked much about _____, what do think are some potential uses for it?"

    item_list = items_list[items_round]
# Items: {item_list}


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



def generate_where_question(transcription): 
    
    
    
    item_list = items_list[items_round]
  

    prompt  = f"""
You are a helpful and informal conversation facilitator robot assisting two participants in a subarctic survival activity. They are working together to rank a list of survival items in order of importance and come to an agreement. Your job is to help the conversation move forward by inquiring them about an item that has not been brought up or talked about least frequently in the conversation.


You will be given a recent snippet of their conversation and the current list of survival items under discussion. Use this information to infer which item has been mentioned the least dynamically from their conversation.

Answer with only the name of the least talked about item. If they have talked about an item recently

Transcription:
{transcription}


Item list = {item_list}

Selected item:

"""

# "You haven't talked much about _____, what do think are some potential uses for it?"

# Items: {item_list}


    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )

    item = response['choices'][0]['message']['content'].strip()
    return item



def execute_gaze_tasks(gaze_tasks, stop_event):

    # ADD: baseline
    if gaze_tasks == "random_movements":
        random_movements()


    for task in gaze_tasks:
        if stop_event.is_set():
            print("[Gaze Thread] Interrupted before task.")
            break
        
        # CHANGED 
        # while pause_event.is_set():
        #     print("[Gaze Thread] Paused.")
        #     time.sleep(0.1)
        run_gaze_event.wait()

        try:
            [x, y] = task[1]
            
            move_head(x, y)
            move_arm(x)
            # if x < 0.4:
            #     set_eyes("look left")
            # elif x > 0.6: 
            #     set_eyes("look right")
            # else:
            #     set_eyes("default")

            # Interruptible sleep in small chunks
            total_sleep = task[0]
            elapsed = 0
            interval = 0.1  # 100ms chunks
            while elapsed < total_sleep:
                if stop_event.is_set() or not run_gaze_event.is_set():
                    print("[Gaze Thread] Interrupted during sleep.")
                    return
                time.sleep(min(interval, total_sleep - elapsed))
                elapsed += interval

        except Exception as e:
            print(f"[Gaze Thread] Error: {e}")




    
def receiver_program():
    global gaze_task_thread, stop_event, pause_listener

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    port = 5000

    server_socket.bind((host, port))
    server_socket.listen(1)
    print("Server listening for connections...")
    conn, address = server_socket.accept()
    print(f"Connection established with {address}")



    while True:
        # conn, address = server_socket.accept()
        # print(f"Connection established with {address}")

        # CHANGED
        # if pause_event.is_set():
        #     # interface is prompting behavior
        #     print("pause event set")
        #     pause_event.wait(timeout=0.1)
        #     pause_event.clear()
        #     continue 

        run_gaze_event.wait()

        data = conn.recv(1024).decode('utf-8')

        if not data:
            conn, address = server_socket.accept()
            print(f"Connection established with {address}")
            continue
        
        
        # if data is not None, it means new gaze_tasks are generated
        try:
            gaze_tasks = json.loads(data)
    
            if len(gaze_tasks) > 0:
                print("[Receiver] New commands received!")

                # If there's a running thread, interrupt it
                if gaze_task_thread and gaze_task_thread.is_alive():
                    print("[Receiver] Interrupting current gaze task...")
                    stop_event.set()
                    gaze_task_thread.join() 

                # Clear interrupt and start new task
                stop_event.clear()
                gaze_task_thread = threading.Thread(target=execute_gaze_tasks, args=(gaze_tasks, stop_event))
                gaze_task_thread.start()
                

        except json.JSONDecodeError:
            print("[Receiver] Failed to decode JSON")
        except TypeError:
            print("[Receiver] TypeError in received data.")

        # conn.close()






# ADD
def pause_listener():
    global pause_event, run_gaze_event
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 6000))
    server.listen(1)
    print("[Control Listener] Ready on port 6000")

    while True:
        conn, _ = server.accept()
        command = conn.recv(1024).decode()

 
        if command:
            run_gaze_event.set()

            # pause_event.set()
            # if command == "resume":
            #     print("[Control] Resuming gaze.")
            #     pause_event.clear()
            
            # else:
            #     pause_event.set()
        
            tasks = generate_behaviors(command) # this is where we check for resume
            if not sim:
                execute_commands(tasks)
        # else:
        #     pause_event.clear()
            
        conn.close()



def execute_commands(tasks):
  
    for task in tasks:
        func_name = task[0]
        total_sleep = task[1]
        params = task[2]

        func = globals()[func_name]
        func(params)
        time.sleep(total_sleep)
        # for _ in range(int(total_sleep / 0.05)):
        #     if pause_event.is_set(): return
        #     time.sleep(0.05)


def generate_behaviors(cmd):
    global items_list, items_round, run_gaze_event

    print("command received: ", cmd)
    cmd = json.loads(cmd)
    

    if isinstance(cmd, list):
        cmd_type = cmd[0]
        player_id = cmd[1]
        pnt = cmd[2]
        pt = cmd[3]

        print(cmd_type, pt, pnt)
    else:
        cmd_type = cmd
        pnt = (0.3, 0.6)
        pt = (0.7, 0.6)
    
    if cmd_type == "resume":
        run_gaze_event.set()
        print("Resuming Gaze Tasks")
        return 

    if player_id == "Player 1":
        other_player = "Player 2"
    elif player_id == "Player 2":
        other_player = "Player 1"

    
    middle = (0.5, 0.6)
    left = (0.3, 0.6)
    right = (0.7, 0.6)


    tasks = []
    
    # LIST

    if cmd_type == "1" or cmd_type == "2" or cmd_type == "3":
        items_round = cmd_type

            
    # TEXT BOX

    if cmd_type == "send":
        tasks.append(["gaze", 0.3, middle])
        tasks.append(["speak", 0.3, player_id])

    elif cmd_type == "hi":
        hi = "Hi, I am misty! What are your names?"
        tasks.append(["gaze", 0.3, pt])
        tasks.append(["gaze", 0.3, pnt])
        tasks.append(["gaze", 0.3, pt]) 

        tasks.append(["speak", 0, hi])
        tasks.append(["gaze", 0.4, pnt])
        # tasks.append(["tilt_head", 1, pt])


    elif cmd_type == "nice":
    
        prompt = "Nice to meet you!"

        tasks.append(["set_eyes", 0.2, "happy"])
        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 0.2, pnt])
        tasks.append(["gaze", 0.2, pt])
        # tasks.append(["tilt_head",3, pt])
        tasks.append(["set_eyes", 0.2, "default"])


    elif cmd_type == "intro":
        prompt = "It’s my pleasure to be the facilitator for your task today. You may think of me as a mediator for a group discussion. Sometimes I might jump in and ask you questions, other time I just observe. You may use the board to play out your thought process at anytime during the study."
        tasks.append(["speak", 0.3, prompt])
        tasks.append(["gaze", 0.2, pnt])
        tasks.append(["gaze", 0.2, pt])


    elif cmd_type == "know":
        prompt = "I do know the correct ranking of these items based on expert advice. And I will be here to monitor your responses."
        tasks.append(["gaze", 0.2, pnt])
        tasks.append(["gaze", 0.2, pt])
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 0.1, middle])


    elif cmd_type == "thank":
        prompt = "Thank you, shall we begin?"
        tasks.append(["speak", 0.3, prompt])
        tasks.append(["gaze", 0.2, middle])
     




    # CONNECTION 

    elif cmd_type == "last1":
        prompt = "Thank you guys for the last discussion. You guys did a great job with the ranking. "
        tasks.append(["speak", 0.3, prompt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 0.1, pt])
    
    elif cmd_type == "last2":
        prompt = "Good discussion. Keep up the good work!"
        tasks.append(["speak", 0.3, prompt])
        tasks.append(["gaze", 0.2, pnt])
        tasks.append(["gaze", 0.2, pt])

    

    # OPEN (INTERVENTION)

    elif cmd_type == "open1":
        player_id = random.choice(["Player 1", "Player 2"])
        if player_id == "Player 1":
            pos = (0.3, 0.6)
        else:
            pos = (0.7, 0.6)

        # prompt = f"Now it's time to discuss with your partner and agree on a shared ranking for the items. The discussion should be around 5 minutes. {player_id}, why don't you start first? "
        prompt = f"Now it's time to discuss with your partner and agree on a shared ranking for the items. Why don't you guys go ahead and start by sharing your top ranked item, and continue from there? "
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 1, pos])
        tasks.append(["gaze", 1, middle])
    
    elif cmd_type == "open2":
        player_id = random.choice(["Player 1", "Player 2"])
        if player_id == "Player 1":
            pos = (0.3, 0.6)
        else:
            pos = (0.7, 0.6)

        prompt = f"Now take the next 5 minutes to discuss the new items together and decide on a shared list. You guys may begin with the items you think are the most useful and continue your thoughts from there."
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 1, pos])
        tasks.append(["gaze", 0.5, middle])

    elif cmd_type == "open3":
        player_id = random.choice(["Player 1", "Player 2"])
        if player_id == "Player 1":
            pos = (0.3, 0.6)
        else:
            pos = (0.7, 0.6)

        prompt = f"You can begin the discussion now. Keep in mind you only have 5 minutes. Feel free to start with the items you feel most strongly about and go from there."
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 1, pos])
        tasks.append(["gaze", 0.5, middle])


    # TIME
    elif cmd_type == "1min":
        prompt = "You guys have about 1 minute left to reach an agreement."
        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 1, middle])

    elif cmd_type == "nudge":
        prompt = random.choice(nudges)
        nudges.remove(prompt)
        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 1, middle])
    
    elif cmd_type == "agreement":
        prompt = "Seems like you have reached an agreement. Good job. You may end the discussion now."
        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 0.6, middle])

    elif cmd_type == "explain_all":
        prompt = f"{player_id}, could you explain to me the main reasoning behind ranking all the items the way you did?"
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 0.5, pnt])

    elif cmd_type == "extra":

        item = random.choice(extra_item_list)
        extra_item_list.remove(item)

        prompt = "You guys still have a little bit time left. Now what would you do if I give you an extra item ---" + item
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 0.3, pnt])
        tasks.append(["gaze", 0.3, pt])

    elif cmd_type == "wrap":
        prompt = "That wraps up our discussion for this round. Thank you."
        tasks.append(["speak", 0.5, prompt])
        tasks.append(["gaze", 1, middle])
    

    # BASICS
    elif cmd_type == "yes":
        prompt = "Yes"
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 0.2, pnt])

    elif cmd_type == "no":
        prompt = "Not quite"
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 0.2, pnt])

    elif cmd_type == "idk":
        prompt = "Sorry, I don't know"
        tasks.append(["speak", 0.5, prompt])
        tasks.append(["gaze", 1, pnt])

    elif cmd_type == "thankyou":
        prompt = "Thank you!"
        tasks.append(["speak", 0.2, prompt])
        tasks.append(["gaze", 0.2, pnt])
        tasks.append(["gaze", 0.2, pt])
        tasks.append(["gaze", 0.2, middle])

    elif cmd_type == "goodpoint":
        prompt = "That's a good point!"
        tasks.append(["speak", 0.5, prompt])
        tasks.append(["gaze", 0.3, middle])

    elif cmd_type == "back":
        prompt = random.choice(backchannel_prompts)
        backchannel_prompts.remove(prompt)
        tasks.append(["speak", 0.3, prompt])
        tasks.append(["nod", 0.1, pnt])
        tasks.append(["gaze", 0.7, pnt])
        tasks.append(["gaze", 0.3, pt])
        tasks.append(["gaze", 0.3, middle])

    
    elif cmd_type == "wbu":
        wbu = random.choice(["What about you?", "What do you think?", "Do you agree?"])
        prompt = f"{other_player}{wbu}"
        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 1.5, pt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, middle])

    elif cmd_type == "Bye ":
        prompt = "Byeee"
        tasks.append(["speak", 0.5, prompt])

    # OPEN-ENDED

    elif cmd_type == "buffer":
        prompt ='Hmmm.... I have quick question. '
        tasks.append(["speak", 0.3, prompt])
        tasks.append(["gaze", 0.5, pnt])
        tasks.append(["gaze", 0.1, middle])

    elif cmd_type == "clarify":
        prompt ='Hmmm.... I want to clarify something quickly.'
        tasks.append(["speak", 0.3, prompt])
        tasks.append(["gaze", 0.5, pnt])
        tasks.append(["gaze", 0.1, middle])

    elif cmd_type == "why":
        prompt ='Why? '
        tasks.append(["speak", 0.5, prompt])
        tasks.append(["gaze", 0.5, pnt])
        tasks.append(["gaze", 0.7, pt])
        tasks.append(["gaze", 0.7, middle])

    elif cmd_type == "explain":
        prompt ='Could you explain to your partner why you think so?'
        tasks.append(["speak", 0.5, prompt])
        tasks.append(["gaze", 2, pnt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["gaze", 1, middle])

    elif cmd_type == "skill":
        prompt = f"{player_id}, what’s one skill you think is super important for surviving in the subarctic?"
        tasks.append(["speak", 0.5, prompt])
        tasks.append(["gaze", 2, pnt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["gaze", 1, middle])

    elif cmd_type == "challenge":
        prompt = f"{player_id}, what do you think is the biggest challenge we’ll face out here?"
        tasks.append(["speak", 0.5, prompt])
        tasks.append(["gaze", 2, pnt])
        tasks.append(["gaze", 1, pt])
        tasks.append(["gaze", 1, middle])


    elif cmd_type == "where":
        last_transcription = ""
        with open("transcripts.txt", "r") as file:
            lines = file.readlines()
            # last_line_idx = len(lines)
            # last_four = lines[-8:] 
            for line in lines:
                last_transcription += line
        item = generate_where_question(last_transcription)
        prompt = f"So {player_id},  where did you rank {item} " # (currently a filler)

        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, middle])
        tasks.append(["gaze", 1, pnt])

    elif cmd_type == "change":
        prompt = "What changed your opinion?"
        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, middle])
        tasks.append(["gaze", 1, pnt])


    elif cmd_type == "continue":
        prompt = "You may continue."
        tasks.append(["speak", 0.1, prompt])
        tasks.append(["gaze", 1, pnt])
        tasks.append(["gaze", 1, middle])
        tasks.append(["gaze", 1, pnt])

    # elif cmd_type == "generate":
    #     last_transcription = ""
    #     with open("transcripts.txt", "r") as file:
    #         lines = file.readlines()
    #         last_line_idx = len(lines)
    #         last_four = lines[-8:]  # Get the last 3 lines
    #         for line in last_four:
    #             last_transcription += line
    #     questions_list = generate_turn_taking_questions(last_transcription)
    #     print(questions_list,"\n")
    #     question = random.choice(questions_list)
    #     prompt = f"{player_id}{question}"
    #     tasks.append(["speak", 0.5, question])
    #     print(question,"\n")

    # elif cmd_type == "warmth":
    #     prompt = f"{player_id}, how would you handle staying warm if things get really tough?"
    #     tasks.append(["speak", 0.5, prompt])
    #     tasks.append(["gaze", 2, pnt])
    #     tasks.append(["gaze", 1, pt])
    #     tasks.append(["gaze", 1, middle])

    # elif cmd_type == "shelter":
    #     prompt = f"{player_id}, how important is it, in your opinion, to find shelter?"
    #     tasks.append(["speak", 0.5, prompt])
    #     tasks.append(["gaze", 2, pnt])
    #     tasks.append(["gaze", 1, pt])
    #     tasks.append(["gaze", 1, middle])
    
    # elif cmd_type == "food":
    #     prompt = f"{player_id}, how do you guys plan to sustain yourselves until rescue? Is food necessary?"
    #     tasks.append(["speak", 0.5, prompt])
    #     tasks.append(["gaze", 2, pnt])
    #     tasks.append(["gaze", 1, pt])
    #     tasks.append(["gaze", 1, middle])

    # elif cmd_type == "water":
    #     prompt = f"{player_id}, what do you guys plan on doing for water? Is that an easily accessible resource?"
    #     tasks.append(["speak", 0.5, prompt])
    #     tasks.append(["gaze", 2, pnt])
    #     tasks.append(["gaze", 1, pt])
    #     tasks.append(["gaze", 1, middle])




    # GAZE
    elif cmd_type == "nod":
        tasks.append(["nod", 0, middle])

    elif cmd_type == "left":
        tasks.append(["gaze", 1, left])
    
    elif cmd_type == "right":
        tasks.append(["gaze", 1, right])

    elif cmd_type == "center":
        tasks.append(["gaze", 1, middle])

    # FACE

    elif cmd_type == "default":
        tasks.append(["set_eyes", 0.2, "default"])
    
    elif cmd_type == "sleep":
        tasks.append(["sleep", 0, "sleep"])
        tasks.append(["set_eyes", 0.2, "sleep"])

    elif cmd_type == "concerned":
        tasks.append(["set_eyes", 0.2, "concerned"])

    return tasks


if __name__ == "__main__":

    sim = "-s" in sys.argv

    if not sim:
        try:
            misty = Robot(misty_ip)
            start_skill()
        except Exception as e:
            misty_ip = "192.168.0.100"
            misty = Robot(misty_ip)
            start_skill()

    # list_misty_images()

    output_receiver_thread = threading.Thread(target=receiver_program, daemon=True)
    output_receiver_thread.start()

    pause_listener_thread = threading.Thread(target=pause_listener, daemon=True)
    pause_listener_thread.start()

    output_receiver_thread.join()
    pause_listener_thread.join()


    # gaze_condition = "-g" in sys.argv
    # wizard = "-w" in sys.argv

    # if gaze_condition: 
    #     output_receiver_thread = threading.Thread(target=receiver_program, daemon=True)
    #     output_receiver_thread.start()

    # if wizard:
    #     pause_listener_thread = threading.Thread(target=pause_listener, daemon=True)
    #     pause_listener_thread.start()

    # if gaze_condition:
    #     output_receiver_thread.join()
    # if wizard:
    #     pause_listener_thread.join()
    


