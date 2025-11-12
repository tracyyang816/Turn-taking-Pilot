# this file recieves *angles* from doa.py
# this file reads image input from the camera

# when tested on robot, send gaze_tasks to gaze_intervention.py
# this file contains the GazeDecision class




import cv2
import mediapipe as mp
import numpy as np
import time
from collections import defaultdict
import matplotlib.pyplot as plt
import socket
import json
import sys
from speaker import Speaker
import threading
import random
from GazeDecision import GazeDecision
# from gaze_decision import GazeDecision

from doa_tuning import Tuning
import usb.core
import usb.util



# DELETE 
# received_angles = [] 

# def receive_angles():
#     global received_angles
#     HOST = 'localhost'
#     PORT = 50007
#     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     while True:
#         try:
#             client_socket.connect((HOST, PORT))
#             break
#         except ConnectionRefusedError:
#             time.sleep(0.5)
#     while True:
#         try:
#             data = client_socket.recv(1024)
#             if not data:
#                 break
#             payload = json.loads(data.decode('utf-8'))
#             received_angles = payload.get("angles", [])
#         except:
#             break
#     client_socket.close()

def plot_speaking_activity(speaking_activity, total_seconds_passed):
    plt.clf()
    speakers = speaking_activity.keys()
    for speaker, times in speaking_activity.items():
        for t in times:
            plt.plot([t, t], [speaker - 0.4, speaker + 0.4], color='blue')
    plt.yticks(range(len(speakers)), labels=[f'Speaker {s}' for s in speakers])
    plt.xticks(range(total_seconds_passed))
    plt.xlabel("Time (seconds)")
    plt.ylabel("Speakers")
    plt.title("Speaking Activity Over Time")
    plt.draw()
    plt.pause(0.01)

        
def send(client_socket, gaze_tasks):
    data_to_send = json.dumps(gaze_tasks)
    client_socket.sendall(data_to_send.encode())

def connect_host():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    port = 5000
    client_socket.connect((host, port))
    return client_socket


def detect_faces_and_lips(frame, face_mesh, w, h):
    results = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if not results.multi_face_landmarks:
        return None, {}, {}

    pos_list = defaultdict(list)
    lip_ratios = {}
    for i, face_landmarks in enumerate(results.multi_face_landmarks):
        upper_lip = np.array([face_landmarks.landmark[13].x * w, face_landmarks.landmark[13].y * h])
        lower_lip = np.array([face_landmarks.landmark[14].x * w, face_landmarks.landmark[14].y * h])
        top_edge = np.array([face_landmarks.landmark[10].x * w, face_landmarks.landmark[10].y * h])
        bottom_edge = np.array([face_landmarks.landmark[152].x * w, face_landmarks.landmark[152].y * h])

        lip_distance = np.linalg.norm(upper_lip - lower_lip) / h
        face_length = np.linalg.norm(top_edge - bottom_edge) / h
        ratio = lip_distance / face_length
        lip_ratios[i] = ratio

        for landmark in [13, 14]:
            x = int(face_landmarks.landmark[landmark].x * w)
            y = int(face_landmarks.landmark[landmark].y * h)
            pos_list[i] = (round(face_landmarks.landmark[landmark].x, 2), round(face_landmarks.landmark[landmark].y, 2))
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

    return results, lip_ratios, pos_list


def process_speaking_variability(lip_distances, talking_variability_threshold, is_talking_dict, speaking_activity, total_seconds_passed):
    for i in lip_distances:
        variability = np.std(lip_distances[i])
        is_talking = (variability > talking_variability_threshold)
        is_talking_dict[i] = is_talking
        if is_talking:
            speaking_activity[i].append(total_seconds_passed)
        lip_distances[i] = []
    
    return lip_distances


def create_speakers(pos_list, speaker_list, w):
    print(pos_list)
    # pos_list is a list of current speaker positions
    for i in range(0, len(pos_list)):
        speaker_list[i].set_position_and_range(pos_list[i], w)

def update_speakers(is_talking_dict, angles, speaking_activity, speaker_list):
    for i in range(0, len(speaker_list)):
        speaker = speaker_list[i]


        lip_moved = is_talking_dict[i]
        time_stamp = speaking_activity[i]

        speaker.update_lip_movement(lip_moved)
        speaker.check_if_talking(angles)
        speaker.add_speaking_activity(time_stamp)








def main():

    # DELETE
    # receiver_thread = threading.Thread(target=receive_angles, daemon=True)
    # receiver_thread.start()

    rob = "-c" in sys.argv
    plt.ion()
    fig, ax = plt.subplots()

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=2, min_detection_confidence=0.5)

    talking_variability_threshold = 0

    lip_distances = defaultdict(list)
    is_talking_dict = defaultdict(bool)
    speaking_activity = defaultdict(list)

    segment_duration = 0.2 # is_talking decision is made based on lip variability within segment_duration
    start_time = time.time()
    total_seconds_passed = 0

    speaker1 = Speaker(0)
    speaker2 = Speaker(1)
    # speaker_list = [speaker1]
    speaker_list = [speaker1, speaker2]
    speaker_created = False
    gaze_controller = GazeDecision(speaker1, speaker2, min_gaze=3.0, max_gaze=5.0)
    angles = []
    
    

    if rob:
        client_socket = connect_host()

    # initialize camera 
    cap = cv2.VideoCapture(0)

    # initialize mic array 
    device = usb.core.find(idVendor=0x2886, idProduct=0x0018)
    if device is None:
        raise ValueError("Device not found")

    if device:
        Mic_tuning = Tuning(device)
    
    # Recording

    name = input ("Participant number: ")
    fourcc = cv2.VideoWriter_fourcc(*'MP4V')  # Or 'MJPG', 'MP4V', etc.
    out = cv2.VideoWriter("Dyad" + name + "gaze.mp4" , fourcc, 20.0, (640, 480))  # filename, codec, fps, frame size

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame. Exiting...")
            break

        h, w, _ = frame.shape

        # make the frame lighter 
        frame_float = frame.astype(np.float32)
        lighter_frame = cv2.add(frame_float, 50)
        frame = np.clip(lighter_frame, 0, 255).astype(np.uint8)
        
        results, lip_ratios, pos_list = detect_faces_and_lips(frame, face_mesh, w, h)


        if pos_list and not speaker_created:
            print("create speakers", pos_list)
            create_speakers(pos_list, speaker_list, w)
            speaker_created = True

        # if results is None:
        #     cv2.putText(frame, 'No face detected', (10, 30),
        #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        #     continue

        try:
            VAD = Mic_tuning.read("VOICEACTIVITY")
            angle = Mic_tuning.read("DOAANGLE")
            if VAD:
                angles.append(angle)

        except KeyboardInterrupt:
            break


        for i in lip_ratios:
            ratio = lip_ratios[i]
            lip_distances[i].append(ratio)

        current_time = time.time()
        if current_time - start_time >= segment_duration:
            total_seconds_passed += 1
            process_speaking_variability(lip_distances, talking_variability_threshold, is_talking_dict, speaking_activity, total_seconds_passed)
            update_speakers(is_talking_dict, angles, speaking_activity, speaker_list)
            gaze_tasks = gaze_controller.gaze_decision(speaker1, speaker2)
            
            print("gaze_tasks", gaze_tasks)

            # Here on just for debugging purposes
            # print_tasks = []
            # try:
            #     for tup in gaze_tasks:
            #         if tup[1] == speaker1.position:
            #             new_tup = (tup[0], speaker1.speaker_id)
            #         if tup[1] == speaker2.position:
            #             new_tup = (tup[0], speaker2.speaker_id)
            #         print_tasks.append(new_tup)
            #     print("gaze_tasks", print_tasks)
            # except TypeError:
            #     print("None")
            #     continue

            angles = []
            start_time = current_time
            # plot_speaking_activity(speaking_activity, total_seconds_passed)
            if rob:
                send(client_socket, gaze_tasks)
        
        for speaker in speaker_list:
            if speaker.position == None:
                break
            x = speaker.position[0] * w
            y = speaker.position[1] * h
            is_talking = speaker.is_talking
            cv2.putText(frame, f'Talking: {is_talking}', (int(x)-20, int(y)-60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0) if is_talking else (0, 255, 0), 2, cv2.LINE_AA)

        cv2.putText(frame, f'Silence: {gaze_controller.silence}', (10, 30),
                         cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.putText(frame, f'Speech time ratio: {gaze_controller.speech_ratio}', (30, 60),
                         cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        out.write(frame)  # Save the frame to file
        cv2.imshow("MediaPipe Mouth Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()






