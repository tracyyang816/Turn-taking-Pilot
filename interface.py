# address http://localhost:8080/


from flask import Flask, render_template, request, redirect, session
import socket
import threading
import json
import os
from flask import jsonify
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session support


app = Flask(__name__)
robot_host = "localhost"
command_port = 6000
status_port = 6010

# Shared state
status_data = {
    "name":"test",
    "condition":"test",
    "non_dom_id":"Player 0",
    "overlap": 0,
    "silence": 0,
    "speech_ratio": 0,
    "cur_time_passed": 0,
    "dom_pos":(0.6,0.6),
    "nondom_pos": (0.4,0.6)
}


intervention_list = []


# user_profiles = {
#     "left_user": {
#         "sequence": [(0.2, 0.6), (0.8, 0.6)]
#     },
#     "right_user": {
#         "sequence": [(0.8, 0.6), (0.2, 0.6)]
#     }
# }



@app.route("/status")
def status():
    # ADD
    
    return jsonify({
        "overlap": status_data.get("overlap"),
        "silence": status_data.get("silence"),
        "non_dom_id": status_data.get("non_dom_id"),
        "speech_ratio": status_data.get("speech_ratio"),
        "cur_time_passed": status_data.get("cur_time_passed"),
       
    })


def receive_status():
    global status_data, intervention_list
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', status_port))
    server.listen(1)
    print("[Status Server] Listening on port", status_port)

    # ADD
   

    while True:
        try:
            conn, addr = server.accept()
            print(f"[Status Server] Connection accepted from {addr}")
            buffer = ""
            intervention_list = []
            

            while True:
                data = conn.recv(1024)
                name = status_data.get("name")
                intervention_type = status_data.get("condition")
                if not data:
                    print("[Status Server] Connection closed by sender.")
                    with open(f"./data/Dyad{name}/P{name}_{intervention_type}_intervention.json", "w") as f:
                        json.dump({"Intervention Condition": intervention_type, 
                            "Intervention list": intervention_list}, 
                            f, indent=4)
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    try:
                        parsed = json.loads(line)
                        status_data.update(parsed)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[Status Server] Error: {e}")
            time.sleep(1)  # avoid rapid retry loop
        finally: 
         
            with open(f"./data/Dyad{name}/P{name}_{intervention_type}_intervention.json", "w") as f:
                json.dump({"Intervention Condition": intervention_type, 
                    "Intervention list": intervention_list}, 
                    f, indent=4)



        # conn.close()


@app.route('/')
def index():
    return render_template("interface.html", **status_data)


# @app.route('/set_user/<user>')
# def set_user(user):
#     if user in ["left_user", "right_user"]:
#         session["target_user"] = user
#     return redirect("/")

@app.route('/send_custom_command', methods=['POST'])
def send_custom_command():
    data = request.get_json()
    command = data['command']
    print(f"Custom command received: {command}")
    # You can choose to process the custom command here
    return "Received"

@app.route('/set_quick_command', methods=['POST'])
def set_quick_command():
    global quick_command
    data = request.get_json()
    quick_command = data['quick_command']
    print(f"Quick command set to: {quick_command}")
    return "OK"
    

@app.route('/send_command', methods=['POST'])
def send_command():
    global intervention_list

    
    command = request.form['command']

    print (command, " command")


    time_passed = status_data.get("cur_time_passed")
    intervention_list.append([time_passed, command])
    player_id = status_data.get("non_dom_id")

    # ADD
    custom_text = request.form.get('custom_text', '')  
    if command == "send" and custom_text:
        player_id = custom_text
        # command = f"{command}:{custom_text}"  # or use a tuple/list

    data = [command, player_id, tuple(status_data["nondom_pos"]), tuple(status_data["dom_pos"])]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((robot_host, command_port))
            data_encoded = json.dumps(data).encode('utf-8')
            s.sendall(data_encoded)

        return redirect("/")
    except Exception as e:
        print("Error in /send_command:", e)
        return "Server error", 500


if __name__ == "__main__":
    threading.Thread(target=receive_status, daemon=True).start()

    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=8080)
