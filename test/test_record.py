# this file test recording a data stream
# # and replaying that data stream

import random


# record_stream.py
import time
import json

def record_data(get_data_fn, duration_sec=10, save_path="recorded_data.json"):
    """
    get_data_fn: function that returns current mic data (e.g., list of angles)
    duration_sec: how long to record
    """
    data_log = []
    start_time = time.time()

    print("Recording started...")
    while time.time() - start_time < duration_sec:
        current_time = time.time() - start_time  # relative timestamp
        data = get_data_fn()
        data_log.append({"time": current_time, "data": data})
        time.sleep(0.01)  # adjust this to your mic sampling rate

    with open(save_path, "w") as f:
        json.dump(data_log, f, indent=2)
    print(f"Recording saved to {save_path}")



# replay_stream.py
import json
import time

def replay_data(filename="recorded_data.json", send_fn=print):
    with open(filename, "r") as f:
        data_log = json.load(f)

    print("Replaying...")
    start_time = time.time()

    for i, entry in enumerate(data_log):
        if i == 0:
            delay = entry["time"]
        else:
            delay = entry["time"] - data_log[i-1]["time"]
        
        time.sleep(delay)
        send_fn(entry["data"])


def fake_mic():
    return [random.uniform(0, 180) for _ in range(3)]

# record for 5 seconds
record_data(fake_mic, duration_sec=5)

# replay using a custom function
replay_data(send_fn=lambda x: print("Replaying:", x))
