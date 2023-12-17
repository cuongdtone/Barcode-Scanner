# import nmap
import paramiko
import socket
import os

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


def install_barcode(ssh_client):
    sftp_client = ssh_client.open_sftp()
    service_list = ['barcode-scanner', 'config-manager', 'usb-gadget-msc', 'usb-manager', 'wifi-manager']
    service_dir = '/etc/systemd/system/'
    script_dir = '/etc/'
    stdin, stdout, stderr = ssh_client.exec_command(f'sudo apt-get -y update')
    stdout.channel.recv_exit_status()
    stdin, stdout, stderr = ssh_client.exec_command(f'sudo apt-get install -y python3-pip')
    stdout.channel.recv_exit_status()
    stdin, stdout, stderr = ssh_client.exec_command(f'sudo apt-get install -y python3-dev')
    stdout.channel.recv_exit_status()
    stdin, stdout, stderr = ssh_client.exec_command(f'pip install flask')
    stdout.channel.recv_exit_status()
    stdin, stdout, stderr = ssh_client.exec_command(f'pip install evdev')
    stdout.channel.recv_exit_status()

    for service in service_list:
        execute_file = f'{service}/{service}'
        service_file = f'{service}/{service}.service'
        print(os.path.exists(execute_file), execute_file)
        print(os.path.exists(service_file), service_file)
        print()
        sftp_client.put(execute_file, f'{script_dir}/{service}')
        sftp_client.put(service_file, f'{service_dir}/{service}.service')

        ssh_client.exec_command(f'chmod +x {script_dir}/{service}')
        stdout.channel.recv_exit_status()
        stdin, stdout, stderr = ssh_client.exec_command(f'systemctl enable {service}')
        stdout.channel.recv_exit_status()
        print(stdout.read().decode())

    stdin, stdout, stderr = ssh_client.exec_command(f'systemctl daemon-reload')
    stdout.channel.recv_exit_status()
    stdin, stdout, stderr = ssh_client.exec_command(f'reboot -f')
    print(f"Orangepi: Installed")
    sftp_client.close()
    exit(0)

def scan_network():
    subnet = getNetworkIp().split('.')
    subnet.pop()
    subnet = ".".join(subnet)
    print("Subnet scanning: ", subnet)
    for i in range(1, 255):
        ip = f'{subnet}.{i}'
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
                print(f"SSH ip: {ip}: failed")

        sock.close()

scan_network()
