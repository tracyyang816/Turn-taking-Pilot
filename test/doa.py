
from doa_tuning import Tuning
import usb.core
import usb.util
import time
import socket
import json


segment_duration = 0.2
start_time = time.time()
angles = []

# Setup socket server
HOST = 'localhost'
PORT = 50007
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print("Waiting for connection on port", PORT)
conn, addr = server_socket.accept()
print("Connected by", addr)

device = usb.core.find(idVendor=0x2886, idProduct=0x0018)
if device is None:
    raise ValueError("Device not found")

if device:
    Mic_tuning = Tuning(device)
    # Mic_tuning.set_vad_threshold(7) # Modify this vad threshold based on ambient noises
    while True:
        
        try:
            VAD = Mic_tuning.read("VOICEACTIVITY")
            angle = Mic_tuning.read("DOAANGLE")
            if VAD:
                angles.append(angle)

        except KeyboardInterrupt:
            break

        current_time = time.time()
        if current_time - start_time >= segment_duration:
            try:
                payload = json.dumps({"angles": angles})
                conn.sendall(payload.encode('utf-8'))
            except:
                print("Connection lost. Exiting.")
                break
            angles = []
            start_time = current_time

conn.close()
server_socket.close()

