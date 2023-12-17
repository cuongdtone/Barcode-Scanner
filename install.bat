@echo off

REM Đường dẫn đến thư mục chứa mã nguồn Flask Python
set "FLASK_APP_PATH=%~dp0dist\server.exe"

REM In ra giá trị của biến FLASK_APP_PATH
echo %FLASK_APP_PATH%

REM Tên dịch vụ
set "SERVICE_NAME=BarcodeScannerV5"

REM Tên mô tả dịch vụ
set "SERVICE_DISPLAY_NAME=Barcode Scanner Server"

echo Install
REM Cài đặt các gói cần thiết
python -m pip install pywin32
python -m pip install waitress

REM Tạo dịch vụ
sc create %SERVICE_NAME% binPath= "%FLASK_APP_PATH%" displayname= "%SERVICE_DISPLAY_NAME%" start= auto

REM Khởi động dịch vụ
sc start %SERVICE_NAME%

echo Done.

timeout /t 10