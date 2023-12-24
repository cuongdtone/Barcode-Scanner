import customtkinter
import os
from PIL import Image
from tkinter import ttk
import requests
from threading import Thread


customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class ScrollableLabelButtonFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, command=None, upload_command=None, rename_command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.upload_command = upload_command
        self.rename_command = rename_command
        self.radiobutton_variable = customtkinter.StringVar()
        self.label_list = []
        self.button_list = []
        self.button2_list = []
        self.ip_label_list = []
        

    def add_item(self, item, ip):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        upload_image = customtkinter.CTkImage(Image.open(os.path.join(current_dir, "icon/upload-button.png")))
        choice_image = customtkinter.CTkImage(Image.open(os.path.join(current_dir, "icon/choice-button.png")))
        rename_image = customtkinter.CTkImage(Image.open(os.path.join(current_dir, "icon/rename-button.png")))
        device_image = customtkinter.CTkImage(Image.open(os.path.join(current_dir, "icon/barcode-scanner.png")))

        name_label = customtkinter.CTkLabel(self, text=item, image=device_image, compound="left", padx=5, anchor="w")
        name_label.grid(row=len(self.label_list) * 2, column=0, pady=(0, 10), sticky="w")


        ip_label = customtkinter.CTkLabel(self, text=ip, compound="left", padx=5, anchor="w")
        ip_label.grid(row=len(self.label_list) * 2, column=1, pady=(0, 10), sticky="w")


        button = customtkinter.CTkButton(self, text="Barcode Folder", width=100, height=24, image=choice_image)
        if self.command is not None:
            button.configure(command=lambda: self.command(ip))
        button.grid(row=len(self.button_list) * 2, column=2, pady=(0, 10), padx=5, sticky="e")
    

        button2 = customtkinter.CTkButton(self, text="Upload", width=50, height=24, image=upload_image)
        if self.upload_command is not None:
            button2.configure(command=lambda: self.upload_command(ip))
        button2.grid(row=len(self.button_list) * 2, column=3, pady=(0, 10), padx=5, sticky="e")

        # button3 = customtkinter.CTkButton(self, text="Rename", width=100, height=24, image=rename_image)
        # if self.rename_command is not None:
        #     button3.configure(command=lambda: self.rename_command(ip))
        # button3.grid(row=len(self.button_list) * 2, column=4, pady=(0, 10), padx=5, sticky="e")

        self.label_list.append(name_label)
        self.button_list.append(button)
        self.button2_list.append(button2)
        self.ip_label_list.append(ip_label)

    def update_name_item(self, item, new_item):
        for label in self.label_list:
            if item == label.cget("text"):
                label.configure(text=new_item)
                label.update()
    
                return

    def remove_item(self, item):
        for label, button, button2, ip_label in zip(self.label_list, self.button_list, self.button2_list, self.ip_label_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                button2.destroy()
                ip_label.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                self.button2_list.remove(button2)
                self.ip_label_list.remove(ip_label)
                return


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.window_closed = False

        self.title("Barcode Scanner")
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        self.geometry(f"{1100}x{580}")

        # create scrollable label and button frame
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.scrollable_label_button_frame = ScrollableLabelButtonFrame(master=self, label_text="Devices", width=200, 
                                                                        command=self.label_button_frame_event, corner_radius=0,
                                                                        upload_command=self.upload_button_frame_event,
                                                                        rename_command=self.rename_button_frame_event)
        self.scrollable_label_button_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew", rowspan=3)


        
        self.devices =  self.request_active_device_list()
        for i in self.devices:  # add items with images
            self.scrollable_label_button_frame.add_item(*i[:2])
       
        # create textbox
        self.textbox = customtkinter.CTkTextbox(self, width=450)
        self.textbox.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")

        self.button = customtkinter.CTkButton(self, text="Reload", width=100, height=24)
        self.button.configure(command=lambda: self.reload())
        self.button.grid(row=1, column=2, pady=(0, 10), padx=5, sticky="e")

        Thread(target = self.stream_text).start()

    def reload(self):
        for i in self.devices:
            self.scrollable_label_button_frame.remove_item(i[0])
        self.devices =  self.request_active_device_list()
        for i in self.devices:  # add items with images
            self.scrollable_label_button_frame.add_item(*i[:2])
    
    def request_active_device_list(self):
        """
        request to self server
        [
            (device_ip, device_name, status)
        ]
        """
        try:
            url = 'http://127.0.0.1:8081/devices'
            return requests.get(url).json()
        except:
            return []

    def stream_text(self):
        url = 'http://127.0.0.1:8081/stream'
        response = requests.get(url, stream=True)
        for line in response.iter_lines():
            if self.window_closed:
                break
            if line:
                text_line = line.decode('utf-8')
                if "Device" in text_line:
                    self.reload()
                self.textbox.insert("0.0", text_line + "\n")

    def backend_task(self):
        pass

    def label_button_frame_event(self, item):
        path = customtkinter.filedialog.askdirectory(title="Select a folder")
        if path is not None and os.path.exists(path):
            print('Request')
            url = 'http://127.0.0.1:8081/select_dir'
            print(url)
            response = requests.post(url, json={'device_ip': item, 'dir': path})
            self.textbox.insert("0.0", f"Selected {path} [{item}] [{response.status_code}]\n")

    def upload(self, item, path):
        self.textbox.insert("0.0", f"Uploading {path} to [{item}] ....\n")
        url = f'http://{item}:8080/upload'
        with open(path, 'rb') as file:
            try:
                response = requests.post(url, files={'file': file})
            except:
                self.textbox.insert("0.0", f"Cannot upload: [{item}][{response.status_code}]!!\n")

        if response.status_code == 200:
            self.textbox.insert("0.0", f"Uploaded {path} to [{item}][{response.status_code}]!!\n")
        else:
            self.textbox.insert("0.0", f"Device offline: [{item}][{response.status_code}]!!\n")

    def upload_button_frame_event(self, item):
        file_path = customtkinter.filedialog.askopenfilename(title="Select a file", filetypes=(("All files", "*.*"), ("All files", "*.*")))
        if os.path.exists(file_path):
            Thread(target=self.upload, args=(item, file_path)).start()

    def rename_button_frame_event(self, item):
        print(f"Rename button frame clicked: {item}")
        diaglog = customtkinter.CTkInputDialog(title="Rename Device", text='New name')
        new_item = diaglog.get_input()
        if new_item is not None:
            self.scrollable_label_button_frame.update_name_item(item, new_item)

    def destroy(self):
        self.window_closed = True
        url = 'http://127.0.0.1:8081/shutdown'
        try:
            response = requests.post(url)
        except:
            pass
        super().destroy()

if __name__ == "__main__":
    customtkinter.set_appearance_mode("light")
    app = App()
    app.mainloop()
