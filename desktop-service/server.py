import json
import time
import os
import requests
from threading import Thread
import json

from flask import Flask, request, jsonify, send_file, Response
from queue import Queue
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

app = Flask(__name__)

max_longevity = 30

cfg  = {'source_dir': None}
active_devices_dict = {}
cache_path = 'cache_active_devices_dict.json'
cache_path_cfg = 'cache_cfg.json'

if os.path.exists(cache_path):
    with open(cache_path, 'r') as file:
        active_devices_dict = json.load(file)

if os.path.exists(cache_path_cfg):
    with open(cache_path_cfg, 'r') as file:
        cfg = json.load(file)
        cfg['case_sensitivity'] = True

for client_ip in active_devices_dict.keys():
    active_devices_dict[client_ip]['longevity'] = max_longevity

barcode_stream = Queue(maxsize=200)

def dump_cache():
    with open(cache_path, 'w') as file:
        json.dump(active_devices_dict, file)

def dump_cfg():
    with open(cache_path_cfg, 'w') as file:
        json.dump(cfg, file)

def alive_thread():
    global active_devices_dict
    while True:
        active_devices_dict_temp = active_devices_dict.copy()
        for client_ip in active_devices_dict_temp.keys():
            if active_devices_dict_temp[client_ip]['longevity'] < 0:
                if active_devices_dict_temp[client_ip]['alive'] == True:
                    active_devices_dict_temp[client_ip]['alive'] = False
                    barcode_stream.put(f'[DRA]')
            else:
                active_devices_dict_temp[client_ip]['longevity'] -= 1 
  
        active_devices_dict = active_devices_dict_temp
        time.sleep(1)

Thread(target=alive_thread).start()

@app.route('/barcode', methods=['POST'])
def barcode():
    data = request.get_json()
    barcode = data['barcode']
    client_ip = request.remote_addr
    dir_barcode = cfg.get('source_dir')
    if client_ip not in active_devices_dict.keys():
    #     dir_barcode = active_devices_dict[client_ip]['dir']
    # else:
        barcode_stream.put(f'{now} [{client_ip}] Barcode sent from unregister device')
        return "clean"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    ###########################################
    if dir_barcode is not None:
        # if client_ip in active_devices_dict.keys():
        #     barcode_stream.put(f'{now} [{active_devices_dict[client_ip]["name"]}] Barcode {barcode} file sent')
        file_path = f'{dir_barcode}/{barcode}'
        if not os.path.exists(file_path):
            if cfg['case_sensitivity']:
                for ff in os.listdir(dir_barcode):
                    fo = ff
                    if str(ff).lower() == str(barcode).lower():
                        file_path = f'{dir_barcode}/{fo}'
                        break

        if os.path.exists(file_path):
            barcode_stream.put(f'{now} [{active_devices_dict[client_ip]["name"]}] Barcode {barcode} file sent')
            return send_file(file_path, download_name=os.path.basename(file_path), as_attachment=True)
        else:
            barcode_stream.put(f'{now} [{active_devices_dict[client_ip]["name"]}] Barcode {barcode} - File is not existed')
    else:
        barcode_stream.put(f'{now} [{active_devices_dict[client_ip]["name"]}] Barcode {barcode} - Source folder is not selected')
    return "clean"

@app.route('/usb_file_event', methods=['POST'])
def usb_content():
    client_ip = request.remote_addr
    data = request.get_json()
    fname = data['fname']
    if client_ip in active_devices_dict.keys():
        active_devices_dict[client_ip]['usb'] = fname
    barcode_stream.put(f'[DRA]')


@app.route('/usb_clean', methods=['POST'])
def usb_clean():
    client_ip = request.remote_addr
    if client_ip in active_devices_dict.keys():
        active_devices_dict[client_ip]['usb'] = None
    barcode_stream.put(f'[DRA]')


@app.route('/shutdown', methods=['POST'])
def shutdown():
    dump_cache()
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
    if client_ip in active_devices_dict.keys():
        barcode_stream.put(f'{now} [{active_devices_dict[client_ip]["name"]}] {msg}')
    return "ok"

@app.route('/device_register', methods=['POST'])
def devices_register():
    global active_devices_dict
    data = request.get_json()
    device_id = data['device_id']
    client_ip = request.remote_addr
    if client_ip in active_devices_dict.keys():
        if active_devices_dict[client_ip]['alive'] is False:
            active_devices_dict[client_ip]['alive'] = True
            barcode_stream.put(f'[DRA]')

        active_devices_dict[client_ip]['longevity'] = max_longevity

        if active_devices_dict[client_ip]['name'] != device_id:
            barcode_stream.put(f'Device name changed: {active_devices_dict[client_ip]["name"]} -> {device_id}')
            active_devices_dict[client_ip]['name'] = device_id
            barcode_stream.put(f'[DRA]')
        return 'ok'

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    barcode_stream.put(f'[DRA] {now} [{client_ip}] New Device register!')

    active_devices_dict.update({client_ip: {"name": device_id, "dir": None, "alive": True, "longevity": max_longevity, "usb": None}})
    return "ok"


@app.route('/remove_device', methods=['POST'])
def remove_device():
    global active_devices_dict
    data = request.get_json()
    device_id = data['device_id']
    if device_id in list(active_devices_dict.keys()):
        del active_devices_dict[device_id]
        barcode_stream.put(f'Removed device {device_id}')
    dump_cache()
    return "ok"

@app.route('/clear_cache', methods=['GET'])
def clear_cache():
    global active_devices_dict
    if os.path.exists(cache_path):
        os.remove(cache_path)
    active_devices_dict = {}
    barcode_stream.put(f'Clear cache')
    dump_cache()
    return "ok"

@app.route('/select_dir', methods=['POST'])
def select_dir():
    global active_devices_dict
    data = request.get_json()
    # client_ip = data['device_ip']
    # active_devices_dict[client_ip]['dir'] = data['dir']
    cfg['source_dir'] = data['dir']
    dump_cfg()
    return "ok"

@app.route('/case_sensitivity', methods=['POST'])
def case_sensitivity():
    global active_devices_dict
    data = request.get_json()
    # client_ip = data['device_ip']
    # active_devices_dict[client_ip]['dir'] = data['dir']
    cfg['case_sensitivity'] = data['case_sensitivity']
    # print(data)
    barcode_stream.put(f'Switch case_sensitivity mode: {cfg["case_sensitivity"]}')
    dump_cfg()
    return "ok"

@app.route('/change_name', methods=['POST'])
def change_name():
    global active_devices_dict
    data = request.get_json()
    client_ip = data['device_ip']
    active_devices_dict[client_ip]['name'] = data['name']
    dump_cache()
    return "ok"

@app.route('/devices', methods=['GET'])
def devices():
    global active_devices_dict
    active_devices_list = []
    for client_ip, value in active_devices_dict.items():
        device_id = value['name']
        status = value['alive']
        source_folder = cfg.get('source_dir')
        usb = value['usb']
        active_devices_list.append([device_id, client_ip, status, source_folder, usb])
    active_devices_list =  sorted(active_devices_list, key=lambda x: x[0])
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

@app.route('/upload', methods=['POST'])
def upload():
    def upload_task(ip, name, path):
        url = f'http://{ip}:8080/upload'
        with open(path, 'rb') as file:
            try:
                response = requests.post(url, files={'file': file})
                if response.status_code != 200:
                    barcode_stream.put(f"[IS]  Device offline: [{name}][{response.status_code}]!!\n")
                else:
                    barcode_stream.put(f"[IS] Uploaded: [{name}][{response.status_code}]!!\n")
            except:
                barcode_stream.put(f"[IS] Cannot upload: [{name}][Connect error]!!\n")

    data = request.get_json()
    file_path = data.get('fpath')
    ip = data.get('ip')
    name = data.get('name')
    if file_path and ip:
        Thread(target=upload_task, args=(ip, name, file_path, )).start()
    else:
        barcode_stream.put(f"[IS] Cannot upload: [{name}][Task error]!!\n")
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081, debug=False)
