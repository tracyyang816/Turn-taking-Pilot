
import subprocess
import time 


type = input("intervention type (verbal/gaze): ")
print("\n----  Make sure that all terminals are initialized correctly, ---- \n----         and that both participants are in frame.         ----\n")

gaze_programs = [
    "python3 /Users/tracyyang/Piloting/doa.py",
    "python3 /Users/tracyyang/Piloting/gaze_intervention.py -c",
    "python3 /Users/tracyyang/Piloting/gaze_output.py -c"
]

verbal_programs = [
    "python3 /Users/tracyyang/Piloting/doa.py",
    "python3 /Users/tracyyang/Piloting/verbal_intervention.py -c",
    "python3 /Users/tracyyang/Piloting/verbal_output.py -c"
]

if type == "gaze":
    for command in gaze_programs:
        # This opens a new Terminal window and runs the command
        subprocess.run([
            'osascript', '-e',
            f'tell application "Terminal" to do script "{command}"'
        ])
        time.sleep(0.5)

else:
    for command in verbal_programs:
        # This opens a new Terminal window and runs the command
        subprocess.run([
            'osascript', '-e',
            f'tell application "Terminal" to do script "{command}"'
        ])
        time.sleep(0.5)


        




'''
if type == "gaze": 
    subprocess.Popen(["python3", "doa.py"])
    time.sleep(0.5)
    subprocess.Popen(["python3", "gaze_intervention.py"])
    time.sleep(0.5)
    subprocess.Popen(["python3", "gaze_output.py"])

else: 
    subprocess.Popen(["python3", "doa.py"])
    time.sleep(0.5)
    subprocess.Popen(["python3", "verbal_intervention.py", "-c"])
    time.sleep(0.5)
    subprocess.Popen(["python3", "verbal_output.py", "-c"])
'''


