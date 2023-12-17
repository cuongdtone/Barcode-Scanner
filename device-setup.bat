@echo off
@echo off

REM Kiểm tra nếu đã cài đặt pip
pip --version
IF %ERRORLEVEL% EQU 0 (
    echo pip installed.
    goto end
)

REM Cài đặt pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py

REM Kiểm tra lại phiên bản pip
pip --version

:end
pip install -r requirements.txt
python device-setup.py
pause