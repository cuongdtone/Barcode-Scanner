import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QLabel, QVBoxLayout, QWidget, QListWidget, QPushButton, \
    QTableWidget, QTableWidgetItem, QTextEdit, QLineEdit, QDialog, \
    QHBoxLayout, QStyledItemDelegate, QStyle, QDialogButtonBox, \
    QDialogButtonBox, QGridLayout, QFileDialog, QAbstractItemView, QRadioButton, QCheckBox
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QPalette

from PyQt5.QtCore import Qt
from PyQt5.QtCore import Qt, QObject, pyqtSignal
import os
import time
from threading import Thread
import requests

class CircularDotDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        color = index.data(Qt.DecorationRole)
        text = index.data(Qt.DisplayRole)

        if color.isValid() and option.state & QStyle.State_Enabled:

            radius = min(option.rect.width(), option.rect.height()) * 0.4
            left = option.rect.left() + radius

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(left), round(option.rect.center().y() - radius/2), int(radius), int(radius))

        # Draw the text
        text_rect = option.rect.adjusted(int(radius*2 + 10), 0, 0, 0)
        painter.setPen(QPen(option.palette.color(QPalette.Text)))
        painter.drawText(text_rect, Qt.AlignVCenter, text)

        painter.restore()


class EditDeviceDialog(QDialog):
    def __init__(self, parent=None):
        super(EditDeviceDialog, self).__init__(parent)
        self.setWindowTitle("Edit Device")
        self.apply_all = True
    
    def init(self, name):
        self.label1 = QLabel("Name:")
        self.line_edit1 = QLineEdit(name)
        self.label2 = QLabel("WIFI SSID")
        self.line_edit2 = QLineEdit()

        self.label3 = QLabel("Password")
        self.line_edit3 = QLineEdit()

        self.label4 = QLabel("HOST IP")
        self.line_edit4 = QLineEdit()

        self.label5 = QLabel("PORT")
        self.line_edit5 = QLineEdit("8081")

        self.apply_wf_config = QCheckBox("Aplly for all")
        self.apply_wf_config.setChecked(True)
        self.apply_wf_config.clicked.connect(self.handle_ap_button)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout = QGridLayout()
        layout.addWidget(self.label1, 0, 0)
        layout.addWidget(self.line_edit1, 0, 1)
        layout.addWidget(self.label2, 1, 0)
        layout.addWidget(self.line_edit2, 1, 1)
        layout.addWidget(self.label3, 2, 0)
        layout.addWidget(self.line_edit3, 2, 1)
        layout.addWidget(self.label4, 3, 0)
        layout.addWidget(self.line_edit4, 3, 1)
        layout.addWidget(self.label5, 4, 0)
        layout.addWidget(self.line_edit5, 4, 1)

        layout.addWidget(self.apply_wf_config, 5, 0)
    
        layout.addWidget(self.button_box, 6, 0, 1, 2) 

        self.setLayout(layout)
    
    def handle_ap_button(self, state):
        self.apply_all = state

    def get_data(self):
        return self.line_edit1.text(), self.line_edit2.text(), self.line_edit3.text(), self.line_edit4.text(), self.line_edit5.text()
    

class AddDeviceDialog(QDialog):
    def __init__(self, parent=None):
        super(AddDeviceDialog, self).__init__(parent)
        self.setWindowTitle("Add Device")
        
        self.label1 = QLabel("Name:")
        self.line_edit1 = QLineEdit()
        self.label2 = QLabel("IP Address:")
        self.line_edit2 = QLineEdit()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout = QGridLayout()
        layout.addWidget(self.label1, 0, 0)
        layout.addWidget(self.line_edit1, 0, 1)
        layout.addWidget(self.label2, 1, 0)
        layout.addWidget(self.line_edit2, 1, 1)
        layout.addWidget(self.button_box, 2, 0, 1, 2)  # Trải dài button_box qua 2 cột

        self.setLayout(layout)
        
    def get_data(self):
        return self.line_edit1.text(), self.line_edit2.text()



class DeviceStatus(QObject):
    statusChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.status = 1

    def str_status(self):
        return "Online" if self.status else "Offline"

    def color_status(self):
        return QColor("green") if self.status else QColor("red")
    
    def set_online(self):
        self.status = 1
        self.statusChanged.emit()  # Emit the custom signal

    def set_offline(self):
        self.status = 0
        self.statusChanged.emit()  # Emit the custom signal



class Device(QObject):
    nameChanged = pyqtSignal()
    sourceFolderChanged = pyqtSignal()

    def __init__(self, name, ip):
        super().__init__()
        self.name = name
        self.ip = ip
        self.source_folder = None
        self.status = DeviceStatus()
        self.usb = None
        self.wifi_signal = '11'
        self.wifi_quality = '11'
        self.usb_busy = False

    def is_online(self):
        return self.status.status

    def set_online(self):
        self.status.set_online()

    def set_offline(self):
        self.status.set_offline()

    def rename(self, new_name):
        self.name = new_name
        self.nameChanged.emit()
    
    def set_source_folder(self, fpath):
        self.source_folder = fpath
        self.sourceFolderChanged.emit()

class UpdateGUI(QObject):
    reloadSignal = pyqtSignal()
    addLog = pyqtSignal()
    uploadEnable = pyqtSignal()
    uploadDisable = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.log = None
    
    def reload(self):
        self.reloadSignal.emit()

    def logger(self, msg):
        self.log = msg
        # print(msg)
        self.addLog.emit()
    
    def enable_upload(self):
        self.uploadEnable.emit()

    def disable_upload(self):
        self.uploadDisable.emit()
        
        
class DeviceManagerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EmbConnect Wifi")
        self.setFixedSize(1200, 900)
        # self.resize(1100, 600)
        button_width = 120

        self.devices = []
        self.get_devices()
        self.update_gui = UpdateGUI()
        self.update_gui.reloadSignal.connect(self.reload)
        self.update_gui.addLog.connect(self.add_log)
        self.update_gui.uploadEnable.connect(self.enable_upload_button)
        self.update_gui.uploadDisable.connect(self.disable_upload_button)


        self.selected_device = None

        self.device_table_widget = QTableWidget()
        self.device_table_widget.setColumnCount(6)
        self.device_table_widget.setItemDelegateForColumn(2, CircularDotDelegate())
        self.device_table_widget.setColumnWidth(0, 100)
        self.device_table_widget.setColumnWidth(1, 200)
        self.device_table_widget.setColumnWidth(4, 300)
        self.device_table_widget.setColumnWidth(5, 300)
        self.device_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.device_table_widget.setFixedHeight(600)

        self.device_table_widget.setHorizontalHeaderLabels(
            ["Wifi", "Name", "Status", "IP", "Source Folder", "USB File"])
        self.populate_device_table()

        self.device_table_widget.cellClicked.connect(self.device_selected)

        self.device_info_label = QLabel("Select a device to view its info.")

        self.add_button = QPushButton("Add Device")
        self.add_button.clicked.connect(self.add_device)
        self.add_button.setFixedWidth(button_width)

        self.remove_button = QPushButton("Remove Device")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self.remove_device)
        self.remove_button.setFixedWidth(button_width)

        self.reload_button = QPushButton("Reload")
        self.reload_button.setEnabled(True)
        self.reload_button.clicked.connect(self.reload)
        self.reload_button.setFixedWidth(button_width)

        self.clear_button = QPushButton("Clear log")
        self.clear_button.setEnabled(True)
        self.clear_button.clicked.connect(self.clear_log)
        self.clear_button.setFixedWidth(button_width)
    
        self.setup_button = QPushButton("Edit Device")
        self.setup_button.setEnabled(False)
        self.setup_button.clicked.connect(self.edit_device)

        self.upload_button = QPushButton("Upload")
        self.upload_button.setEnabled(False)
        self.upload_button.clicked.connect(self.upload_to_device)

        self.select_folder_button = QPushButton("Source Folder")
        self.select_folder_button.setEnabled(False)
        self.select_folder_button.clicked.connect(self.select_source_folder)

        self.cs_button1 = QCheckBox("Case Sensitivity")
        self.cs_button1.setChecked(True)
        self.cs_button1.clicked.connect(self.handle_cs_button)

        self.clear_usb_button = QPushButton("Clear USB")
        self.clear_usb_button.setEnabled(False)
        self.clear_usb_button.clicked.connect(self.clear_usb)

        self.repair_usb_button = QPushButton("Repair USB")
        self.repair_usb_button.setEnabled(False)
        self.repair_usb_button.clicked.connect(self.repair_usb)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("border: 1px solid black;")

        central_widget = QWidget()
        layout = QVBoxLayout()
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addWidget(self.clear_button)

        button_device_layout = QHBoxLayout()
        button_device_layout.addWidget(self.setup_button)
        button_device_layout.addWidget(self.upload_button)
        button_device_layout.addWidget(self.select_folder_button)
        button_device_layout.addWidget(self.cs_button1)
        button_device_layout.addWidget(self.clear_usb_button)
        button_device_layout.addWidget(self.repair_usb_button)

        layout.addLayout(button_layout)
        layout.addWidget(self.device_table_widget)
        layout.addLayout(button_device_layout)

        layout.addWidget(self.device_info_label)
        layout.addWidget(self.log_text_edit)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.alive = True
        Thread(target=self.update_screen).start()

    def handle_cs_button(self, state):
        url = f'http://127.0.0.1:8081/case_sensitivity'
        try:
            response = requests.post(url, json={'case_sensitivity': state})
        except:
            pass

    def repair_usb(self):
        if self.selected_device:
            url = f'http://{self.selected_device.ip}:8080/repair'
            try:
                response = requests.get(url)
                self.reload()
            except:
                pass
    
    def clear_usb(self):
        if self.selected_device:
            url = f'http://{self.selected_device.ip}:8080/clean'
            try:
                self.disable_upload_button()
                response = requests.get(url)
                self.reload()
            except:
                pass

    def clear_cache(self):
        url = 'http://127.0.0.1:8081/clear_cache'
        try:
            response = requests.get(url)
            self.reload2()
        except:
            pass

    def clear_log(self):
        self.log_text_edit.clear()
    
    def enable_upload_button(self):
        self.upload_button.setEnabled(True)

    def disable_upload_button(self):
        self.upload_button.setEnabled(False)
    
    def update_screen(self):
        url = 'http://127.0.0.1:8081/stream'
        try:
            response = requests.get(url, stream=True)
            for line in response.iter_lines():
                if self.alive:
                    if line:
                        try:
                            text_line = line.decode('utf-8')
                            if text_line.startswith('[DRA]'):
                                self.update_gui.reload()
                            else:
                                self.update_gui.logger(text_line)
                        except:
                            continue
                else:
                    break
        except:
            return 
    
    def add_log(self):
        sender = self.sender()
        self.log_text_edit.append(sender.log)

    def get_devices(self):
        try:
            url = 'http://127.0.0.1:8081/devices'
            response =  requests.get(url).json()
            self.devices = []
            for dev in response:
                try:
                    name, ip, status, source_folder, usb, wifi_signal, wifi_quality, usb_busy = dev
                    d = Device(name, ip)
                    d.status = DeviceStatus()
                    d.status.status = int(status)
                    d.source_folder = source_folder
                    d.usb = usb
                    d.wifi_quality = wifi_quality
                    d.wifi_signal = wifi_signal
                    d.usb_busy = usb_busy
                    self.devices.append(d)
                except:
                    pass
        except:
            return []

    def closeEvent(self, event):
        print("Closing the application...")
        self.alive = False

        url = 'http://127.0.0.1:8081/shutdown'
        try:
            response = requests.post(url)
        except:
            pass

    def add_device_raw(self, name, ip):
        self.device_table_widget.setRowCount(len(self.devices) + 1)
        device = Device(name, ip)
        device.nameChanged.connect(self.update_name_item)
        device.sourceFolderChanged.connect(self.update_source_folder_item)

        row = len(self.devices)
        signal_item = QTableWidgetItem("10/10")
        name_item = QTableWidgetItem(device.name)

        device.status.statusChanged.connect(self.update_status_item)
        device.set_offline()

        status_item_gui = QTableWidgetItem(device.status.str_status())
        status_item_gui.setData(Qt.DecorationRole, device.status.color_status())

        ip_item = QTableWidgetItem(device.ip)
        info_item = QTableWidgetItem(device.source_folder)

        usb_status_item = QTableWidgetItem(device.source_folder)

        self.devices.append(device)

        self.device_table_widget.setItem(row, 0, signal_item)
        self.device_table_widget.setItem(row, 1, name_item)
        self.device_table_widget.setItem(row, 2, status_item_gui)
        self.device_table_widget.setItem(row, 3, ip_item)
        self.device_table_widget.setItem(row, 4, info_item)
        self.device_table_widget.setItem(row, 5, usb_status_item)


    def populate_device_table(self):
        self.device_table_widget.setRowCount(len(self.devices))

        for row, device in enumerate(self.devices):

            signal_item = QTableWidgetItem(f"{device.wifi_quality}/{device.wifi_signal}")
            name_item = QTableWidgetItem(device.name)

            device.status.statusChanged.connect(self.update_status_item)
            device.nameChanged.connect(self.update_name_item)
            device.sourceFolderChanged.connect(self.update_source_folder_item)
 
            status_item_gui = QTableWidgetItem(device.status.str_status())
            status_item_gui.setData(Qt.DecorationRole, device.status.color_status())

            ip_item = QTableWidgetItem(device.ip)

            info_item = QTableWidgetItem(device.source_folder)
            if device.source_folder is not None and os.path.exists(device.source_folder):
                color = QColor("green") if len(os.listdir(device.source_folder)) > 0 else QColor("yellow")
                brush = QBrush(color)
                info_item.setBackground(brush)

            usb_item = QTableWidgetItem(device.usb)
            if device.usb is not None:
                color = QColor("green")
                brush = QBrush(color)
                usb_item.setBackground(brush)

            if self.selected_device is not None:
                if self.selected_device.ip == device.ip:
                    self.selected_device = device

            self.device_table_widget.setItem(row, 0, signal_item)
            self.device_table_widget.setItem(row, 1, name_item)
            self.device_table_widget.setItem(row, 2, status_item_gui)
            self.device_table_widget.setItem(row, 3, ip_item)
            self.device_table_widget.setItem(row, 4, info_item)
            self.device_table_widget.setItem(row, 5, usb_item)


    def update_status_item(self):
        sender_status = self.sender()
        for row, device in enumerate(self.devices):
            if device.status == sender_status:
                self.device_table_widget.item(row, 2).setData(Qt.DecorationRole, sender_status.color_status())
                self.device_table_widget.item(row, 2).setText(sender_status.str_status())

    def update_name_item(self):
        sender_status = self.sender()
        for row, device in enumerate(self.devices):
            if device == self.selected_device:
                self.device_table_widget.item(row, 1).setText(sender_status.name)

    def update_source_folder_item(self):
        sender_status = self.sender()
        for row, device in enumerate(self.devices):
            if device == self.selected_device:
                color = QColor("green") if len(os.listdir(sender_status.source_folder)) > 0 else QColor("yellow")
                brush = QBrush(color)
                self.device_table_widget.item(row, 4).setText(sender_status.source_folder)
                self.device_table_widget.item(row, 4).setBackground(brush)

    def device_selected(self, row, column):
        try:
            if row < len(self.devices):
                self.selected_device = self.devices[row]
                if self.selected_device.usb_busy:
                    self.clear_usb_button.setEnabled(False)
                    self.upload_button.setEnabled(False)
                else:
                    self.clear_usb_button.setEnabled(True)
                    self.upload_button.setEnabled(True)

                if column == 4:
                    if self.selected_device.source_folder is not None:
                        list_dir = os.listdir(self.selected_device.source_folder)
                        self.update_gui.logger(f'List files: {list_dir}')

                self.device_info_label.setText(
                    f"Name: {self.selected_device.name}\nStatus: {self.selected_device.status.str_status()}\nIP: {self.selected_device.ip}\nFolder: {self.selected_device.source_folder}")
                self.setup_button.setEnabled(True)
                self.select_folder_button.setEnabled(True)
                self.repair_usb_button.setEnabled(True)
                self.remove_button.setEnabled(True)
        except:
            pass

    def edit_device(self):
        if self.selected_device:
            selected_device = self.selected_device
            try:
                diaglog = EditDeviceDialog()
                diaglog.init(name=selected_device.name)
                if diaglog.exec_() == QDialog.Accepted:
                    name, ssid, pw, host, port = diaglog.get_data()
                    if not selected_device.is_online():
                        self.update_gui.logger("Selected device is offline")
                        # return
                    if selected_device.name != name:
                        # selected_device.rename(name)
                        # server_url = 'http://127.0.0.1:8081/change_name'
                        device_url = f'http://{selected_device.ip}:8080/change_name'
                        try:
                            response = requests.post(device_url, json={"device_ip": selected_device.ip, "name": name}, timeout=3)
                            # requests.post(server_url, json={"device_ip": selected_device.ip, "name": name}, timeout=2)
                            if response.status_code == 200:
                                self.update_gui.logger(f"Edited device name [{selected_device.name}] to [{name}]")
                            else:
                                self.update_gui.logger(f"Failed when edite device name [{selected_device.name}] to [{name}] [{response.status_code}]")
                        except:
                            self.update_gui.logger(f"Failed when edit device name [{selected_device.name}] to [{name}]")
                        self.update_gui.reload()

                    if ssid or host:
                        if diaglog.apply_all:
                            selected_devices = self.devices
                        else:
                            selected_devices = [selected_device]
                        
                        for selected_device in selected_devices:
                            self.update_gui.logger(f"Editing wifi of device: [{selected_device.name}]: SSID {ssid}, HOST {host}:{port}]")
                            device_url = f'http://{selected_device.ip}:8080/change_wifi'
                            try:
                                response = requests.post(device_url, json={"device_ip": selected_device.ip, 
                                                                        "ssid": ssid, 
                                                                        "password": pw,
                                                                        "host": host,
                                                                        "port": port
                                                                        }, timeout=5)
                                if response.status_code == 200:
                                    self.update_gui.logger(f"Edited device wifi [{selected_device.name}]")
                                else:
                                    self.update_gui.logger(f"Failed when edite device info [{selected_device.name}]")
                            except:
                                self.update_gui.logger(f"Failed when edite device info [{selected_device.name}]")
                                pass

                    self.update_gui.reload()
            except:
                self.update_gui.logger(f"Failed except when edite device info")
                pass

    def upload_to_device(self):
        if self.selected_device and self.selected_device.is_online():
            try:
                device_name = self.selected_device.name
                device_ip = self.selected_device.ip
                file_dialog = QFileDialog()
                file_dialog.setFileMode(QFileDialog.ExistingFile)
                file_dialog.setWindowTitle("Select File")
                file_dialog.setNameFilter("All Files (*.*)")
                if file_dialog.exec_() == QFileDialog.Accepted:
                    selected_files = file_dialog.selectedFiles()
                    if selected_files:
                        file_path = selected_files[0]
                        if os.path.exists(file_path):
                            self.update_gui.logger(f"[UI] Uploading {file_path} to [{device_name}]")
                            url = 'http://127.0.0.1:8081/upload'
                            try:
                                self.upload_button.setEnabled(False)
                                self.clear_usb_button.setEnabled(False)
                                for d in self.devices:
                                    if d.ip == device_ip:
                                        d.usb_busy = True
                                response = requests.post(url, json={'ip': device_ip, 'name': device_name, 'fpath': file_path})
                                if response.status_code != 200:
                                    self.upload_button.setEnabled(True)
                                    self.clear_usb_button.setEnabled(True)
                                    self.update_gui.logger(f"[UI] Cannot upload {file_path} to [{device_name}] [Internal server error]")
                            except Exception as e:
                                print(e)
                                self.upload_button.setEnabled(True)
                                self.clear_usb_button.setEnabled(True)
                                self.update_gui.logger(f"[UI] Cannot upload {file_path} to [{device_name}] [Internal server error]")
            except:
                self.update_gui.logger(f"[UI] Try again !")

        else:
            self.upload_button.setEnabled(False)
            self.update_gui.logger(f"[UI] Device offline")



    def select_source_folder(self):
        if self.selected_device:
            # if not self.selected_device.is_online():
            #     self.update_gui.logger("Selected device is offline")
            #     return
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder_path:
                # print("Selected Folder:", folder_path)
                # self.selected_device.set_source_folder(folder_path)
                server_url = 'http://127.0.0.1:8081/select_dir'
                try:
                    response = requests.post(server_url, json={'device_ip': self.selected_device.ip, 'dir': folder_path})
                    self.update_gui.reload()
                except:
                    pass



    def add_device(self):
        device = AddDeviceDialog()
        if device.exec_() == QDialog.Accepted:
            name, ip = device.get_data()
            for d in self.devices:
                if d.ip == ip:
                    return
            self.add_device_raw(name, ip)
    
    def remove_device_server(self, device_ip):
        url = 'http://127.0.0.1:8081/remove_device'
        try:
            response = requests.post(url, json={'device_id': device_ip})
        except:
            pass
        self.get_devices()

    def remove_device(self):
        if self.selected_device:
            self.remove_device_server(self.selected_device.ip)
            self.selected_device = None
            self.device_info_label.setText("Select a device to view its info.")
            self.setup_button.setEnabled(False)
            self.upload_button.setEnabled(False)
            self.select_folder_button.setEnabled(False)
            self.clear_usb_button.setEnabled(False)
            self.repair_usb_button.setEnabled(False)
            self.remove_button.setEnabled(False)
            self.populate_device_table()

    def reload(self):
        self.get_devices()
        # self.selected_device = None
        # self.device_info_label.setText("Select a device to view its info.")
        # self.setup_button.setEnabled(False)
        # self.upload_button.setEnabled(False)
        # self.select_folder_button.setEnabled(False)
        # self.clear_usb_button.setEnabled(False)
        # self.repair_usb_button.setEnabled(False)
        # self.remove_button.setEnabled(False)
        self.populate_device_table()
        if self.selected_device is not None:
            # print("reload2", self.selected_device.name, self.selected_device.usb_busy)
            if self.selected_device.usb_busy:
                self.upload_button.setEnabled(False)
                self.clear_usb_button.setEnabled(False)
            else:
                self.upload_button.setEnabled(True)
                self.clear_usb_button.setEnabled(True)
    
    def reload2(self):
        self.get_devices()
        self.selected_device = None
        self.device_info_label.setText("Select a device to view its info.")
        self.setup_button.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)
        self.clear_usb_button.setEnabled(False)
        self.repair_usb_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.populate_device_table()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeviceManagerGUI()
    window.show()
    sys.exit(app.exec_())
