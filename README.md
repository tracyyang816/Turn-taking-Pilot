# Turn-Taking-Study-Pilot

First:
pip install requests websocket-client misty-sdk mediapipe pyaudio opencv-python

1. Make sure that Misty's router is plugged in, and that Misty II is charged and connected to the network. Connect the laptop to the same network.

2. Get Misty's IP address, usually "192.168.0.100" or "192.168.0.101". Test the connection by opening the IP in a web browser and loading misty's interface.

3. Connect both webcam and mic array to the computer. 

4. Run command. 


Always running:

python3 interface.py

python3 intervention.py (-s if running simulation)


Then depending on condition, run:

python3 output.py -g (for gaze only) / -swg (for speech with gaze) / -v (for verbal only ) 

(-s if running simulation)

5. For wizarding open up window: http://localhost:8080/ but first run interface.py.

# Turn-taking-Pilot
# Turn-taking-Pilot
