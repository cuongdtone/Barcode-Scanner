import json
import time
import os
import requests
from threading import Thread
import json

from flask import Flask, request, jsonify, send_file, Response
from queue import Queue
from datetime import datetime

app = Flask(__name__)

active_devices_dict = {}
cache_path = 'cache_active_devices_dict.json'
if os.path.exists(cache_path):
    with open(cache_path, 'r') as file:
        active_devices_dict = json.load(file)

barcode_stream = Queue(maxsize=100)

def alive_thread():
    global active_devices_dict
    while True:
        off_list = []
        for client_ip in active_devices_dict.keys():

            url = f'http://{client_ip}:8080/alive'
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                respone = requests.get(url, timeout=1)
                if respone.status_code == 200:
                    if active_devices_dict[client_ip]['alive'] == False:
                        active_devices_dict[client_ip]['alive'] = True
                        barcode_stream.put(f'{now} [{client_ip}] Device online')
                else:
                    if active_devices_dict[client_ip]['alive'] == True:
                        active_devices_dict[client_ip]['alive'] = False
                        barcode_stream.put(f'{now} [{client_ip}] Device offline')
                    off_list.append(client_ip)

            except:
                if active_devices_dict[client_ip]['alive'] == True:
                    active_devices_dict[client_ip]['alive'] = False
                    barcode_stream.put(f'{now} [{client_ip}] Device offline')
                off_list.append(client_ip)
        # for clip in off_list:
        #     active_devices_dict[clip]['name'] = 'Offline'
        time.sleep(1)

Thread(target=alive_thread).start()

@app.route('/barcode', methods=['POST'])
def barcode():
    data = request.get_json()
    barcode = data['barcode']
    print("Barcode: ", barcode)
    client_ip = request.remote_addr
    dir_barcode = None
    if client_ip in active_devices_dict.keys():
        dir_barcode = active_devices_dict[client_ip]['dir']
        if dir_barcode is None:
            barcode += " - Not selected folder"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    barcode_stream.put(f'{now} [{client_ip}] Barcode: {barcode}')

    ###########################################
    if dir_barcode is not None:
        file_path = f'{dir_barcode}/{barcode}'
        if os.path.exists(file_path):

            with open(file_path, 'ab+') as file:
                file.seek(5 * 1024 * 1024)  # Seek to 100MB position
                file.truncate()
            return send_file(file_path, download_name=os.path.basename(file_path), as_attachment=True)
    else:
        return "ok"
    return "ok"

@app.route('/shutdown', methods=['POST'])
def shutdown():
    for k in active_devices_dict.keys():
        active_devices_dict[k]['alive'] = False
    with open(cache_path, 'w') as file:
        json.dump(active_devices_dict, file)
    if request.remote_addr == '127.0.0.1':
        os.kill(os.getpid(), 9)
        return 'Server is shutting down...'
    else:
        return 'Permission denied.'

@app.route('/logger', methods=['POST'])
def logger():
    data = request.get_json()
    msg = data['msg']
    client_ip = request.remote_addr
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    barcode_stream.put(f'{now} [{client_ip}] {msg}')
    return "ok"

@app.route('/device_register', methods=['POST'])
def devices_register():
    data = request.get_json()
    device_id = data['device_id']
    client_ip = request.remote_addr
    if client_ip in active_devices_dict.keys():
        return 'ok'
    
    client_ip = request.remote_addr
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    barcode_stream.put(f'{now} [{client_ip}] New Device register !!')

    active_devices_dict.update({client_ip: {"name": device_id, "dir": None, "alive": True}})
    return "ok"

@app.route('/select_dir', methods=['POST'])
def select_dir():
    data = request.get_json()
    client_ip = data['device_ip']
    active_devices_dict[client_ip]['dir'] = data['dir']
    return "ok"

@app.route('/devices', methods=['GET'])
def devices():
    active_devices_list = []
    for client_ip, value in active_devices_dict.items():
        device_id = value['name']
        status = value['alive']
        if status is True:
            active_devices_list.append([device_id, client_ip, status])
    return jsonify(active_devices_list)

@app.route('/stream')
def stream_data():
    def generate():
        while True:
            if not barcode_stream.empty():
                barcode = barcode_stream.get()
                yield barcode + "\n"
            time.sleep(0.2)
    return Response(generate(), mimetype='text/plain')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081, debug=False)
