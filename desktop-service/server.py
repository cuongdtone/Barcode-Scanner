import json
import time
import os

from flask import Flask, request, jsonify, send_file, Response
from queue import Queue
from datetime import datetime

app = Flask(__name__)

active_devices_dict = {}
active_devices_list = []
barcode_stream = Queue(maxsize=100)

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


@app.route('/logger', methods=['GET'])
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
    for a in active_devices_list:
        a_device_id, a_client_ip = a
        if a_client_ip == client_ip:
            return "ok"
    active_devices_list.append([device_id, client_ip])
    active_devices_dict.update({client_ip: {"name": device_id, "dir": None}})
    return "ok"

@app.route('/select_dir', methods=['POST'])
def select_dir():
    data = request.get_json()
    client_ip = data['device_ip']
    active_devices_dict[client_ip]['dir'] = data['dir']
    return "ok"

@app.route('/devices', methods=['GET'])
def devices():
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
    app.run(host='0.0.0.0', port=8080, debug=False)