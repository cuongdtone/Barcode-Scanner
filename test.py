from evdev import InputDevice, list_devices

# Liệt kê tất cả các thiết bị /dev/input/event
devices = [InputDevice(device) for device in list_devices()]

# In ID của từng thiết bị
for device in devices:
    print(f"Device: {device.path}, ID: {device.fd}, Name {device.name}")