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

    def update_name_item(self, item, new_item):
        for label in self.label_list:
            if item == label.cget("text"):
                label.configure(text=new_item)
                label.update()
    
                return

    def remove_item(self, item):
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
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
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")

        Thread(target = self.stream_text).start()
    
    def request_active_device_list(self):
        """
        request to self server
        [
            (device_ip, device_name, status)
        ]
        """
        try:
            url = 'http://127.0.0.1:8080/devices'
            return requests.get(url).json()
        except:
            return []

    def stream_text(self):
        url = 'http://127.0.0.1:8080/stream'
        response = requests.get(url, stream=True)
        for line in response.iter_lines():
            if self.window_closed:
                break
            if line:
                self.textbox.insert("0.0", line.decode('utf-8') + "\n")

    def backend_task(self):
        pass

    def label_button_frame_event(self, item):
        path = customtkinter.filedialog.askdirectory(title="Select a folder")
        if path is not None:
            print(path)
            print(f"Barcode button frame clicked: {item}")

    def upload_button_frame_event(self, item):
        file_path = customtkinter.filedialog.askopenfilename(title="Select a file", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if file_path is not None:
            print(file_path)
            url = f'http://{item}:8080/upload'
            with open(file_path, 'rb') as file:
                response = requests.post(url, files={'file': file})

            print(f"Upload button frame clicked: {item} - {response.status_code}")

    def rename_button_frame_event(self, item):
        print(f"Rename button frame clicked: {item}")
        diaglog = customtkinter.CTkInputDialog(title="Rename Device", text='New name')
        new_item = diaglog.get_input()
        if new_item is not None:
            self.scrollable_label_button_frame.update_name_item(item, new_item)

    def destroy(self):
        self.window_closed = True
        super().destroy()

if __name__ == "__main__":
    customtkinter.set_appearance_mode("light")
    app = App()
    app.mainloop()