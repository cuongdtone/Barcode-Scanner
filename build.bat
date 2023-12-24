pyinstaller --noconfirm --onefile --windowed  "/desktop-service/server.py"
pyinstaller --noconfirm --onedir --windowed --add-data "desktop-service/icon;icon/"  "desktop-service/app.py"