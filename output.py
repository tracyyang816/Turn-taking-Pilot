
# this file reads angles input from mic array
# this file reads image input from the camera

# combined "gaze_output.py" and "verbal_output.py"
# when running on a robot, use the CLI: python3 output.py -c 
# when running verbal intervention, use the CLI: python3 output.py -v (-c if also on robot)
# when running gaze intervention, use the CLI: python3 output.py -g (-c if also on robot)

# when runnning baseline, just: python3 output.py, for data collection purposes
# the robot behavior runs independently in a separate file




import cv2
import mediapipe as mp
import numpy as np
import time
from collections import defaultdict
# import matplotlib.pyplot as plt
import socket
import json
import sys
from speaker import Speaker
import threading
import random
from VerbalDecision import VerbalDecision
from GazeDecision import GazeDecision

from doa_tuning import Tuning
import usb.core
import usb.util
import json
import queue

import sounddevice as sd
import soundfile as sf
import subprocess
from pathlib import Path
import os

# from queue import Queue

angles = []
stop_event = threading.Event()
stop_event.clear()

frame_queue = queue.Queue()

# video_queue = Queue()

        
def send(client_socket, gaze_tasks):
    data_to_send = json.dumps(gaze_tasks)
    client_socket.sendall(data_to_send.encode('utf-8'))


def connect_host():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    port = 5000
    client_socket.connect((host, port))
    return client_socket


def detect_faces_and_lips(frame, face_mesh, w, h):
    results = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if not results.multi_face_landmarks:
        return None, None

    pos_list = defaultdict(list)
    lip_ratios = {}
    if results.multi_face_landmarks:
        sorted_faces = sorted(
        results.multi_face_landmarks,
        key=lambda face: np.mean([lm.x for lm in face.landmark])
    )
        for i, face_landmarks in enumerate(sorted_faces):
            upper_lip = np.array([face_landmarks.landmark[13].x * w, face_landmarks.landmark[13].y * h])
            lower_lip = np.array([face_landmarks.landmark[14].x * w, face_landmarks.landmark[14].y * h])
            top_edge = np.array([face_landmarks.landmark[10].x * w, face_landmarks.landmark[10].y * h])
            bottom_edge = np.array([face_landmarks.landmark[152].x * w, face_landmarks.landmark[152].y * h])

            lip_distance = np.linalg.norm(upper_lip - lower_lip) / h
            face_length = np.linalg.norm(top_edge - bottom_edge) / h
            ratio = round(lip_distance / face_length, 5)
            lip_ratios[i] = ratio 
            

            for landmark in [13, 14]:
                x = round(face_landmarks.landmark[landmark].x, 2)
                y = round(face_landmarks.landmark[landmark].y, 2)
                x_dot = int(x * w)
                y_dot = int(y * h)
                cv2.circle(frame, (x_dot, y_dot), 2, (0, 255, 0), -1)
                pos_list[i] = (x, y)
    
    return lip_ratios, pos_list


def process_speaking_variability(lip_distances, talking_variability_threshold, is_talking_dict):
    for i in lip_distances:
        variability = np.std(lip_distances[i])
        is_talking = (variability > talking_variability_threshold)
        if is_talking:
            print(i, "lip talking")
        is_talking_dict[i] = is_talking
        lip_distances[i] = []


def create_speakers(pos_list, speaker_list):
    # pos_list is a list of current speaker positions
    for i in range(0, len(pos_list)):
        speaker_list[i].set_position_and_range(pos_list[i])

def update_speakers(is_talking_dict, angles, speaker_list):
    for i in range(0, len(speaker_list)):
        speaker = speaker_list[i]
        lip_moved = is_talking_dict[i]

        speaker.update_lip_movement(lip_moved)
        speaker.check_if_talking(angles)


def receive_angles(Mic_Tuning):
    global angles, stop_event
    while not stop_event.is_set():
        try:
            VAD = Mic_Tuning.read("VOICEACTIVITY")
            angle = Mic_Tuning.read("DOAANGLE")
            if VAD:
          
                angles.append(angle)
        except KeyboardInterrupt:
            break

            
# def video_writer(video_out):
#     while True:
#         frame = video_queue.get()
#         if frame is None: 
#             break
#         video_out.write(frame)




def show_video():
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            cv2.imshow("MediaPipe Mouth Detection", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            break
    cv2.destroyAllWindows()

def record_audio(audio_out, samplerate=44100, channels=1):

    frames = []  # We'll collect chunks here

    def callback(indata, frames_count, time_info, status):
        if stop_event.is_set():
            raise sd.CallbackStop()  # Stop the stream gracefully
        frames.append(indata.copy())

    with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
        print("Recording audio... Press Ctrl+C to stop early.")
        while not stop_event.is_set():
            time.sleep(0.1)  # Keep thread alive while recording

    # Concatenate all chunks and write to a file
    audio_data = np.concatenate(frames, axis=0)
    sf.write(audio_out, audio_data, samplerate)
    print(f"Audio saved: {audio_out}")




def main():
    global angles
 

    sim = "-s" in sys.argv
    
    if "-g" in sys.argv:
        intervention_type = "gaze"
        wizard = False
    if "-swg" in sys.argv:
        intervention_type = "speech_w_gaze"
        wizard = True
    elif "-v" in sys.argv:
        intervention_type = "verbal"
        wizard = True

    name = input ("Participant number: ")
    folder = Path(f"./data/Dyad{name}/")
    folder.mkdir(parents=True, exist_ok=True)  # Creates the folder
    video_path = f"./data/Dyad{name}/P{name}_{intervention_type}_video.mp4"
    audio_path = f"./data/Dyad{name}/P{name}_{intervention_type}_audio.wav"
    final_path = f"./data/Dyad{name}/P{name}_{intervention_type}_merged.mp4"

    audio_thread = threading.Thread(target = record_audio, args=(audio_path,))
   
    
    # initialize mic array 
    if not sim:
        device = usb.core.find(idVendor=0x2886, idProduct=0x0018)
        if device is None:
            raise ValueError("Device not found")
        if device:
            Mic_tuning = Tuning(device)
            Mic_tuning.set_vad_threshold(5) # Modify this vad threshold based on ambient noises

        receive_angle_thread = threading.Thread(target = receive_angles, args = (Mic_tuning, ))
        receive_angle_thread.start()

    global angles

    mp_face_mesh = mp.solutions.face_mesh
    confidence = 0.5
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=2, min_detection_confidence = confidence) # (static_image_mode=False, max_num_faces=2, min_detection_confidence = 0.5)
    talking_variability_threshold = 0.0045

    lip_distances = defaultdict(list)
    is_talking_dict = defaultdict(bool)

    segment_duration = 0.2 # is_talking decision is made based on lip variability and angles within segment_duration
    start_time = time.time()

    speaker1 = Speaker("Player 0")
    speaker2 = Speaker("Player 0")
    speaker_list = [speaker1, speaker2]
    speaker_created = False
    angles = []
    cam_failure = 0
    audio_started = False
    

    controller = GazeDecision(speaker1, speaker2, min_gaze=3.0, max_gaze=5.0)
    client_socket = connect_host() # sending to intervention.py
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")


    # recording
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  
    outpath = os.path.abspath(f"./data/Dyad{name}/P{name}_{intervention_type}_video.mp4")
    video_out = cv2.VideoWriter(outpath, fourcc, 20.0, (w, h))

    # timestamp
    time_passed = 0
    intervention_activity = []
    speech_ratios = []
   
    status_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    status_socket.connect(('localhost', 6010))  # Connect to web interface

    fps = 20.0
    frame_interval = 1.0 / fps

    try:
        # Repeat to read from sensors 
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame. Exiting...")
                break

            h, w, _ = frame.shape    
            frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=50)
            lip_ratios, pos_list = detect_faces_and_lips(frame, face_mesh, w, h)

            

            # initialization check 
            # once correctly intialized will skip this part
            if not speaker_created:
                cam_failure +=1 

                if not pos_list:
                    continue

                if sim:
                    create_speakers(pos_list, speaker_list)
                    speaker_created = True
                    voice_only = False

                # if we already failed the camera initialization check, now fall back on voice activity 
                # we initialize pos_list and is_talking_dict, by default we assume lips are moving 
                voice_only = (cam_failure >= 120)
                if voice_only:
                    pos_list = [(0.3, 0.6), (0.7, 0.6)]
                    create_speakers(pos_list, speaker_list)
                    is_talking_dict[0] = False
                    is_talking_dict[1] = False
                    speaker_created = True
                    print("Voice-only detection activated.")
                    continue

                # check how many faces are detected 
                face_detected = len(pos_list)

                if face_detected == 2: 
                    correct_pos = pos_list[0][0] < 0.5 and pos_list[1][0] > 0.5 # or (pos_list[1][0] < 0.5 and pos_list[0][0] > 0.5)
                    if correct_pos:
                        create_speakers(pos_list, speaker_list)
                        speaker_created = True
                        voice_only = False
                        print("Speaker correctly intitialized.")
                    else:
                        print("Two speakers detected, but not correctly initialized.")
                        continue 

                else: # less than 2 faces detected
                    confidence -= 0.05 # decrease the detection confidence and rerun 
                    # print('Only '+ str(face_detected) + " face detected.")
                    continue 
            
            

            # TEST
            # angles = receive_angles(Mic_tuning)
            # populate the lip_distances list with variations of lip movement during this segment
            if lip_ratios is not None:
                for i in lip_ratios:
                    ratio = lip_ratios[i]
                    lip_distances[i].append(ratio)


            current_time = time.time()
            if current_time - start_time >= segment_duration:
                time_passed += segment_duration
                
                if not voice_only: # if we are not using voice only
                    process_speaking_variability(lip_distances, talking_variability_threshold, is_talking_dict)

                update_speakers(is_talking_dict, angles, speaker_list)

                if intervention_type == "verbal": # speech without gaze
                    _ = controller.gaze_decision(speaker1, speaker2)
                    tasks = "random_movements"
                else:
                    tasks = controller.gaze_decision(speaker1, speaker2)

                if tasks == []:
                    tasks = None

                # ADD: Send to interface 
                if intervention_type == "verbal":
                    dom_pos =  (0.45 + 0.01 * random.randint(0, 10), 0.6)
                    nondom_pos = (0.45 + 0.01 * random.randint(0, 10), 0.6)
                else:
                    dom_pos = controller.dom.position
                    nondom_pos = controller.non_dom.position


                status_payload = {
                    "name": name,
                    "condition": intervention_type,
                    "non_dom_id":controller.non_dom.speaker_id,
                    "overlap": controller.overlap,
                    "silence": controller.silence,
                    "speech_ratio": controller.speech_ratio,
                    "cur_time_passed": time_passed,
                    "dom_pos": dom_pos,
                    "nondom_pos": nondom_pos,
                }
                try:
                    status_socket.sendall((json.dumps(status_payload) + "\n").encode())
                except:
                    pass  # Don’t crash on failure

                print("angles: ", angles)

                # Misty Logs
                intervention_activity.append((time_passed, tasks))
                speech_ratios.append((time_passed, controller.speech_ratio))
                

                # finish up
                angles = []
      
                start_time = current_time
                send(client_socket, tasks)
            
            for speaker in speaker_list:
                if speaker.position == None:
                    break
                x = speaker.position[0] * w
                y = speaker.position[1] * h
                speaker_talking = speaker.is_talking
                cv2.putText(frame, f'Talking: {speaker_talking}', (int(x)-20, int(y)-60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0) if speaker_talking else (0, 255, 0), 2, cv2.LINE_AA)

                cv2.putText(frame, f'Silence: {controller.silence}', (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

                cv2.putText(frame, f'Speech time ratio: {controller.speech_ratio}', (30, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)


            
            # video_out.write(frame)
            # if not video_out.isOpened():
            #     raise RuntimeError(f"VideoWriter could not open")
       
            cv2.imshow("MediaPipe Mouth Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break

            if not audio_started:
                audio_thread.start()
                audio_started = True

    


    finally:
        print("Cleaning up...")
        stop_event.set()
    
        with open(f"./data/Dyad{name}/P{name}_{intervention_type}_output.json", "w") as f:
            json.dump({"Intervention Activity": intervention_activity, 
                "Speech Ratios": speech_ratios, 
                "Speaker 1 Activity": speaker1.speaking_activity, 
                "Speaker 2 actvity": speaker2.speaking_activity}, 
                f, indent=4)
      
        client_socket.close()
        cap.release()
        video_out.release()
        cv2.destroyAllWindows()
        
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, stopping thread...")

    finally:
        stop_event.set()
        print("stop")
        if not sim:
            receive_angle_thread.join()
        audio_thread.join()


  
    
    # print("Merging with ffmpeg...")
    # subprocess.run([
    #     'ffmpeg', '-y', '-i', video_path, '-i', audio_path,
    #     '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', final_path
    # ])

      # stop_event.set()
    # if not sim:
    #     receive_angle_thread.join()  # Wait for thread to finish
    #     usb.util.dispose_resources(device)


if __name__ == "__main__":
    main()
