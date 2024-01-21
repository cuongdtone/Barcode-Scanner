# import nmap
import paramiko
import socket
import os
import concurrent.futures

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


def getNetworkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.connect(('<broadcast>', 0))
    return s.getsockname()[0]

def run_ssh_cmd(ssh_client:  paramiko.SSHClient, cmd: str):
    stdin, stdout, stderr = ssh_client.exec_command('ls -l')
    return stdout.read().decode()

def push_file(sftp_client, file, remote_path):
    sftp_client.put(file, remote_path)

def wait_ssh(stdout):
    for line in stdout:
        print(line.strip())
    stdout.channel.recv_exit_status()


def install_barcode(ssh_client):
    sftp_client = ssh_client.open_sftp()
    sftp_client.put('desktop-service/cfg.json', f'/root/cfg.json')
    sftp_client.close()

def device_setup(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((ip, 22))
    if result == 0:
        print(f"{ip} SSH openning ..")
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, port=22, username='root', password='orangepi')
            ##################################################################
            print(f"Orangepi: {ip}.")
            install_barcode(ssh)
            print(f"Orangepi: {ip}: Installed")
            ##################################################################
            ssh.close()
        except Exception as e:
            print(e)
            print(f"SSH ip: {ip}: failed")
        sock.close()

def scan_network():
    subnet = getNetworkIp().split('.')
    subnet.pop()
    subnet = ".".join(subnet)
    print("Subnet scanning:", subnet)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(1, 255):
            ip = f'{subnet}.{i}'
            futures.append(executor.submit(device_setup, ip))
        
        # Gắn kết kết quả của các tác vụ
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            # Xử lý kết quả nếu cần thiết

scan_network()
